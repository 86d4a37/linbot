import re
import time
from typing import Pattern
from aiosqlite import connect, Connection
from asyncio import wait_for, TimeoutError
from discord import Embed
from discord.ext.commands import Context
from pkg_resources import resource_filename

from lin_utils.clientwide import GREEN, RED, YELLOW, SAD

DB_PATH = resource_filename('resources.examples', 'examples_concat.db')


def compile_regex(pattern: str) -> Pattern:
    pattern = pattern.replace('@', r'\b')
    pattern = pattern.replace('"', r'\W')
    pattern = re.sub(r'(?<!\\)(\[)([^]]|\\\])*(#)',
                     r'\1\2' + u'⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎', pattern)
    pattern = pattern.replace('#', u'[⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]')
    RE = re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.UNICODE)
    return RE

    'We will abide by their decision.\n我們願意遵從他們的決定。'

async def select_sentences(db: Connection):
    async with db.execute(
            r'SELECT * FROM sentences WHERE RE(sentence) ORDER BY RANDOM() LIMIT 100') as c:
        results = await c.fetchall()
        return results

async def example_search(ctx: Context, pattern: str) -> None:
    if pattern is None:
        return
    try:
        RE = compile_regex(pattern)
    except re.error:
        embed = Embed(color=RED, title=':no_entry:  Compile error',
                      description=f'`{pattern}` is not a valid regular expression.')
        await ctx.send(embed=embed)
        return

    embed = Embed(color=YELLOW, title='Searching. Please wait...')
    msg = await ctx.send(embed=embed)

    before = time.monotonic()
    async with connect(DB_PATH) as db:
        async with db.execute(r'SELECT * FROM dictionaries') as c:
            dictionaries = dict(await c.fetchall())
        await db.create_function('RE', 1, lambda sent: bool(RE.findall(sent)))
        async with db.execute(
                r'SELECT * FROM sentences WHERE RE(sentence) ORDER BY RANDOM() LIMIT 100') as c:
            results = await c.fetchall()
    after = time.monotonic()

    if not results:
        await msg.delete()
        await ctx.message.add_reaction(SAD)
        return

    embed = Embed(
        color=GREEN,
        title=f'Found {len(results) if len(results) < 100 else "99+"} '
              f'result{"s" * (len(results) > 1)} for `{pattern}` :'
    )
    for result in results[:6]:
        sentence = RE.sub(r'__\g<0>__', result[0]).replace('____', '')
        embed.add_field(name=dictionaries[int(result[1])], value=sentence, inline=False)
    embed.set_footer(text=f'Search time: {(after - before) * 1000:,.0f} ms')
    await msg.edit(embed=embed)
