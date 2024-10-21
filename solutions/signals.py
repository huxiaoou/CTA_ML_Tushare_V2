import pandas as pd
import multiprocessing as mp
from itertools import product
from rich.progress import Progress, track
from husfort.qutility import check_and_makedirs, error_handler
from husfort.qsqlite import CMgrSqlDb
from husfort.qcalendar import CCalendar
from solutions.shared import gen_sig_db, gen_fac_neu_db
from typedef import CFactor, TFactors, TFactorClass, TFactorName, TFactorNames


class _CSignal:
    def __init__(self, signal_save_dir: str, signal_id: str):
        self.signal_save_dir = signal_save_dir
        self.signal_id = signal_id

    def save(self, new_data: pd.DataFrame, calendar: CCalendar):
        db_struct_sig = gen_sig_db(self.signal_save_dir, self.signal_id)
        check_and_makedirs(db_struct_sig.db_save_dir)
        sqldb = CMgrSqlDb(
            db_save_dir=db_struct_sig.db_save_dir,
            db_name=db_struct_sig.db_name,
            table=db_struct_sig.table,
            mode="a",
        )
        if sqldb.check_continuity(new_data["trade_date"].iloc[0], calendar) == 0:
            sqldb.update(new_data[db_struct_sig.table.vars.names])
        return 0

    def read(self, bgn_date: str, stp_date: str) -> pd.DataFrame:
        db_struct_sig = gen_sig_db(self.signal_save_dir, self.signal_id)
        sqldb = CMgrSqlDb(
            db_save_dir=db_struct_sig.db_save_dir,
            db_name=db_struct_sig.db_name,
            table=db_struct_sig.table,
            mode="r",
        )
        data = sqldb.read_by_range(bgn_date, stp_date)
        return data

    def load_input(self, bgn_date: str, stp_date: str, calendar: CCalendar) -> pd.DataFrame:
        raise NotImplementedError

    def core(self, input_data: pd.DataFrame, bgn_date: str, stp_date: str, calendar: CCalendar) -> pd.DataFrame:
        raise NotImplementedError

    def main(self, bgn_date: str, stp_date: str, calendar: CCalendar):
        input_data = self.load_input(bgn_date, stp_date, calendar)
        new_data = self.core(input_data, bgn_date, stp_date, calendar)
        self.save(new_data=new_data, calendar=calendar)
        return 0

    @staticmethod
    def moving_average_signal(signal_data: pd.DataFrame, bgn_date: str, maw: int) -> pd.DataFrame:
        """

        :param signal_data: pd.Dataframe with columns = ["trade_date", "instrument", "weight"]
        :param bgn_date:
        :param maw:
        :return:
        """
        pivot_data = pd.pivot_table(
            data=signal_data,
            index=["trade_date"],
            columns=["instrument"],
            values=["weight"],
        )
        instru_ma_data = pivot_data.fillna(0).rolling(window=maw).mean()
        truncated_data = instru_ma_data.query(f"trade_date >= '{bgn_date}'")
        normalize_data = truncated_data.div(truncated_data.abs().sum(axis=1), axis=0).fillna(0)
        stack_data = normalize_data.stack(future_stack=True).reset_index()
        return stack_data[["trade_date", "instrument", "weight"]]


class CSignalFromFactorNeu(_CSignal):
    def __init__(self, factor: CFactor, factor_save_root_dir: str, signal_save_dir: str, maw: int):
        self.factor = factor
        self.factor_save_root_dir = factor_save_root_dir
        self.maw = maw
        signal_id = f"{factor.factor_name}.MA{maw:02d}"
        super().__init__(signal_save_dir=signal_save_dir, signal_id=signal_id)

    @property
    def factor_class(self) -> TFactorClass:
        return self.factor.factor_class

    @property
    def factor_name(self) -> TFactorName:
        return self.factor.factor_name

    @staticmethod
    def map_factor_to_signal(data: pd.DataFrame) -> pd.DataFrame:
        n = len(data)
        data["weight"] = [1] * int(n / 2) + [0] * (n % 2) + [-1] * int(n / 2)
        if (abs_sum := data["weight"].abs().sum()) > 0:
            data["weight"] = data["weight"] / abs_sum
        return data[["trade_date", "instrument", "weight"]]

    def load_input(self, bgn_date: str, stp_date: str, calendar: CCalendar) -> pd.DataFrame:
        base_bgn_date = calendar.get_next_date(bgn_date, -self.maw + 1)
        db_struct_fac = gen_fac_neu_db(
            db_save_root_dir=self.factor_save_root_dir,
            factor_class=self.factor_class,
            factor_names=TFactorNames([self.factor_name]),
        )
        sqldb = CMgrSqlDb(
            db_save_dir=db_struct_fac.db_save_dir,
            db_name=db_struct_fac.db_name,
            table=db_struct_fac.table,
            mode="r",
        )
        data = sqldb.read_by_range(
            bgn_date=base_bgn_date, stp_date=stp_date,
            value_columns=["trade_date", "instrument", self.factor_name],
        )
        return data

    def core(self, input_data: pd.DataFrame, bgn_date: str, stp_date: str, calendar: CCalendar) -> pd.DataFrame:
        sorted_data = input_data.sort_values(
            by=["trade_date", self.factor_name, "instrument"], ascending=[True, False, True]
        )
        grouped_data = sorted_data.groupby(by=["trade_date"], group_keys=False)
        signal_data = grouped_data.apply(self.map_factor_to_signal)
        signal_data_ma = self.moving_average_signal(signal_data, bgn_date=bgn_date, maw=self.maw)
        return signal_data_ma


def process_for_signal_from_factor_neu(
        factor: CFactor,
        factor_save_root_dir: str,
        maw: int,
        signal_save_dir: str,
        bgn_date: str,
        stp_date: str,
        calendar: CCalendar,
):
    signal = CSignalFromFactorNeu(
        factor, factor_save_root_dir=factor_save_root_dir, signal_save_dir=signal_save_dir, maw=maw,
    )
    signal.main(bgn_date, stp_date, calendar)
    return 0


def main_signals_from_factor_neu(
        factors: TFactors,
        factor_save_root_dir: str,
        maws: list[int],
        signal_save_dir: str,
        bgn_date: str,
        stp_date: str,
        calendar: CCalendar,
        call_multiprocess: bool,
        processes: int,
):
    desc = "Translating neutralized factors to signals"
    iter_args = product(factors, maws)
    if call_multiprocess:
        with Progress() as pb:
            main_task = pb.add_task(description=desc, total=len(factors))
            with mp.get_context("spawn").Pool(processes) as pool:
                for factor, maw in iter_args:
                    pool.apply_async(
                        process_for_signal_from_factor_neu,
                        kwds={
                            "factor": factor,
                            "factor_save_root_dir": factor_save_root_dir,
                            "maw": maw,
                            "signal_save_dir": signal_save_dir,
                            "bgn_date": bgn_date,
                            "stp_date": stp_date,
                            "calendar": calendar,
                        },
                        callback=lambda _: pb.update(main_task, advance=1),
                        error_callback=error_handler,
                    )
                pool.close()
                pool.join()
    else:
        for factor, maw in track(list(iter_args), description=desc):
            process_for_signal_from_factor_neu(
                factor=factor,
                factor_save_root_dir=factor_save_root_dir,
                maw=maw,
                signal_save_dir=signal_save_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
            )
    return 0
