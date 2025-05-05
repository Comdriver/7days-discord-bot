# 🧟‍♂️ 7 Days to Die Discord Bot

   WORK IN PROGRESS

This is a Discord bot for the game **7 Days to Die** that helps monitor and manage your dedicated game server.  
It can read server logs, announce in-game events to Discord, and provide admin commands through chat.

---

## 📜 Features

- Reads server logs and posts updates to Discord
- Sends alerts about hordes, player deaths, logins, and more
- Custom commands for querying server status
- Lightweight and configurable

---

## 🛠️ Commands

| Command | Description | Admin Only |
|--------|-------------|---|
| `!backup` | Makes a backup of the saved world (WORK IN PROGRESS) | ✔ |
| `!banlist` | Shows the list of banned players | |
| `!bloodmoon` | Shows the next blood moon day and time left | |
| `!playerban` | Bans a player from the server | ✔ |
| `!playerkick` | Kicks a player from the server | ✔ |
| `!players` | Shows all the players online | |
| `!players all` | With additional paramenters, shows all the registered players on the server, online and offline | |
| `!playerunban` | Removes player from the banned list | ✔ |
| `!playerwhois` | Shows detailed information about specified player (WORK IN PROGRESS) | ✔ |
| `!reboot` | Reboots the game server (WORK IN PROGRESS) | ✔ |
| `!saveworld` | Saves the current state of world to a drive | ✔ |
| `!say` | Sends a message to the game chat | ✔ |
| `!serverstart` | Starts the game serer, if it is offline (WORK IN PROGRESS) | ✔ |
| `!setchannel` | Sets the current channel for the bot as a channel for information output | ✔ |
| `!shutdown` | Shuts down the game server (WORK IN PROGRESS) | ✔ |
| `!status` | Shows the game server current status, including autoshutdown time if servertools mod installed and configured for autoshutdown | |
| `!time` | Shows current ingame time and date | |


---

## 🧪 Installation Instructions (Windows)

0. **Create a Discord bot in Discrod**

   WORK IN PROGRESS

1. **Install Python**

   - Download the latest version of Python 3.13+ from [python.org](https://www.python.org/downloads/windows/)
   - Make sure to check ✅ **"Add Python to PATH"** during installation!

2. **Clone or download this repository**

   ```bash
   git clone https://git.zodcode.tech/ZODCODE/7days-discord-bot.git
   cd your-bot-repo
   ```

3. **Install required packages**

   WORK IN PROGRESS

4. **Configure the bot**

   - Create `bot.env` file or copy `sample_bot.env` file to `bot.env`
   - Set your Discord bot token, log file path, and other settings

| ENV | Required | Description | Default value |
|--------|-----|-------------|------|
| `GAME` | | Game server executable file | `7DaysToDieServer` |
| `GAME_PATH` | ✔ | Location of your game installation | |
| `DATA_PATH` | ✔ | Location, where your game data is stored, usually defined in serverconfig.xml as UserDataFolder and SaveGameFolder. | `7DaysToDieServer` |
| `GAME_LOG` | | Name for the game log files | `output_log` |
| `BOT_LOG` | | Name for the bot log files | `zombie_alert` |
| `GAME_LOG_KEEP_COUNT` | | How many game log files to keep | `20` |
| `BOT_LOG_KEEP_COUNT` | | How many bot log files to keep | `20` |
| `GAME_MONITOR` | | Defines if the bot should try to restart the sevrver if server is not running. `1` - run the server, `0` - just wait for the server to be started to other tools | `0` |
| `SERVERTOOLS` | | Defines if [SERVERTOOLS](https://bitbucket.org/obsessive-coder/sevendaystodie-servertools/src/core/) mod is installed on the server. `1` - installed, `0` - no servertools | `0` |
| `DISCORD_TOKEN` | ✔ | Your discord bot token, you can generate one here | |
| `DISCORD_PREFIX` | | Prefix for discord commands, like `!` in `!status` | `!` |
| `DISCORD_CHANNEL` | | Channel for the bot to output some server information, like server status or ingame chat. Can be set up after bot launch by using `setchannel` command | |
| `BM_START_TIME` | | Time of the day, when Bloodmoon STARTS on your server | `22:00` |
| `BM_END_TIME` | | Time of the day, when Bloodmoon ENDS on your server | `04:00` |

5. **Run the bot**

   ```python bot.py```

---

## 📦 Required Packages

   WORK IN PROGRESS

---

## LICENSE

   WORK IN PROGRESS


