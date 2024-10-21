import os
import multiprocessing as mp
import numpy as np
import pandas as pd
from rich.progress import track, Progress
from husfort.qutility import error_handler, check_and_makedirs, SFG
from husfort.qevaluation import CNAV
from husfort.qsqlite import CMgrSqlDb, CDbStruct
from husfort.qplot import CPlotLines
from solutions.shared import gen_nav_db
from typedef import CSimArgs, TSimGrpId


class CEvl:
    def __init__(self, db_struct_nav: CDbStruct):
        self.db_struct_nav = db_struct_nav
        self.indicators = ("hpr", "retMean", "retStd", "retAnnual", "volAnnual", "sharpe", "calmar", "mdd")

    def load(self, bgn_date: str, stp_date: str) -> pd.DataFrame:
        sqldb = CMgrSqlDb(
            db_save_dir=self.db_struct_nav.db_save_dir,
            db_name=self.db_struct_nav.db_name,
            table=self.db_struct_nav.table,
            mode="r"
        )
        nav_data = sqldb.read_by_range(bgn_date, stp_date)
        return nav_data

    def add_arguments(self, res: dict):
        raise NotImplementedError

    def get_ret(self, bgn_date: str, stp_date: str) -> pd.Series:
        """

        :param bgn_date:
        :param stp_date:
        :return: a pd.Series, with string index
        """
        nav_data = self.load(bgn_date, stp_date)
        ret_srs = nav_data.set_index("trade_date")["net_ret"]
        return ret_srs

    def main(self, bgn_date: str, stp_date: str) -> dict:
        ret_srs = self.get_ret(bgn_date, stp_date)
        nav = CNAV(ret_srs, input_type="RET")
        nav.cal_all_indicators()
        res = nav.to_dict()
        res = {k: res[k] for k in self.indicators}
        self.add_arguments(res)
        return res


class CEvlFacNeu(CEvl):
    def __init__(self, sim_args: CSimArgs, sim_frm_fac_neu_dir: str):
        self.sim_args = sim_args
        db_struct_nav = gen_nav_db(db_save_dir=sim_frm_fac_neu_dir, save_id=sim_args.sim_id)
        super().__init__(db_struct_nav)

    def add_arguments(self, res: dict):
        factor_name, maw, ret_name = self.sim_args.sim_id.split(".")
        other_arguments = {
            "factor_name": factor_name,
            "maw": maw,
            "ret_name": ret_name,
        }
        res.update(other_arguments)
        return 0


def process_for_evl_fac_neu(sim_args: CSimArgs, sim_frm_fac_neu_dir: str, bgn_date: str, stp_date: str) -> dict:
    s = CEvlFacNeu(sim_args, sim_frm_fac_neu_dir)
    return s.main(bgn_date, stp_date)


def main_evl_fac_neu(
        sim_args_list: list[CSimArgs],
        sim_frm_fac_neu_dir: str,
        evl_frm_fac_neu_dir: str,
        bgn_date: str,
        stp_date: str,
        call_multiprocess: bool,
        processes: int,
):
    desc = "Calculating evaluations for neutralized factors"
    evl_sims: list[dict] = []
    if call_multiprocess:
        with Progress() as pb:
            main_task = pb.add_task(description=desc, total=len(sim_args_list))
            with mp.get_context("spawn").Pool(processes=processes) as pool:
                jobs = []
                for sim_args in sim_args_list:
                    job = pool.apply_async(
                        process_for_evl_fac_neu,
                        args=(sim_args, sim_frm_fac_neu_dir, bgn_date, stp_date),
                        callback=lambda _: pb.update(main_task, advance=1),
                        error_callback=error_handler,
                    )
                    jobs.append(job)
                pool.close()
                pool.join()
            evl_sims = [job.get() for job in jobs]
    else:
        for sim_args in track(sim_args_list, description=desc):
            evl = process_for_evl_fac_neu(sim_args, sim_frm_fac_neu_dir, bgn_date, stp_date)
            evl_sims.append(evl)

    evl_data = pd.DataFrame(evl_sims)
    evl_data = evl_data.sort_values(by="sharpe", ascending=False)
    evl_data.insert(loc=0, column="calmar", value=evl_data.pop("calmar"))
    evl_data.insert(loc=0, column="sharpe", value=evl_data.pop("sharpe"))

    pd.set_option("display.max_rows", 40)
    pd.set_option("display.float_format", lambda z: f"{z:.3f}")
    print(evl_data)

    check_and_makedirs(evl_frm_fac_neu_dir)
    evl_file = "evaluations_for_neu_facs.csv.gz"
    evl_path = os.path.join(evl_frm_fac_neu_dir, evl_file)
    evl_data.to_csv(evl_path, float_format="%.6f", index=False)
    return 0


def plot_sim_args_list(
        grp_id: TSimGrpId,
        sim_args_list: list[CSimArgs],
        sim_frm_fac_neu_dir: str, evl_frm_fac_neu_dir: str,
        bgn_date: str, stp_date: str,
):
    ret_data_by_sim = {}
    for sim_args in sim_args_list:
        s = CEvlFacNeu(sim_args, sim_frm_fac_neu_dir)
        ret_data_by_sim[sim_args.sim_id] = s.get_ret(bgn_date, stp_date)
    ret_data = pd.DataFrame(ret_data_by_sim)
    nav_data = (1 + ret_data).cumprod()
    fig_name = f"{grp_id[0]}-{grp_id[1]}-{grp_id[2]}"
    artist = CPlotLines(
        plot_data=nav_data,
        fig_name=fig_name,
        fig_save_dir=evl_frm_fac_neu_dir,
        fig_save_type="jpg",
        colormap="jet",
    )
    artist.plot()
    artist.save_and_close()
    return 0


def main_plt_fac_neu(
        grouped_sim_args: dict[TSimGrpId, list[CSimArgs]],
        sim_frm_fac_neu_dir: str,
        evl_frm_fac_neu_dir: str,
        bgn_date: str,
        stp_date: str,
):
    for grp_id, sim_args_list in track(grouped_sim_args.items(), description="Plot by group id"):
        plot_sim_args_list(
            grp_id=grp_id,
            sim_args_list=sim_args_list,
            sim_frm_fac_neu_dir=sim_frm_fac_neu_dir,
            evl_frm_fac_neu_dir=evl_frm_fac_neu_dir,
            bgn_date=bgn_date,
            stp_date=stp_date,
        )
    return 0