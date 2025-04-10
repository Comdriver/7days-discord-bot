import discord
from discord.ext import commands
import telnetlib3
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='bot.env')

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELNET_HOST = os.getenv("TELNET_HOST")
TELNET_PORT = int(os.getenv("TELNET_PORT", "23"))
TELNET_USER = os.getenv("TELNET_USER")
TELNET_PASS = os.getenv("TELNET_PASS")