import argparse


def parse_args():
    arg_parser = argparse.ArgumentParser(description="To calculate data, such as macro and forex")
    arg_parser.add_argument("--bgn", type=str, help="begin date, format = [YYYYMMDD]", required=True)
    arg_parser.add_argument("--stp", type=str, help="stop  date, format = [YYYYMMDD]")
    arg_parser.add_argument("--nomp", default=False, action="store_true",
                            help="not using multiprocess, for debug. Works only when switch in (factor,)")
    arg_parser.add_argument("--processes", type=int, default=None,
                            help="number of processes to be called, effective only when nomp = False")
    arg_parser.add_argument("--verbose", default=False, action="store_true",
                            help="whether to print more details, effective only when sub function = (feature_selection,)")

    arg_parser_subs = arg_parser.add_subparsers(
        title="Position argument to call sub functions",
        dest="switch",
        description="use this position argument to call different functions of this project. "
                    "For example: 'python main.py --bgn 20120104 --stp 20240826 available'",
        required=True,
    )

    # switch: available
    arg_parser_subs.add_parser(name="available", help="Calculate available universe")

    # switch: market
    arg_parser_subs.add_parser(name="market", help="Calculate market universe")

    # switch: test return
    arg_parser_subs.add_parser(name="test_return", help="Calculate test returns")

    # switch: factor
    arg_parser_sub = arg_parser_subs.add_parser(name="factor", help="Calculate factor")
    arg_parser_sub.add_argument(
        "--fclass", type=str, help="factor class to run", required=True,
        choices=("MTM", "SKEW",
                 "RS", "BASIS", "TS",
                 "S0BETA", "S1BETA", "CBETA", "IBETA", "PBETA",
                 "CTP", "CTR", "CVP", "CVR", "CSP", "CSR",
                 "NOI", "NDOI", "WNOI", "WNDOI",
                 "AMP", "EXR", "SMT", "RWTC",
                 "TA",),
    )

    # switch: test return
    arg_parser_subs.add_parser(name="feature_selection", help="Select features")

    return arg_parser.parse_args()


if __name__ == "__main__":
    from project_config import proj_cfg, db_struct_cfg
    from husfort.qlog import define_logger
    from husfort.qcalendar import CCalendar

    define_logger()

    calendar = CCalendar(proj_cfg.calendar_path)
    args = parse_args()
    bgn_date, stp_date = args.bgn, args.stp or calendar.get_next_date(args.bgn, shift=1)

    if args.switch == "available":
        from solutions.available import main_available

        main_available(
            bgn_date=bgn_date, stp_date=stp_date,
            universe=proj_cfg.universe,
            cfg_avlb_unvrs=proj_cfg.avlb_unvrs,
            db_struct_preprocess=db_struct_cfg.preprocess,
            db_struct_avlb=db_struct_cfg.available,
            calendar=calendar,
        )
    elif args.switch == "market":
        from solutions.market import main_market

        main_market(
            bgn_date=bgn_date, stp_date=stp_date,
            calendar=calendar,
            db_struct_avlb=db_struct_cfg.available,
            db_struct_mkt=db_struct_cfg.market,
            path_mkt_idx_data=proj_cfg.market_index_path,
            mkt_idxes=list(proj_cfg.mkt_idxes.values()),
            sectors=proj_cfg.const.SECTORS,
        )
    elif args.switch == "test_return":
        from solutions.test_return import CTstRetRaw, CTstRetNeu

        for win in proj_cfg.test_rets_wins:
            # --- raw return
            tst_ret = CTstRetRaw(
                win=win, lag=proj_cfg.const.LAG,
                universe=proj_cfg.universe,
                db_tst_ret_save_dir=proj_cfg.test_return_dir,
                db_struct_preprocess=db_struct_cfg.preprocess,
            )
            tst_ret.main_test_return_raw(bgn_date, stp_date, calendar)

            # --- neutralization
            tst_ret_neu = CTstRetNeu(
                win=win, lag=proj_cfg.const.LAG,
                universe=proj_cfg.universe,
                db_tst_ret_save_dir=proj_cfg.test_return_dir,
                db_struct_avlb=db_struct_cfg.available,
            )
            tst_ret_neu.main_test_return_neu(
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
            )
    else:
        raise ValueError(f"args.switch = {args.switch} is illegal")
