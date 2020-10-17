import time
from typing import Union

import discord
from discord.ext.commands import CommandNotFound, Context

from lin_utils.auth import token
from lin_utils.clientwide import GREEN, SAD, client
from lin_utils.help import help_embed
from lin_utils.quiz.leaderboard import (get_leaderboard_embed, join_taisho, leave_taisho,
                                        update_taisho_scorers)
from lin_utils.quiz.run import run_quiz

client.remove_command('help')


@client.event
async def on_command_error(ctx: Context, error: Exception):
    if isinstance(error, CommandNotFound):
        return
    raise error


@client.command(aliases=['h'])
async def help(ctx: Context) -> None:
    await ctx.send(embed=help_embed)


@client.command()
async def ping(ctx: Context) -> None:
    before = time.monotonic()
    embed = discord.Embed(color=GREEN, title=f':ping_pong: {ctx.message.author}')
    msg = await ctx.send(embed=embed)
    after = time.monotonic()
    embed.description = f'Latency: **{(after - before) * 1000:.1f} ms**'
    await msg.edit(embed=embed)


@client.command(aliases=['q!'])
async def q(ctx: Context, *, txt: Union[str, None]) -> None:
    if ctx.message.content[1:3] == 'q!':
        timeout_two = 0.0
    else:
        timeout_two = 2.5
    if txt is None:
        await run_quiz(client, ctx)
    else:
        txt = txt.lower()
        if len(txt.split()) == 1:
            await run_quiz(client, ctx, txt.split()[0], length=15, timeout_two=timeout_two)
        elif len(txt.split()) == 2:
            quiz_length = txt.split()[1]
            sequential = quiz_length.endswith('-')
            if sequential:
                quiz_length = quiz_length[:-1]
            try:
                quiz_length = int(quiz_length)
            except ValueError:
                quiz_length = 0 if sequential else 15
            await run_quiz(client, ctx, txt.split()[0], length=quiz_length, sequential=sequential,
                           timeout_two=timeout_two)


@client.command()
async def optin(ctx: Context, *, txt: Union[str, None]) -> None:
    if txt is not None:
        await ctx.message.add_reaction(SAD)
    else:
        join_taisho(ctx.guild, ctx.message.author)
        await update_taisho_scorers(ctx.guild)
        await ctx.message.add_reaction('\u2705')


@client.command()
async def optout(ctx: Context, *, txt: Union[str, None]) -> None:
    if txt is not None:
        await ctx.message.add_reaction(SAD)
    else:
        leave_taisho(ctx.guild, ctx.message.author)
        await update_taisho_scorers(ctx.guild, leaving_member=ctx.message.author)
        await ctx.message.add_reaction('\u2705')


@client.command(aliases=['lbt', 'lbr'])
async def lb(ctx: Context, *, txt: str = 'all') -> None:
    taisho = ctx.message.content[1:4] in {'lbr', 'lbt'}
    await ctx.send(embed=get_leaderboard_embed(client, ctx.guild, txt, taisho))

client.run(token)
