# 🧟‍♂️ Zombie Alert - 7 Days to Die Discord Bot

   WORK IN PROGRESS

Zombie Alert is a Discord bot for the game **7 Days to Die** that helps monitor and manage your dedicated game server.  
It can read server logs, announce in-game events to Discord, and provide admin commands through chat.

If [SERVERTOOLS](https://bitbucket.org/obsessive-coder/sevendaystodie-servertools/src/core/) are installed on the server, bot can utilize some of the SERVERTOOLS commands.

---

## 📜 Features

- Reads server logs and posts updates to Discord
- Sends alerts about hordes, player deaths, logins, and more
- Custom commands for querying server status
- Lightweight and configurable

---

## 🛠️ Commands


| Command             | Description                                                                                   | Admin Only |
|---------------------|-----------------------------------------------------------------------------------------------|------------|
| <code>!backup</code>        | Creates a backup of the current world (WORK IN PROGRESS)                                         | ✔          |
| <code>!banlist</code>       | Displays the list of banned players                                                              |            |
| <code>!bloodmoon</code>     | Shows when the next blood moon will occur and how much time is left                             |            |
| <code>!playerban</code>     | Bans a specified player from the server                                                          | ✔          |
| <code>!playerkick</code>    | Kicks a player from the server                                                                   | ✔          |
| <code>!players</code>       | Lists players currently online                                                                   |            |
| <code>!players&nbsp;all</code> | Shows all registered players (online and offline) with extra details                          |            |
| <code>!playerunban</code>   | Removes a player from the ban list                                                               | ✔          |
| <code>!playerwhois</code>   | Displays detailed info about a specific player (WORK IN PROGRESS)                                | ✔          |
| <code>!reboot</code>        | Restarts the game server (WORK IN PROGRESS)                                                      | ✔          |
| <code>!saveworld</code>     | Saves the current state of the world                                                             | ✔          |
| <code>!say</code>           | Sends a message to the in-game chat                                                              | ✔          |
| <code>!serverstart</code>   | Starts the server if it is offline (WORK IN PROGRESS)                                            | ✔          |
| <code>!setchannel</code>    | Sets the current Discord channel as the bot's output channel                                     | ✔          |
| <code>!shutdown</code>      | Shuts down the game server (WORK IN PROGRESS)                                                    | ✔          |
| <code>!status</code>        | Displays the server's current status and autoshutdown info (if servertools mod installed and configured for autoshutdown) |            |
| <code>!time</code>          | Shows the current in-game time and date                                                         |            |

---

## 🧪 Installation Instructions (Windows)

0. **Create a Discord bot in Discrod**

   1. Go to the Developer Portal
      - Visit: [https://discord.com/developers/applications](https://discord.com/developers/applications)
      - Log in with your Discord account if needed.
   2. Create a New Application
      - Click the "New Application" button (top right).
      - Give your bot a name (this will be its display name).
      - Click "Create".
   3. Create the Bot
      - In the left sidebar, go to the “Bot” section.
      - Click “Add Bot”, then “Yes, do it!” to confirm.
      - (Optional) Set a profile picture or name for your bot.
   4. Get the Bot Token
      - Still in the “Bot” section, click “Reset Token” or “Copy” under Token.
      - Save the token somewhere safe – you’ll use it in your bot configuration.
      - ⚠️ Never share it! It gives full control of your bot.

1. **Install Python**

   - Download the latest version of Python 3.13+ from [python.org](https://www.python.org/downloads/windows/)
   - Make sure to check ✅ **"Add Python to PATH"** during installation!

2. **Clone or download this repository**

   ```bash
   git clone https://git.zodcode.tech/ZODCODE/7days-discord-bot.git
    ```
     ```bash
   cd your-bot-repo
   ```

3. **Install required packages**

   WORK IN PROGRESS

4. **Configure the bot**

   - Create `bot.env` file or copy `sample.bot.env` file to `bot.env`
   - Set your Discord bot token, log file path, and other settings

| ENV | Required | Description | Default value |
|--------|-----|-------------|------|
| `GAME` | | Game server executable file | 7DaysToDieServer |
| `GAME_PATH` | ✔ | Location of your game installation | |
| `DATA_PATH` | ✔ | Location, where your game data is stored, usually defined in serverconfig.xml as UserDataFolder and SaveGameFolder. | 7DaysToDieServer |
| `GAME_LOG` | | Name for the game log files | output_log |
| `BOT_LOG` | | Name for the bot log files | zombie_alert |
| `GAME_LOG_KEEP_COUNT` | | How many game log files to keep | 20 |
| `BOT_LOG_KEEP_COUNT` | | How many bot log files to keep | 20 |
| `GAME_MONITOR` | | Defines if the bot should try to restart the sevrver if server is not running. `1` - run the server, `0` - just wait for the server to be started to other tools | 0 |
| `SERVERTOOLS` | | Defines if [SERVERTOOLS](https://bitbucket.org/obsessive-coder/sevendaystodie-servertools/src/core/) mod is installed on the server. `1` - installed, `0` - no servertools | 0 |
| `DISCORD_TOKEN` | ✔ | Your discord bot token, you can generate one here | |
| `DISCORD_PREFIX` | | Prefix for discord commands, like `!` in `!status` | ! |
| `DISCORD_CHANNEL` | | Channel for the bot to output some server information, like server status or ingame chat. Can be set up after bot launch by using `setchannel` command | |
| `TELNET_HOST` | | Address for your game server telnet | 127.0.0.1 |
| `BM_START_TIME` | | Time of the day, when Bloodmoon STARTS on your server | 22:00 |
| `BM_END_TIME` | | Time of the day, when Bloodmoon ENDS on your server | 04:00 |

5. **Run the bot**

      ```bash
      python 7daysbot.py
      ```

6. **Add the bot to your server**

   1. Go to the Developer Portal again
      - Visit: [https://discord.com/developers/applications](https://discord.com/developers/applications)
      - Log in with your Discord account if needed.
   2. Go to the “OAuth2 > URL Generator”
      - In the left sidebar, go to “OAuth2” > “URL Generator”.
   3. Generate an Invite Link
      - Under Scopes, check: bot
      - Under Bot Permissions, check what your bot will need: Send Messages, Embed Links, Read MEssage History, Mention Everyone
      - Copy the generated URL at the bottom.
   4. Invite the Bot to Your Server
      - Paste the URL into your browser and choose a server you manage.
      - Click “Authorize” and complete the CAPTCHA.

---

## 📦 Required Packages

   WORK IN PROGRESS

---

## LICENSE

   WORK IN PROGRESS


