from discord import Embed
from lin_utils.clientwide import prefixes

help_embed = Embed(color=0x77dd77, title=':beginner: linbot help',
                   descrption='This is the testing version of linbot.')

help_embed.add_field(name='Prefix', value=f'The current prefix is set to `{prefixes[0]}`.',
                     inline=False)

help_embed.add_field(name='Quiz game',
                     value=f'Type `{prefixes[0]}q` for more information.', inline=False)
