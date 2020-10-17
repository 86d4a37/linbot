from discord import Intents
from discord.ext.commands import Bot

intents = Intents.default()
intents.members = True

prefixes = ['^']
client = Bot(command_prefix=prefixes, case_insensitive=True, intents=intents)

GREEN = 0x77dd77
RED = 0xff6961
YELLOW = 0xffef00
WHITE = 0xfefefe

SAD = '\U0001F626'
