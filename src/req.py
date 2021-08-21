from typing import List

import aiohttp

from src import schemas
from src.config import api_root


async def get_status() -> schemas.StatusRet:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_root()}/status') as resp:
            return schemas.StatusRet(**(await resp.json()))


async def today_battle_logs() -> List[schemas.BattleLog]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_root()}/battle/log', params={'which_day': 'today'}) as resp:
            return [schemas.BattleLog(**i) for i in await resp.json()]


async def today_battle_count() -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_root()}/battle/log/count', params={'which_day': 'today'}) as resp:
            return float(await resp.text())


async def commit_battle(log: dict) -> schemas.BattleLogRet:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_root()}/battle/log', json=log) as resp:
            return schemas.BattleLogRet(**await resp.json())


async def get_current_battle(who: str = '', which_boss: str = '') -> List[schemas.CurrentBattle]:
    params = {}
    if who:
        params['who'] = who
    if which_boss:
        params['which_boss'] = which_boss
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_root()}/battle/current', params=params) as resp:
            return [schemas.CurrentBattle(**i) for i in await resp.json()]


async def commit_current_battle(log: dict) -> schemas.CurrentBattleRet:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_root()}/battle/current', json=log) as resp:
            return schemas.CurrentBattleRet(**await resp.json())


_member_list = []


async def update_members():
    global _member_list
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{api_root()}/member') as resp:
            _member_list = [schemas.Member(**i) for i in await resp.json()]


async def get_members() -> List[schemas.Member]:
    if not _member_list:
        await update_members()
    return _member_list


async def add_member(member: dict) -> schemas.Member:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{api_root()}/member', json=member) as resp:
            return schemas.Member(**await resp.json())


async def get_game_id(khl_id: str) -> List[int]:
    ret = filter(lambda x: x.contact_khl == khl_id, await get_members())
    if not ret:
        await update_members()
        ret = filter(lambda x: x.contact_khl == khl_id, await get_members())
        if not ret:
            raise ValueError(f'Member not found with khl_id:{khl_id}')
    return [i.game_id for i in ret]
