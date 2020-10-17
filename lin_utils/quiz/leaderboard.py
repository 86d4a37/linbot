import json
from typing import Dict, Union

import discord
from discord import Member
from discord.ext.commands import Bot
from pkg_resources import resource_filename

from lin_utils.clientwide import YELLOW

LB_PATH = resource_filename('resources.quiz.leaderboard', 'leaderboard.json')
TS_PATH = resource_filename('resources.quiz.leaderboard', 'taisho.json')


def update_leaderboard(scorers: Dict[str, int], guild: discord.Guild, deck_name: str) -> None:
    if guild is None:
        return
    guild_id = str(guild.id)
    with open(LB_PATH, 'r') as f:
        leaderboard = json.load(f)
    if guild_id not in leaderboard:
        leaderboard[guild_id] = {}
        leaderboard[guild_id]['all'] = {}
    if deck_name not in leaderboard[guild_id]:
        leaderboard[guild_id][deck_name] = scorers
    else:
        for scorer in scorers:
            if scorer in leaderboard[guild_id][deck_name]:
                leaderboard[guild_id][deck_name][scorer] += scorers[scorer]
            else:
                leaderboard[guild_id][deck_name][scorer] = scorers[scorer]
    for scorer in scorers:
        if scorer in leaderboard[guild_id]['all']:
            leaderboard[guild_id]['all'][scorer] += scorers[scorer]
        else:
            leaderboard[guild_id]['all'][scorer] = scorers[scorer]
    with open(LB_PATH, 'w') as f:
        json.dump(leaderboard, f, indent=4)


def get_leaderboard_embed(client: Bot, guild: discord.Guild, deck_name: str,
                          taisho: bool = False) -> discord.Embed:
    embed_title = f':medal:  Leaderboard for quiz {deck_name}'
    if deck_name == 'all':
        embed_title = ':medal:  ' + '御山の大将' if taisho else 'Server leaderboard'
    embed = discord.Embed(title=embed_title, color=YELLOW)
    if guild is None:
        embed.description = 'Leaderboards are only available inside servers.'
        return embed

    guild_id = str(guild.id)
    with open(LB_PATH, 'r') as f:
        leaderboard = json.load(f)
    with open(TS_PATH, 'r') as f:
        participant_guilds = json.load(f)
    if guild_id not in leaderboard:
        return embed
    sorted_relevant_leaderboard = sorted(
        [(k, leaderboard[guild_id][deck_name][k]) for k in leaderboard[guild_id][deck_name]
         if ((k in participant_guilds[guild_id]) if taisho else True)],
        key=lambda x: -x[1]
    )
    rank = 0
    tie_increment = 0
    previous_result = float('inf')
    for (scorer, result) in sorted_relevant_leaderboard[:10]:
        if result < previous_result:
            rank += 1 + tie_increment
            tie_increment = 0
        else:
            tie_increment += 1
        embed.add_field(name=f'{rank}. {client.get_user(int(scorer))}', value=f'{result} pt',
                        inline=False)
        previous_result = result
    return embed


async def update_taisho_scorers(guild: discord.Guild,
                                leaving_member: Union[Member, None] = None) -> None:
    if guild is None:
        return

    guild_id = str(guild.id)

    with open(TS_PATH, 'r') as f:
        participant_guilds = json.load(f)

    if guild_id in participant_guilds:
        with open(LB_PATH, 'r') as f:
            leaderboard = json.load(f)
        if guild_id not in leaderboard:
            return
        role = discord.utils.get(guild.roles, name="御山の大将")
        if leaving_member and role in leaving_member.roles:
            await leaving_member.remove_roles(role)
        scorers_dict = leaderboard[guild_id]['all']
        scorers = {k: scorers_dict[k] for k in participant_guilds[guild_id] if k in scorers_dict}
        if not scorers:
            return
        max_score = max(scorers.values())
        for k in participant_guilds[guild_id]:
            user = guild.get_member(int(k))
            if scorers[k] == max_score:
                if role not in user.roles:
                    await user.add_roles(role)
            else:
                if role in user.roles:
                    await user.remove_roles(role)


def join_taisho(guild: discord.Guild, member: discord.Member) -> None:
    if guild is None:
        return
    guild_id = str(guild.id)
    with open(TS_PATH, 'r') as f:
        participant_guilds = json.load(f)
    member_id = str(member.id)
    if guild_id not in participant_guilds:
        participant_guilds[guild_id] = [member_id]
    else:
        if member_id in participant_guilds[guild_id]:
            return
        else:
            participant_guilds[guild_id].append(member_id)
    with open(TS_PATH, 'w') as f:
        json.dump(participant_guilds, f)


def leave_taisho(guild: discord.Guild, member: discord.Member) -> None:
    if guild is None:
        return
    guild_id = str(guild.id)
    with open(TS_PATH, 'r') as f:
        participant_guilds = json.load(f)
    member_id = str(member.id)
    if guild_id not in participant_guilds or member_id not in participant_guilds[guild_id]:
        return
    else:
        participant_guilds[guild_id].remove(member_id)
    with open(TS_PATH, 'w') as f:
        json.dump(participant_guilds, f)
