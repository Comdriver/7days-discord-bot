#####################################################################
#                                                                   #
#                          Zombie Alert v0.1                        #
#                                                                   #
#####################################################################

import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import psutil
import sys
import re
import socket
import random
import xml.etree.ElementTree as ET
#from pathlib import Path
import glob
import subprocess

from pprint import pprint # remove it later

env_file = "bot.env"
load_dotenv(dotenv_path=env_file)

# check if everything required is in the config file
required_vars={"GAME_PATH": None, "DATA_PATH": None, "DISCORD_TOKEN": None, "TELNET_HOST": None}
missing_vars=[key for key, default in required_vars.items() if os.getenv(key) is None]
if missing_vars:
    print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    sys.exit(1)  # Exit with error code

# ===== main config
GAME=os.getenv("GAME","7DaysToDieServer")
GAME_PATH=os.getenv("GAME_PATH")
DATA_PATH=os.getenv("DATA_PATH")
GAME_LOG=os.getenv("GAME_LOG","output_log")
BOT_LOG=os.getenv("BOT_LOG","zombie_alert")
BOT_LOG_KEEP_COUNT=int(os.getenv("BOT_LOG_KEEP_COUNT", "20"))
GAME_LOG_KEEP_COUNT=int(os.getenv("GAME_LOG_KEEP_COUNT", "20"))
GAME_MONITOR=int(os.getenv("GAME_MONITOR", "0"))
SERVERTOOLS=int(os.getenv("SERVERTOOLS", "0"))

# connection config
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_PREFIX = os.getenv("DISCORD_PREFIX", "!")
DISCORD_CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
TELNET_HOST = os.getenv("TELNET_HOST","127.0.0.1")

# bloodmoon start and end time
BM_START_TIME = os.getenv("BM_START_TIME", "22:00")
BM_END_TIME = os.getenv("BM_END_TIME", "04:00")

bot_description="7 Days to Die server bot"

log_latest=""
log_position=0
bloodMoonDay=0
lastbloodMoonDay=0
servertime=""
serverstatus="offline"
cooldown = 0

delim_line = "============================================="
utc = True
hello="> " # bot will start all messages with this symbol, "> " is a code to start a quote in discord.
# more on discord formatting here: https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline
error="ERROR: "
no_permissions = f":warning: You do not have the required permissions to use this command."
error_message = f":no_entry: An error occurred while processing the command.\n"
development_message = f":warning: command in development."


reasons = [
    "Just because",
    "No reason provided",
    "¯\\_(o_o)_/¯",
    "Because the admin felt like it",
    "Probably deserved it",
    "Kicked into the void"
]

def get_timestamp(utc_tz=False,file_path = False):
    if utc_tz:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if file_path:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H-%M-%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# find stuff in DATA_PATH
LOG_PATH = os.path.join(DATA_PATH, 'logs')
serverconfig_path = os.path.join(GAME_PATH, "serverconfig.xml")
serverworld_name = ET.parse(serverconfig_path).getroot().find(".//property[@name='GameWorld']").get("value")
servergame_name = ET.parse(serverconfig_path).getroot().find(".//property[@name='GameName']").get("value")
player_config = os.path.join(DATA_PATH, "saved", serverworld_name, servergame_name, "players.xml")
TELNET_PORT = int(ET.parse(serverconfig_path).getroot().find(".//property[@name='TelnetPort']").get("value", "8081"))
TELNET_PASS = ET.parse(serverconfig_path).getroot().find(".//property[@name='TelnetPassword']").get("value")
TELNET_ENABLED = ET.parse(serverconfig_path).getroot().find(".//property[@name='TelnetEnabled']").get("value",)

# configure discord bot

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=DISCORD_PREFIX, case_insensitive=True, description=bot_description, intents=intents)

# check if logging path exists and create it
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

# logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] - %(message)s', '%Y-%m-%d %H:%M:%S')

# for file output
file_handler = RotatingFileHandler(os.path.join(LOG_PATH, BOT_LOG+"_"+get_timestamp(file_path=True)+".log"),maxBytes=10 * 1024 * 1024,encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# for discrod output
class DiscordLoggingHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def send_to_discord(self, message):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            message = f"{hello}{message}"
            await channel.send(message)

    def emit(self, record):
        log_message = self.format(record)
        # Run async task in the bot's event loop
        asyncio.create_task(self.send_to_discord(log_message))
discord_handler = DiscordLoggingHandler(bot, DISCORD_CHANNEL)
discord_handler.setLevel(logging.INFO)

# logging variables
to_console = "log_console"
to_discord = "log_discord"
to_file = "log_file"
outputs = {
    to_console: console_handler,
    to_file: file_handler,
    to_discord: discord_handler
}

# default output
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# ===== main output function
# log to console (log_console), to file (log_file) and discord notifications (log_discord)
def output(message, output_selection=[to_console,to_file,to_discord]):
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    output_selection = [outputs[handler] for handler in output_selection if handler in outputs]
    for handler in output_selection:
        logger.addHandler(handler)

    logger.info(message)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# ===== 7 days telnet client
class AsyncTelnetClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    async def connect(self,nolog=False):
        loop = asyncio.get_event_loop()
        self.sock = await loop.sock_connect(self._create_socket(), (self.host, self.port))
        if not nolog:
            output(f"Connected to {self.host}:{self.port}",[to_console,to_file])

    def _create_socket(self):
        # Create the socket object with necessary parameters
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        return sock

    async def send_command(self, command,password=False,nolog=False):
        if not self.sock:
            raise ConnectionError("Not connected.")
        
        # Send the command to the server
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self.sock, command.encode('utf-8') + b'\n') # was ascii
        if password:
            command = "**********"
        if not nolog:
            output(f"Sent command: {command}",[to_console,to_file])

    async def receive_telnet_data(self, phrase="",IngnoreTimestamps=True,nolog=False):
        buffer_size = 4096
        phrase = phrase.encode()
        loop = asyncio.get_event_loop()

        data = b''

        while True:
            # Read data in chunks
            chunk = await loop.sock_recv(self.sock, buffer_size)
            if not chunk:
                break
            # print(chunk)
            data += chunk
            if phrase in data:
                break

        result = b''
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')  # Regex to match date format: YYYY-MM-DDTHH:MM:SS

        # Split the data into lines for easier processing
        lines = data.split(b'\n')

        # Check each line
        for line in lines:
            line_str = line.decode('utf-8', errors='ignore').strip()  # Decode line to string and strip whitespace

            line = line.strip(b'\r\x00')  # strip CR and NULL chars
            if not line:  # skip empty lines
                continue

            # Ignore lines starting with a date in the specified format
            if date_pattern.match(line_str) and IngnoreTimestamps:
                continue  # Skip this line

            result += line + b'\n'

        if not nolog:
            output(result.decode().strip(),[to_console,to_file])
        return result

    async def close(self,nolog=False):
        if self.sock:
            self.sock.close()
            if not nolog:
                output("Connection closed.",[to_console,to_file])


# ===== sync fuctions are here

def clean_logs(logfile, logs_keep=BOT_LOG_KEEP_COUNT):
    log_files = sorted(glob.glob(os.path.join(LOG_PATH, f"{logfile}_*.log")),key=os.path.getmtime)
    if len(log_files) > logs_keep:
        for old_log in log_files[:-logs_keep]:
            os.remove(old_log)

def players_format(list):
    # list = list.strip()
    if "crossid" in list:
        pattern = re.compile(r'(\d+)\.\s+id=(\d+),\s+(.*?),.*?level=(\d+),.*?ping=(\d+)', re.DOTALL)
        players_online = []
        for match in pattern.finditer(list):
            player_index, player_id, player_name, player_level, player_ping = match.groups()
            players_online.append(f"{player_name} ({player_id}), level {player_level} - ping {player_ping}")

    else:
        players_online = [f"{list}"]

    return players_online

def parse_time(timestr):
    if timestr.startswith("Day "):
        timestr = timestr[4:]
    day_str, time_str = timestr.strip().split(",")
    day = int(day_str.strip())
    hour, minute = map(int, time_str.strip().split(":"))
    return day * 24 * 60 + hour * 60 + minute

def get_time_left(current, start =BM_START_TIME, end=BM_END_TIME ):
    now = parse_time(current)
    start_min = parse_time(f"{bloodMoonDay}, {start}")
    end_min = parse_time(f"{bloodMoonDay}, {end}")

    if now < start_min: # still ahve time
        days_left = (start_min - now) // (24 * 60)
        remainder = (start_min - now) % (24 * 60)
        hours_left = remainder // 60
        minutes_left = remainder % 60

        if days_left: #still have more than 1 day
            return f"Next Blood Moon is at day {bloodMoonDay}. Starts in {days_left} ingame days and {hours_left:02}:{minutes_left:02} ingame hours."
        else:         # less than a day left, be prepared
            return f"Blood Moon is TODAY! Starts in {hours_left:02}:{minutes_left:02} ingame hours. Be ready!"
        
    elif start_min <= now <= end_min: # bloodmoon is active
        minutes_remaining = end_min - now
        return f"BloodMoon is active! {minutes_remaining} ingame time left!"

    return "Something went wrong"

def find_bloodmoon(line):
    global bloodMoonDay
    global lastbloodMoonDay
    pattern = r"BloodMoon SetDay: day (\d+), last day (\d+)"
    match = re.search(pattern, line)
    if match:
        bloodMoonDay=int(match.group(1))
        lastbloodMoonDay=int(match.group(2))
        output(f"new Bloodmoon date found: {bloodMoonDay}, last Bloodmoon day: {lastbloodMoonDay}",[to_console, to_file])


def find_latest_log():
    global log_latest
    global log_position

     # find all logs
    pattern = os.path.join(LOG_PATH, f"{GAME_LOG}*.log")

    all_logs = glob.glob(pattern)
    if not all_logs: # no logs found
        output ("No initial log files found, skipping log read for now",[to_console,to_file])
        return

    all_logs.sort(key=os.path.getctime, reverse=True)

    # if there is a new log - reset read position to 0
    if log_latest != all_logs[0]:
        log_position = 0

    log_latest = all_logs[0]
    output(f"latest log file is {log_latest}",[to_file,to_console])

    return

def check_process(process_name):
    process_name
    for p in psutil.process_iter(attrs=['pid', 'name']):
        if p.info['name'].lower() == process_name.lower():
            return True
    return False

def progress_bar(message, progress, total, bar_length=50):
    # Calculate the progress
    percent = (progress / total) * 100
    filled_length = int(bar_length * progress // total)
    bar = f"{message}: [{'#' * filled_length}{'-' * (bar_length - filled_length)}] {percent:.2f}%"

    print(bar)

# a way to kill game process if game is frozen or smth like that
def kill_game():
    for p in psutil.process_iter(['name']):
        if p.info['name'] == f"{GAME}.exe":
            output(f"Killing process {p.pid} ({p.info['name']})",[to_console,to_file])
            p.kill()
            return True
    output(f"{error}{GAME}.exe not found, unable to kill",[to_console,to_file])
    return False

# ===== async functions are here

# check the log file on bot start, to see if there is a bloodmoon
async def check_log_initial():
    global log_position

    # find all logs
    find_latest_log()

    # find the latest blood moon
    target_bm = "INF BloodMoon SetDay"
    try:
        with open(os.path.join(log_latest), 'r', encoding='utf-8', errors='ignore') as f:
            print(f"File {log_latest} is found and ready")
            lines = f.readlines()

        # Search in reverse
        for line in reversed(lines):
            if target_bm in line:
                find_bloodmoon(line)
                print ("bloodMoonDay", bloodMoonDay)
                print ("lastbloodMoonDay", lastbloodMoonDay)
                return
            
    except FileNotFoundError:
        print("File not found")
        return None

async def players_read_all():
    all_players  = {}

    # Parse XML
    tree = ET.parse(player_config)
    root = tree.getroot()
    # Header
    print(f"{'Steam ID':<20} {'Name':<20} {'Last Online':<25} {'Bedroll':<8} {'Claim Blocks'}")
    print("-" * 80)
    for player in root.findall("player"):
        steam_id = player.get("nativeplatform", "N/A") + "_" + player.get("nativeuserid", "N/A")
        name = player.get("playername", "N/A")
        last_online = player.get("lastlogin", "N/A")

        # Check for bedroll
        bedroll = player.find("bedroll")
        has_bed = "Yes" if bedroll is not None else "No"

        # Count land claim blocks
        lp_blocks = player.findall(".//lpblock")
        num_lpblocks = len(lp_blocks)

        all_players[name] = {
        "id": steam_id,
        "last online": last_online,
        "has Bedroll": has_bed,
        "claim Blocks": num_lpblocks
        }

    return all_players

# this parses the command parameters to get player name and the reason for ban or kick
async def player_and_reason(params: str):
    players_all = await players_read_all()
    parts = params.split()
    player_name = None
    reason = None
    player_id = None

    for i in range(len(parts), 0, -1):
        possible_name = " ".join(parts[:i])


        if possible_name in players_all:
            print ("got",possible_name)
            player_name = possible_name
            player_data = players_all[player_name]
            player_id = player_data['id'].replace('Steam_', '')
            reason = " ".join(parts[i:]) if len(parts) > i else None
            break
        if player_name:
            break
    print(player_name, player_id, reason)
    # check if player was found
    if not player_name:
        return "Player not found", None

    if not reason:
        reason = random.choice(reasons)
    
    return player_name, reason

async def st_shutdown():
    shutdown_time = await telnet_connect2("st-scheck",stopwrd="SERVERTOOLS")
    shutdown_time = shutdown_time.split("'")
    if len(shutdown_time)>= 2:
        try:
            shutdown_time = shutdown_time[1]
            hours,minutes = shutdown_time.split(":")
            hours = int(hours.strip().replace("H", "").strip())
            minutes = int(minutes.strip().replace("M", "").strip())
            result = f"{hello}The next auto shutdown is in {hours} hours and {minutes} minutes of real time."
        except ValueError:
            result = f"{hello}No auto shutdown time found."
    else:
        # no time found
        result = f"{hello}No auto shutdown time found."
    return result

# ===== telnet stuff
async def telnet_connect2(cmd, stopwrd="\n", waittime = 0,IngnoreTimestamps=True,nolog=False):
    try:
        client = AsyncTelnetClient(TELNET_HOST, TELNET_PORT)
        await client.connect(nolog=nolog)
        result = await client.receive_telnet_data(phrase="Please enter password:",nolog=nolog)

        await client.send_command(TELNET_PASS,password=True,nolog=nolog)
        result = await client.receive_telnet_data(phrase="to end session.",nolog=nolog)

        await client.send_command(cmd,nolog=nolog)
        if waittime:
            await asyncio.sleep(waittime)
        result = await client.receive_telnet_data(phrase=stopwrd,IngnoreTimestamps=IngnoreTimestamps,nolog=nolog)

        #await asyncio.sleep(1)
        await client.close(nolog=nolog)

        return result.decode().strip()
    
    except Exception as e:
        output(f"Telnet error: {e}",[to_console,to_file])
        return f"Telnet error: {e}"

async def banned_list ():
    result = await telnet_connect2("ban list", waittime=1)
    now = datetime.strptime(get_timestamp(), "%Y-%m-%d %H:%M:%S")
    lines = result.split('\n')[2:]
    players={}

    for line in lines:
        banned, rest = line.strip().split(' - ', 1)
        userid_with_name, reason = rest.split(' - ', 1)
        userid, name = userid_with_name.split(' ', 1)
        name = name.strip('()')

        banned = datetime.strptime(banned, "%Y-%m-%d %H:%M:%S")
        time_diff = banned - now
        players[name] = {
            "userid": userid,
            "banned": banned,
            "left": time_diff,
            "reason": reason
        }
    return players

# ===== discord section
@bot.event
async def on_ready():
    global serverstatus
    start_time = get_timestamp(utc)
    output(f"New monitoring session for {GAME} started on {start_time}.")
    output(f'Logged in as {bot.user} (ID: {bot.user.id})',[to_console,to_file])
    output(delim_line,[to_console,to_file])
    if check_process(f"{GAME}.exe"):
        serverstatus="online"
        message = f"{GAME} is online. :green_circle:"
        if SERVERTOOLS:
            shutdown_time= await st_shutdown()
            message = f"{message}\n{shutdown_time}"
    else:
        serverstatus="offline"
        message = f"{GAME} is offline. :red_circle:"
    output(message)

    # read the log to find if there is a bloodmoon day, if no day - skip.
    output ("Initial log file check",[to_console,to_file])
    await check_log_initial()

    # start log monitoring
    output ("Starting log monitoring",[to_console,to_file])
    check_log.start()

    # start bot routines
    output ("Starting bot routines",[to_console,to_file])
    do_routenes.start()

    # start game status monitoring - should restart the game is game is not running and GAME_MONITOR=1
    output ("Starting game monitoring",[to_console,to_file])
    check_game.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f":no_entry: Unknown command. Try `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f":warning: You're missing some arguments. Try `!help <command>` for usage info.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f":warning: Invalid argument type. Make sure you're using the right format.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f":warning: You do not have the required permissions to use this command.")
    else:
        # Fallback for unexpected errors
        await ctx.send(f":warning: An unexpected error occurred. Please contact the admin.")
        await ctx.send(f"{hello}{error}")

# set DISCORD_CHANNEL env_file
@bot.command(name="setchannel",help="Select a channel for bot output")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def setchannel(ctx):
    global DISCORD_CHANNEL
    global discord_handler
    DISCORD_CHANNEL = ctx.channel.id
    # read old content of the env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    # write new content to the env file
    with open(env_file, 'w') as f:
        for line in lines:
            if line.startswith('DISCORD_CHANNEL'):
                f.write(f'DISCORD_CHANNEL={DISCORD_CHANNEL}\n')
            else:
                f.write(line)
    discord_handler = DiscordLoggingHandler(bot, DISCORD_CHANNEL)
    discord_handler.setLevel(logging.INFO)
    # log here
    output(f"Bot channel set to {DISCORD_CHANNEL} ({ctx.channel.mention}) by {ctx.author.name}#{ctx.author.discriminator}.",[to_console,to_file])
    await ctx.send(f"Bot channel set to: {ctx.channel.mention} by {ctx.author.mention}")

# task to monitor game status and resart it if game is offline in case if GAME_MONITOR =1, esle just reset log path to the newst on game restart
@tasks.loop(seconds=15)  # Check every X seconds
async def check_game():
    global serverstatus
    # global log_latest
    global log_position
    global cooldown

    print("STATUS:", serverstatus)
    # check if the monitoring is ON
    #if GAME_MONITOR:

    # in case if we are waiting for the game to start, this loop should skip a few checks
    if cooldown:
        if cooldown > 0:
            cooldown -= check_game.seconds
        else:
            cooldown = 0
        progress_bar("Waiting for the server", 60-cooldown, 60)
        return
    
    if check_process(f"{GAME}.exe"):
        if serverstatus == "offline":
            serverstatus="loading"
            output (f"{GAME} is loading, please wait.")
            # find latest log file
            print ("---------1111------------")
            find_latest_log()
        elif serverstatus == "loading":
            # check log (should have this line "INF [Steamworks.NET] GameServer.LogOn successful") and set status to online
            #telnet_check = await telnet_connect2("",waittime=1,IngnoreTimestamps=True,nolog=True)
            if os.path.isfile(log_latest):
                started = False
                with open(log_latest, "r", encoding='utf-8') as f:
                    f.seek(log_position)
                    new_lines = f.readlines()
                    log_position = f.tell()
                if new_lines:
                    print ("---------22222------------")
                    for line in new_lines:
                        print (line)
                        if "GameServer.LogOn successful" in line:
                            started = True
                if started:
                    serverstatus = "online"
                    message = f"{GAME} is online."
                    if SERVERTOOLS:
                        shutdown_time= await st_shutdown()
                        message = f"{message}\n{shutdown_time}"
                    output (message)
                # else:
                #     output(f"{GAME} is loading, waiting for telnet response")
        elif serverstatus == "online":
            output (f"{GAME} is online, next check is in {check_game.seconds} seconds", [to_console])
        else:
            output (f"Something went wrong", [to_console])
    else:
        serverstatus="offline"
        cooldown = 60
        output (f"{GAME} is OFFLINE. Waiting for the game to start.")
        if GAME_MONITOR: # this means we should start the server
            timestamp = get_timestamp()
            game_log_file = os.path.join(LOG_PATH,f"{GAME_LOG}_{timestamp}.log")
            # remove old log files, keep latest 20
            clean_logs(GAME_LOG, logs_keep=20)
            output (f"Old log files were removed",[to_console,to_file])

            #run the server
            start_args = [
                "START", "/B", # start in the background
                os.path.join(GAME_PATH, f"{GAME}.exe"),
                "-logfile", game_log_file,
                "-quit", "-batchmode", "-nographics",
                "-configfile=serverconfig.xml", "-dedicated"
            ]
                #start_args = f"-logfile \"{game_log_file}\" -quit -batchmode -nographics -configfile=serverconfig.xml -dedicated"
            try:
                # something is wrong here, game doesn't start
                result = subprocess.Popen(start_args, cwd=os.path.join(GAME_PATH))
                print ("result:", result)
            except Exception as error_message:
                print("error:", error_message)

        progress_bar("Server it starting", 60-cooldown, 60)
        #output (f"Latest log file: {log_latest}",[to_console,to_file])




# task to check the log and get bloodmoon set day, bloodmoon start and end, player login/logoff, ingame chat, current day and time and etc
@tasks.loop(seconds=5)  # Check every X seconds, set to 1?
async def check_log():
    global log_position

    #channel = bot.get_channel(DISCORD_CHANNEL)
    #print("...log")

    # if log doesn't exist, just in case
    if not os.path.isfile(log_latest):
        return
    
    with open(log_latest, "r", encoding='utf-8') as f:
        f.seek(log_position)
        new_lines = f.readlines()
        log_position = f.tell()

    if new_lines:
        for line in new_lines:
            # check for blood moon day
            find_bloodmoon(line)

            #check if any player logged in

            #check if any player logged off

            #check for something else

# task to do bot routenes, like check the chat, send timed notifations and etc
@tasks.loop(seconds=5)  # Check every X seconds, set to 1?
async def do_routenes():
    return


# bloodmoon check
@bot.command(name="bloodmoon", aliases=["moon"],help="Tell when is the next Bloodmoon")
async def bloodmoon(ctx):
    if bloodMoonDay:
        today = await telnet_connect2("gettime",stopwrd="Day")
        time_left= get_time_left(today)

        message =f"{time_left}\n{hello}Previous Blood Moon was at day {lastbloodMoonDay}."
    
    else:
        message = "Blood Moon is not found"

    await ctx.send(f"{hello}{message}")

# server status check
@bot.command(name="status", aliases=["server"],help="Check server status")
async def status(ctx):
    if check_process(f"{GAME}.exe"):
        message = f"{hello}{GAME} is online. :green_circle:"
        #get next shutdown time from server tools
        if SERVERTOOLS:
            shutdown_time= await st_shutdown()
            message = f"{message}\n{shutdown_time}"
    await ctx.send(message)

# players check
@bot.command(name="players", aliases=["lp","listplayers","online","list"],help="See who is online")
async def players(ctx, *,command: str = commands.parameter(default="", description="This is commands")):
    if not command:
        result = await telnet_connect2("lp",stopwrd="in the game")  # 'lp' is the 7DTD command for listing players
        result = players_format(result)
        for player in result:
            await ctx.send(f"{hello}{player}\n")
    else:
        command = command.strip().lower()
        # validate commands
        if not command.startswith("all"):
            raise commands.BadArgument()

        mode = [item.strip() for item in command[3:].split(',')]
        allowed_mode = {
            "names","name","online","status","bedroll","bed","beds","claim","claimblock","block","blocks"
        }
        if not mode == [""]:
            for item in mode:
                if not item in allowed_mode:
                    raise commands.BadArgument()

        all_players = await players_read_all()
        counter = 0
        if "online" in mode or "status" in mode or mode==[""]:
            online_players = await telnet_connect2("lp",stopwrd="in the game")
        for player in all_players:
            counter += 1
            player_status = " :red_circle: "
            player_data = all_players[player]

            if "names" in mode or "name" in mode:
                output = f"{hello}{player}"
            else:
                output = f"{hello}{player}{player_status}:"
            if ("online" in mode or "status" in mode) or mode==[""]:
                if player in online_players:
                    player_status = " :green_circle: "
                output += f" Last online: {player_data['last online']}"
            if ("bed"  in mode or "bedroll" in mode) or mode==[""]:
                output += f", Bedroll: {player_data['has Bedroll']}"
            if ("claim"  in mode or "claimblock" in mode or "block" in mode) or mode==[""]:
                output += f", Claim blocks: {player_data['claim Blocks']}"
            await ctx.send(output)
        await ctx.send(f"{hello}Total registered players cout: {counter}\n")  

# players whois
@bot.command(name="playerwhois", aliases=["who", "player","whoisplayer","whois"],help="Player info")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def playerwhois(ctx, *, player_name: str):
    print (player_name)
    await ctx.send(development_message)

# check time
@bot.command(name="time", aliases=["day"],help="Show current ingame date and time")
async def time(ctx):
    result = await telnet_connect2("gettime",stopwrd="Day")
    output(f"received time: {result}",[to_console,to_file])
    await ctx.send(f"{hello}{result}\n")

# player kick
@bot.command(name="playerkick", aliases=["kick"], help="Kick a player from the server")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def playerkick(ctx, *, content):
    print (content)
    player_name, reason = await player_and_reason(content)
    admin_name = ctx.author.mention
    if reason:
        await telnet_connect2(f"kick \"{player_name}\" \"{reason}\"")
        message = f"Player `{player_name}` was kicked by {admin_name} from the server - {reason}"
    else:
        message = f"{player_name}"

    output(message, [to_console,to_file])
    await ctx.send(message)

# player ban
@bot.command(name="playerban", aliases=["ban"], help="Ban a player from the server")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def playerban(ctx, *, content):
    player_name, reason = await player_and_reason(content)
    admin_name = ctx.author.mention

    if reason:
        await telnet_connect2(f"ban \"{player_name}\" 1 day \"{reason}\"")
        message = f"Player `{player_name}` was banned by {admin_name} from the server - {reason}"
    else:
        message = f"{player_name}"

    output(message, [to_console,to_file])
    await ctx.send(message)

# ban list
@bot.command(name="banlist",aliases=["banned"],  help="Show banned players")
async def banlist(ctx):
    banned = await banned_list()
    for name, data in banned.items():
        banned = data["banned"].strftime("%Y-%m-%d %H:%M:%S")
        time_diff = str(data["left"])
        reason = data["reason"]
        await ctx.send(f"{hello}{name}: {banned} ({time_diff}) - {reason}\n")

    await ctx.send(f"{hello}End of the list\n")

# player unban
@bot.command(name="playerunban", aliases=["unban"], help="Unban a player")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def playerunban(ctx, *, player_name: str):
    banned = await banned_list()
    if player_name in banned:
        result = await telnet_connect2(f"ban remove \"{banned[player_name]['userid']}\"", waittime=1)
    else:
        player_list = await players_read_all()
        if player_name in player_list:
            result = f"Player {player_name} is not banned."
        else:
            result = f"Player {player_name} not found. Try `!playersall names` to get the list of registered players."

    await ctx.send(f"{hello}{result}")


# say to chat
@bot.command(name="say", aliases=["chat"], help="Send a message")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def say(ctx, *, message: str):
    await telnet_connect2(f"say \"{message}\"", waittime=1)
    await ctx.send(f"Your message was sent```{message}```")

# server shutdown
@bot.command(name="shutdown", help="Shitdown the server")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def shutdown(ctx, *, reason="Time to shutdown"):
    # this will shudown the server and unlike the restart command, also stop process monitoring and server restart if down
    # may be should check is server is  
    print (reason)
    await ctx.send(development_message)

# server restart
@bot.command(name="reboot", aliases=["restart"], help="Restart the server")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def reboot(ctx, *, reason="Time to restart"):
    # this will just shutdown the server, process monitoring will restart it
    print (reason)
    await ctx.send(development_message)

# server start
@bot.command(name="serverstart", aliases=["start"], help="Start the server if not running")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def serverstart(ctx, *, reason="Time to restart"):
    # this will just shutdown the server, process monitoring will restart it
    print (reason)
    await ctx.send(development_message)

# server save world
@bot.command(name="saveworld", aliases=["save"], help="Save the current world state")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def saveworld(ctx):
    output(f"Saving world",[to_console,to_file])
    await ctx.send(f"{hello}Saving world")
    result = await telnet_connect2("saveworld",stopwrd="World saved")
    last_inf_index = result.rfind("INF ")
    if last_inf_index != -1:
        result = result[last_inf_index + len("INF "):]
    else:
        result = f"Something went wrong: ```{result}```"
    output(f"{result}",[to_console,to_file])
    await ctx.send(f"{hello}{result}")

# server backup
@bot.command(name="backup", help="Make a backup of the world")
@commands.has_permissions(administrator=True)  # Limit command to admins only
async def backup(ctx):
    # use server tools telnet command?
    await ctx.send(development_message)

# ===== here the magic begins
async def main():
    try:
        output(delim_line,[to_console,to_file])
        output("Bot intialization",[to_console,to_file])
        await bot.start(DISCORD_TOKEN)  # Start the bot with your bot's token

    except KeyboardInterrupt:
        # Handle Ctrl+C press (KeyboardInterrupt)
        stop_bot = input("\nDo you really want to stop the bot? (y/n): ").strip().lower()
        if stop_bot == 'y' or stop_bot == 'yes':
            output(f"Stopping the bot...")
            await bot.close()  # Gracefully close the bot
            sys.exit(0)  # Exit the program
        else:
            output(f"Continuing to run the bot...",[to_console])

    except asyncio.CancelledError:
        output(f"Bot was stopped gracefully.")
        await bot.close()
        print("\nBot is shut down. Press Enter to continue...")
        await asyncio.to_thread(input)
        # raise  

# Run the main function to start the bot
if __name__ == "__main__":
    try:
        # Using asyncio.run for the main function call
        clean_logs(BOT_LOG)
        asyncio.run(main())
    except KeyboardInterrupt:
        # This exception will be raised if Ctrl+C is pressed, handled here
        output(f"Bot stopped due to KeyboardInterrupt")
        sys.exit(0)

#asyncio.run(main())


# notes
# 2025-04-10T20:01:33 30191.510 INF BloodMoon starting for day 194
# 2025-04-10T20:35:11 32209.132 INF Blood moon is over!
# 2025-04-10T20:35:11 32209.133 INF BloodMoon SetDay: day 201, last day 194, freq 7, range 0