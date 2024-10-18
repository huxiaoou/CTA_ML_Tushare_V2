import os
import pandas as pd
import scipy.stats as sps
from husfort.qsqlite import CDbStruct, CSqlTable, CSqlVar


def convert_mkt_idx(mkt_idx: str, prefix: str = "I") -> str:
    return f"{prefix}{mkt_idx.replace('.', '_')}"


# ---------------------------------------
# ------ algorithm: neutralization ------
# ---------------------------------------

def neutralize_by_date(
        raw_data: pd.DataFrame,
        old_names: list[str],
        new_names: list[str],
        date_name: str = "trade_date",
        sec_name: str = "sectorL1",
        instru_name: str = "instrument",
) -> pd.DataFrame:
    """

    :param raw_data: a dataframe with columns = [date_name, instru_name, sec_name] + old_names
    :param old_names:
    :param new_names:
    :param date_name:
    :param sec_name:
    :param instru_name:
    :return: a dataframe, old_names are normalized, and renamed as new_names
             columns = [date_name, instru_name, sec_name] + new_names
    """

    rename_mapper = {o: n for o, n in zip(old_names, new_names)}
    # --- get instrument rank for each day
    rank_data = (
        raw_data[[date_name] + old_names]
        .groupby(by=date_name, group_keys=False)[old_names]
        .apply(lambda z: z.rank() / (z.count() + 1))
    )

    # --- map rank to random variable with normal distribution
    norm_rv_data = rank_data.map(sps.norm.ppf)
    norm_data = pd.merge(
        left=raw_data[[date_name, instru_name, sec_name]],
        right=norm_rv_data,
        how="inner",
        left_index=True, right_index=True,
    )

    # --- neutralize for each sector and day
    neu_data = (
        norm_data[[date_name, sec_name] + old_names]
        .groupby(by=[date_name, sec_name], group_keys=False)[old_names]
        .apply(lambda z: z - z.mean())
    )
    res_data = pd.merge(
        left=raw_data[[date_name, instru_name, sec_name]],
        right=neu_data,
        how="inner",
        left_index=True, right_index=True
    ).rename(columns=rename_mapper)

    # --- reformat
    res_data = res_data[[date_name, instru_name, sec_name] + new_names]
    return res_data


# ----------------------------------------
# ------ sqlite3 database structure ------
# ----------------------------------------

def gen_tst_ret_raw_db(instru: str, db_save_root_dir: str, save_id: str, rets: list[str]) -> CDbStruct:
    return CDbStruct(
        db_save_dir=os.path.join(db_save_root_dir, save_id),
        db_name=f"{instru}.db",
        table=CSqlTable(
            name="test_return",
            primary_keys=[CSqlVar("trade_date", "TEXT")],
            value_columns=[CSqlVar("ticker", "TEXT")] + [CSqlVar(ret, "REAL") for ret in rets],
        )
    )


def gen_tst_ret_neu_db(db_save_root_dir: str, save_id: str, rets: list[str]) -> CDbStruct:
    """

    :param db_save_root_dir:
    :param save_id: like "001L1NEU"
    :param rets: like ["Cls010L1NEU", "Opn010L1NEU"]
    :return:
    """

    return CDbStruct(
        db_save_dir=os.path.join(db_save_root_dir, save_id),
        db_name=f"{save_id}.db",
        table=CSqlTable(
            name="test_return",
            primary_keys=[CSqlVar("trade_date", "TEXT"), CSqlVar("instrument", "TEXT")],
            value_columns=[CSqlVar(ret, "REAL") for ret in rets],
        )
    )
