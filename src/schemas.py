import enum
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel


class BossStatus(BaseModel):
    class StatusCode(enum.Enum):
        UNDEF = 'undef'
        DEFEATED = 'defeated'
        ACTIVE = 'active'
        WAITING = 'waiting'

    number: int
    status: StatusCode
    hp: int
    max_hp: int

    class Config:
        orm_mode = True


class Status(BaseModel):
    round: int

    class Config:
        orm_mode = True


class StatusRet(BaseModel):
    glob: Status
    detail: List[BossStatus]


class BattleLogBase(BaseModel):
    who: int
    which_day: date
    which_round: Optional[int]
    which_boss: Optional[int]
    damage: Optional[int]
    executor: int


class BattleLogCommit(BattleLogBase):
    sl: Optional[bool]
    pass


class BattleLog(BattleLogBase):
    class Types(enum.Enum):
        UNDEF = 'undef'
        NORMAL = 'normal'
        SL = 'sl'
        COMP = 'compensation'

    when: datetime
    is_defeat_boss: Optional[bool]
    real_damage: Optional[int]
    type: Types

    class Config:
        orm_mode = True


class BattleLogRet(BaseModel):
    log: BattleLog
    status: StatusRet


class CurrentBattleBase(BaseModel):
    class Types(enum.Enum):
        UNDEF = 'undef'
        ENTER = 'enter'
        WAITING = 'waiting'

    who: int
    executor: int
    which_boss: int
    type: Types
    comment: Optional[str]

    class Config:
        orm_mode = True


class CurrentBattleCommit(CurrentBattleBase):
    pass


class CurrentBattle(CurrentBattleBase):
    when: datetime


class CurrentBattleRet(BaseModel):
    log: CurrentBattle


class MemberBase(BaseModel):
    game_id: int
    contact_khl: Optional[str]
    contact_qq: Optional[str]


class Member(MemberBase):
    class Permission(enum.Enum):
        MEMBER = 'member'
        VICE_LEADER = 'vice_leader'
        LEADER = 'leader'
        EX_AID = 'ex_aid'

    permission: Permission

    class Config:
        orm_mode = True


class MemberAdd(MemberBase):
    permission: Optional[Member.Permission]
    op_key: Optional[str]


class InfoClan(BaseModel):
    name: str
    desc: str
    khl_server: str
    qq_group: str

    class Config:
        orm_mode = True


class Info(BaseModel):
    clan: InfoClan
