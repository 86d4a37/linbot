import asyncio
import random
import time
from collections import defaultdict
from typing import Union

import discord
from discord.ext.commands import Bot, Context

from lin_utils.clientwide import GREEN, RED, WHITE, prefixes
from lin_utils.quiz.deck import Deck, get_decks
from lin_utils.quiz.image import send_image_of_text
from lin_utils.quiz.leaderboard import (get_leaderboard_embed, update_leaderboard,
                                        update_taisho_scorers)

TIMEOUT_TWO = 2.5

LANG_EMOJIS = {'ja': ':flag_jp:',
               'ko': ':flag_kr:',
               'zh_CN': ':flag_cn:',
               'zh_TW': ':flag_tw:'}
LANG_NAMES = {'ja': 'Japanese',
              'ko': 'Korean (South Korea)',
              'zh_CN': 'Chinese (Simplified)',
              'zh_TW': 'Chinese (Taiwan)'}

quiz_running_channels = set()
review = {}


async def run_quiz(client: Bot, ctx: Context, deck_name: Union[str, None] = None, length: int = 0,
                   sequential: bool = False, timeout_one: Union[float, None] = None,
                   timeout_two: float = 2.5) -> None:

    go_sign = ':checkered_flag:'
    deck_set, deck_dict = get_decks()
    is_review = False

    global quiz_running_channels
    global review

    if ctx.channel.id in quiz_running_channels:
        embed = discord.Embed(
            title=':octagonal_sign:  A quiz is running in this channel. '
                  'Please wait for it to finish.',
            color=RED
        )
        await ctx.send(embed=embed)
        return

    if deck_name in {'review', 'r'}:
        is_review = True
        if ctx.channel.id in review:
            deck_name, failed_indices = review[ctx.channel.id]
        else:
            embed = discord.Embed(
                title=':octagonal_sign:  There are no questions for review in this channel.',
                color=RED)
            await ctx.send(embed=embed)
            return
    elif deck_name in {'list', 'l'}:
        embed = discord.Embed(
            color=GREEN,
            title='List of quizzes',
            description=f'Type `{prefixes[0]}q [quiz name] [optional max score]` to play.\n'
        )
        if ctx.channel.id in review:
            embed.add_field(
                name=f':memo:  Review of {review[ctx.channel.id][0]} '
                     f'({len(review[ctx.channel.id][1])} '
                     f'question{"s" * (len(review[ctx.channel.id][1]) != 1)})',
                value='```review```',
                inline=False)
        for _lang in sorted(deck_dict.keys(), key=lambda x: LANG_NAMES[x]):
            embed.add_field(name=f'{LANG_EMOJIS[_lang]} {LANG_NAMES[_lang]}',
                            value=f'```\n{", ".join(sorted(deck_dict[_lang]))}```',
                            inline=False)
        await ctx.send(embed=embed)
        return
    elif deck_name is None or deck_name not in deck_set:
        embed = discord.Embed(
            color=GREEN,
            title='Quiz operation',
            description=f'Type `{prefixes[0]}q [quiz name] [optional max score]` to play.\n'
                        f'Type `{prefixes[0]}q list` to see the list of valid quizzes.')
        await ctx.send(embed=embed)
        return
    else:
        failed_indices = set()

    lang = ''
    for _lang in deck_dict:
        if deck_name in deck_dict[_lang]:
            lang = _lang
            break

    deck = Deck(deck_name, lang)
    quiz_running_channels.add(ctx.channel.id)
    await client.change_presence(
        activity=discord.Game(name=(f"{len(quiz_running_channels)} quiz" +
                                    "zes" * (len(quiz_running_channels) != 1)))
    )

    to_stop = False
    num_wrong_in_a_row = 0
    scorers = defaultdict(int)

    if is_review:
        order = list(failed_indices)
        length = len(order)
    elif sequential:
        length %= len(deck)
        order = range(length, len(deck))
        length = len(order)
    else:
        order = list(range(len(deck)))
        random.shuffle(order)
        length = min(length, len(deck))
        if length <= 0:
            length = len(deck)

    embed = discord.Embed(title=f'{go_sign}  Starting {"review of " * is_review}quiz {deck_name}'
                                f'{" in 5 seconds" * (timeout_two > 0)}',
                          color=WHITE,
                          description=f'First to {length} point{"s" * (length != 1)} wins.')
    embed.add_field(name='Quiz information', value=deck.description, inline=False)
    await ctx.send(embed=embed)

    if timeout_two:
        await asyncio.sleep(5.0)

    sorted_temp_scorers = None
    manten_score = 0

    for idx in order:
        if num_wrong_in_a_row >= 5:
            embed = discord.Embed(title=':octagonal_sign:  Five consecutive incorrect answers.',
                                  color=RED)
            await ctx.send(embed=embed)
            break
        if to_stop:
            embed = discord.Embed(title=':octagonal_sign:  Stop signal received.',
                                  color=RED)
            await ctx.send(embed=embed)
            break
        if sorted_temp_scorers:
            if max([scores[1] for scores in sorted_temp_scorers]) >= length:
                break
        embed = discord.Embed(title=f'{go_sign}  {"Review of " * is_review}'
                                    f'{deck_name} to {length}',
                              color=WHITE)
        embed.set_footer(text='Type >stop to stop or .. to skip.')
        if deck.type == 'text':
            embed.description = '```\n' + deck[idx]['question'] + '```'
            await ctx.send(embed=embed)
        elif deck.type == 'url':
            embed.set_image(url=deck[idx]['question'])
            await ctx.send(embed=embed)
        else:
            file, filename = send_image_of_text(ctx, deck.lang, txt=deck[idx]['question'],
                                                embed=True)
            embed.set_image(url='attachment://' + filename)
            await ctx.send(embed=embed, file=file)

        answerers = set()

        time_left = deck.timeout if timeout_one is None else timeout_one

        # Loop to wait for the answer of a single question
        while time_left > 0.0:
            q_start = time.monotonic()
            try:
                ans = await client.wait_for(
                    'message',
                    timeout=time_left,
                    check=lambda message: (ctx.channel.id == message.channel.id
                                           and not message.author.bot)
                )
            except asyncio.TimeoutError:
                time_left = 0.0
                continue
            else:
                if ans.content.lower() in {'stop', '>stop'}:
                    time_left = 0.0
                    to_stop = True
                elif ('..' == ans.content or '。。' == ans.content or 'skip' == ans.content.lower()
                      or '>skip' == ans.content.lower()):
                    time_left = 0.0
                else:
                    if deck.check_equivalency(idx, ans.content):
                        if ans.author.id not in answerers:
                            answerers.add(ans.author.id)
                            scorers[str(ans.author.id)] += 1
                        time_left = timeout_two
                    else:
                        new_time = time.monotonic()
                        elapsed = new_time - q_start
                        time_left -= elapsed

        if not to_stop:
            manten_score += 1
        if answerers:
            if is_review:
                failed_indices.remove(idx)
            num_wrong_in_a_row = 0
            if deck.type == 'image':
                embed = discord.Embed(title=':white_check_mark:  ' + deck[idx]['question'],
                                      description='\n'.join(deck[idx]['answers']),
                                      color=GREEN)
            else:
                embed = discord.Embed(
                    title=f':white_check_mark:  {"、".join(deck[idx]["answers"])}',
                    color=GREEN
                )

            sorted_temp_scorers = sorted(
                [(client.get_user(a), scorers[str(a)]) for a in answerers],
                key=lambda x: -x[1])
            embed.add_field(name='Scorers', value='\n'.join(
                (f'{a}: {s} pt ({s / manten_score * 100 if manten_score > 0 else 0.:.0f}%)' for
                 a, s in sorted_temp_scorers)), inline=False)

        elif not to_stop:
            failed_indices.add(idx)
            num_wrong_in_a_row += 1
            if deck.type == 'image':
                embed = discord.Embed(title=':no_entry:  ' + deck[idx]['question'],
                                      description='\n'.join(deck[idx]['answers']), color=RED)
            else:
                embed = discord.Embed(title=':no_entry:  ' + '、'.join(deck[idx]['answers']),
                                      color=RED)

        if 'comment' in deck[idx] and deck[idx]['comment']:
            embed.add_field(name='Comment', value=deck[idx]['comment'], inline=False)
        embed.set_footer(text=f'No. {idx} in deck {deck_name}')
        await ctx.send(embed=embed)

    sorted_scorers = sorted([(k, scorers[k]) for k in scorers], key=lambda x: -x[1])

    embed = discord.Embed(title=f'{go_sign}  Final results', color=WHITE)
    for rank, (scorer, result) in enumerate(sorted_scorers[:10], 1):
        embed.add_field(
            name=f'{rank}. {client.get_user(int(scorer))}',
            value=f'{result} pt ({result / manten_score * 100 if manten_score > 0 else 0.:.0f}%)',
            inline=False)
    if failed_indices:
        review[ctx.channel.id] = (deck_name, failed_indices)
        embed.add_field(
            name='Note',
            value=f'Type `{prefixes[0]}q review` to play the {len(failed_indices)} failed question'
                  f'{"s" * (len(failed_indices) != 1)}',
            inline=False
        )
        if deck.type != 'image':
            embed.set_footer(
                text=('　'.join(('×' + deck[idx]['answers'][0] for idx in failed_indices)))
            )
        else:
            embed.set_footer(
                text=('　'.join(('×' + deck[idx]['question'] for idx in failed_indices)))
            )
    else:
        if ctx.channel.id in review:
            del review[ctx.channel.id]

    await ctx.send(embed=embed)
    quiz_running_channels.remove(ctx.channel.id)

    if len(quiz_running_channels):
        await client.change_presence(
            activity=discord.Game(name=(f"{len(quiz_running_channels)} quiz" +
                                        "zes" * (len(quiz_running_channels) != 1)))
        )
    else:
        await client.change_presence(activity=None)

    if is_review:
        deck_name = 'review'

    update_leaderboard(scorers, ctx.guild, deck_name)
    await ctx.send(embed=get_leaderboard_embed(client, ctx.guild, deck_name))
    await update_taisho_scorers(ctx.guild)
