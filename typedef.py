import itertools as ittl
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


@dataclass(frozen=True)
class CCfgFactor:
    @property
    def factor_class(self) -> TFactorClass:
        raise NotImplementedError

    @property
    def factor_names(self) -> TFactorNames:
        raise NotImplementedError

    @property
    def factor_names_neu(self) -> TFactorNames:
        return TFactorNames([TFactorName(_.replace("RAW", "NEU")) for _ in self.factor_names])

    def get_raw_class_and_names(self) -> TFactorClassAndNames:
        return TFactorClassAndNames((self.factor_class, self.factor_names))

    def get_neu_class_and_names(self) -> TFactorClassAndNames:
        neu_names = TFactorNames([TFactorName(_.replace("RAW", "NEU")) for _ in self.factor_names])
        return TFactorClassAndNames((self.factor_class, neu_names))

    def get_combs_raw(self, sub_dir: str) -> TFactorsPool:
        factor_class, factor_names = self.get_raw_class_and_names()
        return TFactorsPool([TFactorComb((factor_class, factor_names, sub_dir))])

    def get_combs_neu(self, sub_dir: str) -> TFactorsPool:
        factor_class, factor_names = self.get_neu_class_and_names()
        return TFactorsPool([TFactorComb((factor_class, factor_names, sub_dir))])

    def get_combs(self, sub_dir: str) -> TFactorsPool:
        return TFactorsPool(self.get_combs_raw(sub_dir) + self.get_combs_neu(sub_dir))


# cfg for factors
@dataclass(frozen=True)
class CCfgFactorMTM(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("MTM")

    @property
    def factor_names(self) -> TFactorNames:
        return TFactorNames([TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins])


@dataclass(frozen=True)
class CCfgFactorSKEW(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("SKEW")

    @property
    def factor_names(self) -> TFactorNames:
        return TFactorNames([TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins])


@dataclass(frozen=True)
class CCfgFactorRS(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("RS")

    @property
    def factor_names(self) -> TFactorNames:
        rspa = [TFactorName(f"{self.factor_class}PA{w:03d}_RAW") for w in self.wins]
        rsla = [TFactorName(f"{self.factor_class}LA{w:03d}_RAW") for w in self.wins]
        return TFactorNames(rspa + rsla)


@dataclass(frozen=True)
class CCfgFactorBASIS(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("BASIS")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}D{w:03d}_RAW") for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorTS(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("TS")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}D{w:03d}_RAW") for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorS0BETA(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("S0BETA")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}{self.wins[0]:03d}D{w:03d}_RAW") for w in self.wins[1:]]
        # n2 = [f"{self.factor_class}{w:03d}RES_RAW" for w in self.wins]
        # n3 = [f"{self.factor_class}{w:03d}RESSTD_RAW" for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorS1BETA(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("S1BETA")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}{self.wins[0]:03d}D{w:03d}_RAW") for w in self.wins[1:]]
        # n2 = [f"{self.factor_class}{w:03d}RES_RAW" for w in self.wins]
        # n3 = [f"{self.factor_class}{w:03d}RESSTD_RAW" for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorCBETA(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CBETA")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}{self.wins[0]:03d}D{w:03d}_RAW") for w in self.wins[1:]]
        # n2 = [f"{self.factor_class}{w:03d}RES_RAW" for w in self.wins]
        # n3 = [f"{self.factor_class}{w:03d}RESSTD_RAW" for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorIBETA(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("IBETA")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}{self.wins[0]:03d}D{w:03d}_RAW") for w in self.wins[1:]]
        # n2 = [f"{self.factor_class}{w:03d}RES_RAW" for w in self.wins]
        # n3 = [f"{self.factor_class}{w:03d}RESSTD_RAW" for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorPBETA(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("PBETA")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"{self.factor_class}{self.wins[0]:03d}D{w:03d}_RAW") for w in self.wins[1:]]
        # n2 = [f"{self.factor_class}{w:03d}RES_RAW" for w in self.wins]
        # n3 = [f"{self.factor_class}{w:03d}RESSTD_RAW" for w in self.wins]
        return TFactorNames(n0 + n1)


@dataclass(frozen=True)
class CCfgFactorCTP(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CTP")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorCTR(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CTR")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorCVP(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CVP")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorCVR(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CVR")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorCSP(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CSP")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorCSR(CCfgFactor):
    wins: list[int]
    tops: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("CSR")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{int(t * 10):02d}_RAW") for w, t in
              ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorNOI(CCfgFactor):
    wins: list[int]
    tops: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("NOI")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{t:02d}_RAW") for w, t in ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorNDOI(CCfgFactor):
    wins: list[int]
    tops: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("NDOI")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{t:02d}_RAW") for w, t in ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorWNOI(CCfgFactor):
    wins: list[int]
    tops: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("WNOI")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{t:02d}_RAW") for w, t in ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorWNDOI(CCfgFactor):
    wins: list[int]
    tops: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("WNDOI")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}T{t:02d}_RAW") for w, t in ittl.product(self.wins, self.tops)]
        return TFactorNames(n0)


@dataclass(frozen=True)
class CCfgFactorAMP(CCfgFactor):
    wins: list[int]
    lbds: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("AMP")

    @property
    def factor_names(self) -> TFactorNames:
        nh = [TFactorName(f"{self.factor_class}{w:03d}T{int(l * 10):02d}H_RAW") for w, l in
              ittl.product(self.wins, self.lbds)]
        nl = [TFactorName(f"{self.factor_class}{w:03d}T{int(l * 10):02d}L_RAW") for w, l in
              ittl.product(self.wins, self.lbds)]
        nd = [TFactorName(f"{self.factor_class}{w:03d}T{int(l * 10):02d}D_RAW") for w, l in
              ittl.product(self.wins, self.lbds)]
        return TFactorNames(nh + nl + nd)


@dataclass(frozen=True)
class CCfgFactorEXR(CCfgFactor):
    wins: list[int]
    dfts: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("EXR")

    @property
    def factor_names(self) -> TFactorNames:
        n0 = [TFactorName(f"{self.factor_class}{w:03d}_RAW") for w in self.wins]
        n1 = [TFactorName(f"DXR{w:03d}D{d:02d}_RAW") for w, d in ittl.product(self.wins, self.dfts)]
        n2 = [TFactorName(f"AXR{w:03d}D{d:02d}_RAW") for w, d in ittl.product(self.wins, self.dfts)]
        return TFactorNames(n0 + n1 + n2)


@dataclass(frozen=True)
class CCfgFactorSMT(CCfgFactor):
    wins: list[int]
    lbds: list[float]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("SMT")

    @property
    def factor_names(self) -> TFactorNames:
        n_prc = [TFactorName(f"{self.factor_class}{w:03d}T{int(l * 10):02d}P_RAW") for w, l in
                 ittl.product(self.wins, self.lbds)]
        n_ret = [TFactorName(f"{self.factor_class}{w:03d}T{int(l * 10):02d}R_RAW") for w, l in
                 ittl.product(self.wins, self.lbds)]
        return TFactorNames(n_prc + n_ret)


@dataclass(frozen=True)
class CCfgFactorRWTC(CCfgFactor):
    wins: list[int]

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("RWTC")

    @property
    def factor_names(self) -> TFactorNames:
        nu = [TFactorName(f"{self.factor_class}{w:03d}U_RAW") for w in self.wins]
        nd = [TFactorName(f"{self.factor_class}{w:03d}D_RAW") for w in self.wins]
        nt = [TFactorName(f"{self.factor_class}{w:03d}T_RAW") for w in self.wins]
        nv = [TFactorName(f"{self.factor_class}{w:03d}V_RAW") for w in self.wins]
        return TFactorNames(nu + nd + nt + nv)


@dataclass(frozen=True)
class CCfgFactorTA(CCfgFactor):
    macd: tuple[int, int, int]
    bbands: tuple[int, int, int]
    sar: tuple[float, float]
    adx: int
    bop: None
    cci: int
    cmo: int
    rsi: int
    mfi: int
    willr: int
    adosc: tuple[int, int]
    obv: int
    natr: int

    @property
    def factor_class(self) -> TFactorClass:
        return TFactorClass("TA")

    @property
    def name_macd(self) -> TFactorName:
        fast, slow, diff = self.macd
        return TFactorName(f"{self.factor_class}MACDF{fast}S{slow}D{diff}_RAW")

    @property
    def name_bbands(self) -> TFactorName:
        timeperiod, up, dn = self.bbands
        return TFactorName(f"{self.factor_class}BBANDT{timeperiod}U{up}D{dn}_RAW")

    @property
    def name_sar(self) -> TFactorName:
        acceleration, maximum = self.sar
        return TFactorName(f"{self.factor_class}SARA{int(acceleration * 100):02d}M{int(maximum * 100):02d}_RAW")

    @property
    def name_adx(self) -> TFactorName:
        timeperiod = self.adx
        return TFactorName(f"{self.factor_class}ADXT{timeperiod}_RAW")

    @property
    def name_bop(self) -> TFactorName:
        return TFactorName(f"{self.factor_class}BOP_RAW")

    @property
    def name_cci(self) -> TFactorName:
        timeperiod = self.cci
        return TFactorName(f"{self.factor_class}CCIT{timeperiod}_RAW")

    @property
    def name_cmo(self) -> TFactorName:
        timeperiod = self.cmo
        return TFactorName(f"{self.factor_class}CMOT{timeperiod}_RAW")

    @property
    def name_rsi(self) -> TFactorName:
        timeperiod = self.rsi
        return TFactorName(f"{self.factor_class}RSIT{timeperiod}_RAW")

    @property
    def name_mfi(self) -> TFactorName:
        timeperiod = self.mfi
        return TFactorName(f"{self.factor_class}MFIT{timeperiod}_RAW")

    @property
    def name_willr(self) -> TFactorName:
        timeperiod = self.willr
        return TFactorName(f"{self.factor_class}WILLRT{timeperiod}_RAW")

    @property
    def name_adosc(self) -> TFactorName:
        fast, slow = self.adosc
        return TFactorName(f"{self.factor_class}ADOSCF{fast}S{slow}_RAW")

    @property
    def name_obv(self) -> TFactorName:
        timeperiod = self.obv
        return TFactorName(f"{self.factor_class}OBVT{timeperiod}_RAW")

    @property
    def name_natr(self) -> TFactorName:
        timeperiod = self.natr
        return TFactorName(f"{self.factor_class}NATRT{timeperiod}_RAW")

    @property
    def factor_names(self) -> TFactorNames:
        names_ta = [
            self.name_macd, self.name_bbands, self.name_sar, self.name_adx,
            self.name_bop, self.name_cci, self.name_cmo, self.name_rsi, self.name_mfi,
            self.name_willr, self.name_adosc, self.name_obv, self.name_natr,
        ]
        return TFactorNames(names_ta)


@dataclass(frozen=True)
class CCfgFactors:
    MTM: CCfgFactorMTM | None
    SKEW: CCfgFactorSKEW | None
    RS: CCfgFactorRS | None
    BASIS: CCfgFactorBASIS | None
    TS: CCfgFactorTS | None
    S0BETA: CCfgFactorS0BETA | None
    S1BETA: CCfgFactorS1BETA | None
    CBETA: CCfgFactorCBETA | None
    IBETA: CCfgFactorIBETA | None
    PBETA: CCfgFactorPBETA | None
    CTP: CCfgFactorCTP | None
    CTR: CCfgFactorCTR | None
    CVP: CCfgFactorCVP | None
    CVR: CCfgFactorCVR | None
    CSP: CCfgFactorCSP | None
    CSR: CCfgFactorCSR | None
    NOI: CCfgFactorNOI | None
    NDOI: CCfgFactorNDOI | None
    WNOI: CCfgFactorWNOI | None
    WNDOI: CCfgFactorWNDOI | None
    AMP: CCfgFactorAMP | None
    EXR: CCfgFactorEXR | None
    SMT: CCfgFactorSMT | None
    RWTC: CCfgFactorRWTC | None
    TA: CCfgFactorTA | None

    def values(self) -> list[CCfgFactor]:
        res = []
        for _, v in vars(self).items():
            if v is not None:
                res.append(v)
        return res


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
    factors: dict

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
