import pandas as pd
import multiprocessing as mp
from rich.progress import Progress, track
from husfort.qutility import check_and_makedirs, error_handler
from husfort.qsqlite import CMgrSqlDb
from husfort.qcalendar import CCalendar
from solutions.shared import gen_sig_db, gen_fac_neu_db
from typedef import TFactor, TFactors, TFactorClass, TFactorName, TSaveDir, TFactorNames


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

    def load_input(self, bgn_date: str, stp_date: str) -> pd.DataFrame:
        raise NotImplementedError

    def core(self, input_data: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def main(self, bgn_date: str, stp_date: str, calendar: CCalendar):
        input_data = self.load_input(bgn_date, stp_date)
        new_data = self.core(input_data)
        self.save(new_data=new_data, calendar=calendar)
        return 0


class CSignalFromFactorNeu(_CSignal):
    def __init__(self, factor: TFactor, **kwargs):
        self.factor = factor
        super().__init__(**kwargs)

    @property
    def factor_class(self) -> TFactorClass:
        return self.factor[0]

    @property
    def factor_name(self) -> TFactorName:
        return self.factor[1]

    @property
    def factor_save_root_dir(self) -> TSaveDir:
        return self.factor[2]

    def load_input(self, bgn_date: str, stp_date: str) -> pd.DataFrame:
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
            bgn_date, stp_date, value_columns=["trade_date", "instrument", self.factor_name]
        )
        return data

    @staticmethod
    def map_factor_to_signal(data: pd.DataFrame) -> pd.DataFrame:
        n = len(data)
        s = [1] * int(n / 2) + [0] * (n % 2) + [-1] * int(n / 2)
        data["weight"] = s
        if (abs_sum := data["weight"].abs().sum()) > 0:
            data["weight"] = data["weight"] / abs_sum
        return data[["trade_date", "instrument", "weight"]]

    def core(self, input_data: pd.DataFrame) -> pd.DataFrame:
        sorted_data = input_data.sort_values(
            by=["trade_date", self.factor_name, "instrument"], ascending=[True, False, True]
        )
        grouped_data = sorted_data.groupby(by=["trade_date"], group_keys=False)
        signal_data = grouped_data.apply(self.map_factor_to_signal)
        return signal_data


def process_for_signal_from_factor_neu(
        factor: TFactor,
        signal_save_dir: str,
        bgn_date: str,
        stp_date: str,
        calendar: CCalendar,
):
    signal = CSignalFromFactorNeu(factor, signal_save_dir=signal_save_dir, signal_id=factor[1])
    signal.main(bgn_date, stp_date, calendar)
    return 0


def main_signals_from_factor_neu(
        factors: TFactors,
        signal_save_dir: str,
        bgn_date: str,
        stp_date: str,
        calendar: CCalendar,
        call_multiprocess: bool,
        processes: int,
):
    desc = "Translating neutralized factors to signals"
    if call_multiprocess:
        with Progress() as pb:
            main_task = pb.add_task(description=desc, total=len(factors))
            with mp.get_context("spawn").Pool(processes) as pool:
                for factor in factors:
                    pool.apply_async(
                        process_for_signal_from_factor_neu,
                        kwds={
                            "factor": factor,
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
        for factor in track(factors, description=desc):
            process_for_signal_from_factor_neu(
                factor=factor,
                signal_save_dir=signal_save_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
            )
        return 0
