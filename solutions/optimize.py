import numpy as np
import pandas as pd
from rich.progress import track
from husfort.qcalendar import CCalendar
from husfort.qsqlite import CMgrSqlDb
from husfort.qoptimization import COptimizerPortfolioSharpe
from husfort.qutility import check_and_makedirs
from solutions.shared import gen_opt_wgt_db, gen_nav_db
from typedef import CSimArgs, TSimGrpIdByFacGrp


class COptimizer:
    def __init__(self, x: pd.DataFrame, win: int, save_dir: str, save_id: str):
        """

        :param x: x is a nav dataFrame, with index = "trade_date",
                  columns = assets
        """
        self.x = x
        self.win = win
        self.save_dir = save_dir
        self.save_id = save_id

    def core(self, ret_data: pd.DataFrame) -> pd.Series:
        mu = ret_data.mean()
        cov = ret_data.cov()
        p = len(mu)
        bounds = [(-1.5 / p, 1.5 / p)] * p
        optimizer = COptimizerPortfolioSharpe(m=mu.values, v=cov.values, bounds=bounds)
        result = optimizer.optimize()
        if result.success:
            wgt = result.x
        else:
            wgt = np.ones(shape=p) / p
        return pd.Series(data=wgt, index=self.x.columns.tolist())

    def optimize_at_day(self, model_update_day: str, calendar: CCalendar) -> pd.Series:
        """

        :param model_update_day:
        :param calendar:
        :return: a series with index = self.x.columns, ie weights for each instrument
        """
        opt_b_date = calendar.get_next_date(model_update_day, shift=-self.win + 1)
        opt_e_date = model_update_day
        ret_data = self.x.truncate(before=opt_b_date, after=opt_e_date)
        return self.core(ret_data)

    @staticmethod
    def merge_to_header(opt_data: pd.DataFrame, calendar: CCalendar, bgn_date: str, stp_date: str) -> pd.DataFrame:
        header = calendar.get_dates_header(bgn_date, stp_date)
        new_data = pd.merge(
            left=header, right=opt_data,
            left_on="trade_date", right_index=True,
            how="left"
        ).ffill()
        return new_data

    def save(self, new_data: pd.DataFrame, calendar: CCalendar):
        db_struct_opt = gen_opt_wgt_db(
            db_save_dir=self.save_dir,
            save_id=self.save_id,
            underlying_assets_names=self.x.columns.tolist(),
        )
        sqldb = CMgrSqlDb(
            db_save_dir=db_struct_opt.db_save_dir,
            db_name=db_struct_opt.db_name,
            table=db_struct_opt.table,
            mode="a",
        )
        if sqldb.check_continuity(new_data["trade_date"].iloc[0], calendar) == 0:
            sqldb.update(update_data=new_data)
        return 0

    def main(self, bgn_date: str, stp_date: str, calendar: CCalendar):
        model_update_days = calendar.get_last_days_in_range(bgn_date=bgn_date, stp_date=stp_date)
        res: dict[str, pd.Series] = {}
        for model_update_day in model_update_days:
            next_day = calendar.get_next_date(model_update_day, shift=1)
            res[next_day] = self.optimize_at_day(model_update_day, calendar)
        optimized_wgt = pd.DataFrame.from_dict(res, orient="index")
        new_data = self.merge_to_header(optimized_wgt, calendar, bgn_date, stp_date)
        self.save(new_data, calendar)
        return 0


class COptimizerForMdlPrd(COptimizer):
    def __init__(
            self, group_id: TSimGrpIdByFacGrp, sim_args_list: list[CSimArgs], sim_save_dir: str,
            win: int, save_dir: str
    ):
        save_id = ".".join(group_id)
        x = self.__init_x(sim_args_list, sim_save_dir)
        super().__init__(x=x, win=win, save_dir=save_dir, save_id=save_id)

    @staticmethod
    def __init_x(sim_args_list: list[CSimArgs], sim_save_dir: str) -> pd.DataFrame:
        x_data = {}
        for sim_args in sim_args_list:
            db_struct_nav = gen_nav_db(db_save_dir=sim_save_dir, save_id=sim_args.sim_id)
            sqldb = CMgrSqlDb(
                db_save_dir=db_struct_nav.db_save_dir,
                db_name=db_struct_nav.db_name,
                table=db_struct_nav.table,
                mode="r"
            )
            nav_data = sqldb.read(value_columns=["trade_date", "net_ret"])
            unique_id, prd_ret, factor_group, trn_win, model, maw, tgt_ret = sim_args.sim_id.split(".")
            x_data[unique_id] = nav_data.set_index("trade_date")["net_ret"]
        return pd.DataFrame(x_data)


def main_optimize_mdl_prd(
        grouped_sim_args: dict[TSimGrpIdByFacGrp, list[CSimArgs]],
        sim_save_dir: str, win: int, save_dir: str,
        bgn_date: str, stp_date: str, calendar: CCalendar,
):
    check_and_makedirs(save_dir)
    for group_id, sim_args_list in track(grouped_sim_args.items(), description="Optimize for model prediction"):
        optimizer = COptimizerForMdlPrd(
            group_id=group_id,
            sim_args_list=sim_args_list,
            sim_save_dir=sim_save_dir,
            win=win,
            save_dir=save_dir,
        )
        optimizer.main(bgn_date, stp_date, calendar)
    return 0
