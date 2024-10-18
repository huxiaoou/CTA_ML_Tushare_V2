from typing import NewType, Literal
from dataclasses import dataclass
from husfort.qsqlite import CDbStruct

"""
----------------------------
Part I: test returns
----------------------------
"""

TReturnClass = NewType("TReturnClass", str)
TReturnName = NewType("TReturnName", str)
TReturnNames = NewType("TReturnNames", list[TReturnName])
TReturnComb = NewType("TReturnComb", tuple[TReturnClass, TReturnName, str])
TReturn = NewType("TReturn", tuple[TReturnClass, TReturnName])
TRetType = Literal["RAW", "NEU"]
TRetPrc = Literal["Opn", "CLs"]


@dataclass(frozen=True)
class CRet:
    ret_type: TRetType
    ret_prc: TRetPrc
    win: int
    lag: int

    @property
    def shift(self) -> int:
        return self.win + self.lag

    @property
    def ret_class(self) -> TReturnClass:
        return TReturnClass(f"{self.win:03d}L{self.lag:d}")

    @property
    def ret_name(self) -> TReturnName:
        return TReturnName(f"{self.ret_prc}{self.win:03d}L{self.lag:d}{self.ret_type}")


"""
----------------------------------
Part II: factors configuration
----------------------------------
"""

TFactorClass = NewType("TFactorClass", str)
TFactorName = NewType("TFactorName", str)
TFactorNames = NewType("TFactorNames", list[TFactorName])
TFactorClassAndNames = NewType("TFactorClassAndNames", tuple[TFactorClass, TFactorNames])
TFactorComb = NewType("TFactorComb", tuple[TFactorClass, TFactorNames, str])  # str is for subdirectory
TFactor = NewType("TFactor", tuple[TFactorClass, TFactorName])
TFactorsPool = NewType("TFactorsPool", list[TFactorComb])

"""
--------------------------------------
Part III: Instruments and Universe
--------------------------------------
"""


@dataclass(frozen=True)
class CCfgInstru:
    sectorL0: str
    sectorL1: str


TInstruName = NewType("TInstruName", str)
TUniverse = NewType("TUniverse", dict[TInstruName, CCfgInstru])

"""
--------------------------------
Part IV: generic and project
--------------------------------
"""


@dataclass(frozen=True)
class CCfgAvlbUnvrs:
    win: int
    amount_threshold: float


@dataclass(frozen=True)
class CCfgTrn:
    wins: list[int]


@dataclass(frozen=True)
class CCfgPrd:
    wins: list[int]


@dataclass(frozen=True)
class CCfgSim:
    wins: list[int]


@dataclass(frozen=True)
class CCfgConst:
    COST: float
    SECTORS: list[str]
    LAG: int


@dataclass(frozen=True)
class CCfgProj:
    # --- shared
    calendar_path: str
    root_dir: str
    db_struct_path: str
    alternative_dir: str
    market_index_path: str
    by_instru_pos_dir: str
    by_instru_pre_dir: str
    by_instru_min_dir: str

    # --- project
    project_root_dir: str
    available_dir: str
    market_dir: str
    test_return_dir: str
    factors_by_instru_dir: str
    neutral_by_instru_dir: str

    # --- project parameters
    universe: TUniverse
    avlb_unvrs: CCfgAvlbUnvrs
    mkt_idxes: dict
    const: CCfgConst
    trn: CCfgTrn
    prd: CCfgPrd
    sim: CCfgSim

    @property
    def test_rets_wins(self) -> list[int]:
        return self.prd.wins + self.sim.wins


@dataclass(frozen=True)
class CCfgDbStruct:
    # --- shared database
    macro: CDbStruct
    forex: CDbStruct
    fmd: CDbStruct
    position: CDbStruct
    basis: CDbStruct
    stock: CDbStruct
    preprocess: CDbStruct
    minute_bar: CDbStruct

    # --- project database
    available: CDbStruct
    market: CDbStruct
