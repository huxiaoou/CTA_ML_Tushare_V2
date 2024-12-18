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

    # switch: signals
    arg_parser_sub = arg_parser_subs.add_parser(name="signals", help="generate signals")
    arg_parser_sub.add_argument("--type", type=str, choices=("facNeu", "mdlPrd", "mdlOpt", "grpOpt"))

    # switch: simulations
    arg_parser_sub = arg_parser_subs.add_parser(name="simulations", help="simulate from signals")
    arg_parser_sub.add_argument("--type", type=str, choices=("facNeu", "mdlPrd", "mdlOpt", "grpOpt"))

    # switch: evaluations
    arg_parser_sub = arg_parser_subs.add_parser(name="evaluations", help="evaluate simulations")
    arg_parser_sub.add_argument("--type", type=str, choices=("facNeu", "mdlPrd", "mdlOpt", "grpOpt"))

    # switch: mclrn
    arg_parser_sub = arg_parser_subs.add_parser(name="mclrn", help="machine learning functions")
    arg_parser_sub.add_argument("--type", type=str, choices=("parse", "trnprd"))

    # switch: optimize
    arg_parser_sub = arg_parser_subs.add_parser(name="optimize", help="optimize portfolio and signals")
    arg_parser_sub.add_argument("--type", type=str, choices=("mdlPrd", "mdlOpt"))

    return arg_parser.parse_args()


if __name__ == "__main__":
    import os
    from project_config import proj_cfg, db_struct_cfg, cfg_factors
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
    elif args.switch == "factor":
        from project_config import cfg_factors

        fac, fclass = None, args.fclass
        if fclass == "MTM":
            from solutions.factorAlg import CFactorMTM

            if (cfg := cfg_factors.MTM) is not None:
                fac = CFactorMTM(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "SKEW":
            from solutions.factorAlg import CFactorSKEW

            if (cfg := cfg_factors.SKEW) is not None:
                fac = CFactorSKEW(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "RS":
            from solutions.factorAlg import CFactorRS

            if (cfg := cfg_factors.RS) is not None:
                fac = CFactorRS(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "BASIS":
            from solutions.factorAlg import CFactorBASIS

            if (cfg := cfg_factors.BASIS) is not None:
                fac = CFactorBASIS(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "TS":
            from solutions.factorAlg import CFactorTS

            if (cfg := cfg_factors.TS) is not None:
                fac = CFactorTS(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "S0BETA":
            from solutions.factorAlg import CFactorS0BETA

            if (cfg := cfg_factors.S0BETA) is not None:
                fac = CFactorS0BETA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_mkt=db_struct_cfg.market,
                )
        elif fclass == "S1BETA":
            from solutions.factorAlg import CFactorS1BETA

            if (cfg := cfg_factors.S1BETA) is not None:
                fac = CFactorS1BETA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_mkt=db_struct_cfg.market,
                )
        elif fclass == "CBETA":
            from solutions.factorAlg import CFactorCBETA

            if (cfg := cfg_factors.CBETA) is not None:
                fac = CFactorCBETA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_forex=db_struct_cfg.forex,
                )
        elif fclass == "IBETA":
            from solutions.factorAlg import CFactorIBETA

            if (cfg := cfg_factors.IBETA) is not None:
                fac = CFactorIBETA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_macro=db_struct_cfg.macro,
                )
        elif fclass == "PBETA":
            from solutions.factorAlg import CFactorPBETA

            if (cfg := cfg_factors.PBETA) is not None:
                fac = CFactorPBETA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_macro=db_struct_cfg.macro,
                )
        elif fclass == "CTP":
            from solutions.factorAlg import CFactorCTP

            if (cfg := cfg_factors.CTP) is not None:
                fac = CFactorCTP(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "CTR":
            from solutions.factorAlg import CFactorCTR

            if (cfg := cfg_factors.CTR) is not None:
                fac = CFactorCTR(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "CVP":
            from solutions.factorAlg import CFactorCVP

            if (cfg := cfg_factors.CVP) is not None:
                fac = CFactorCVP(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "CVR":
            from solutions.factorAlg import CFactorCVR

            if (cfg := cfg_factors.CVR) is not None:
                fac = CFactorCVR(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "CSP":
            from solutions.factorAlg import CFactorCSP

            if (cfg := cfg_factors.CSP) is not None:
                fac = CFactorCSP(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "CSR":
            from solutions.factorAlg import CFactorCSR

            if (cfg := cfg_factors.CSR) is not None:
                fac = CFactorCSR(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "NOI":
            from solutions.factorAlg import CFactorNOI

            if (cfg := cfg_factors.NOI) is not None:
                fac = CFactorNOI(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_pos=db_struct_cfg.position.copy_to_another(
                        another_db_save_dir=proj_cfg.by_instru_pos_dir),
                )
        elif fclass == "NDOI":
            from solutions.factorAlg import CFactorNDOI

            if (cfg := cfg_factors.NDOI) is not None:
                fac = CFactorNDOI(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_pos=db_struct_cfg.position.copy_to_another(
                        another_db_save_dir=proj_cfg.by_instru_pos_dir),
                )
        elif fclass == "WNOI":
            from solutions.factorAlg import CFactorWNOI

            if (cfg := cfg_factors.WNOI) is not None:
                fac = CFactorWNOI(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_pos=db_struct_cfg.position.copy_to_another(
                        another_db_save_dir=proj_cfg.by_instru_pos_dir),
                )
        elif fclass == "WNDOI":
            from solutions.factorAlg import CFactorWNDOI

            if (cfg := cfg_factors.WNDOI) is not None:
                fac = CFactorWNDOI(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_pos=db_struct_cfg.position.copy_to_another(
                        another_db_save_dir=proj_cfg.by_instru_pos_dir),
                )
        elif fclass == "AMP":
            from solutions.factorAlg import CFactorAMP

            if (cfg := cfg_factors.AMP) is not None:
                fac = CFactorAMP(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                )
        elif fclass == "EXR":
            from solutions.factorAlg import CFactorEXR

            if (cfg := cfg_factors.EXR) is not None:
                fac = CFactorEXR(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_minute_bar=db_struct_cfg.minute_bar,
                )
        elif fclass == "SMT":
            from solutions.factorAlg import CFactorSMT

            if (cfg := cfg_factors.SMT) is not None:
                fac = CFactorSMT(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_minute_bar=db_struct_cfg.minute_bar,
                )
        elif fclass == "RWTC":
            from solutions.factorAlg import CFactorRWTC

            if (cfg := cfg_factors.RWTC) is not None:
                fac = CFactorRWTC(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_minute_bar=db_struct_cfg.minute_bar,
                )
        elif fclass == "TA":
            from solutions.factorAlg import CFactorTA

            if (cfg := cfg_factors.TA) is not None:
                fac = CFactorTA(
                    cfg=cfg,
                    factors_by_instru_dir=proj_cfg.factors_by_instru_dir,
                    universe=proj_cfg.universe,
                    db_struct_preprocess=db_struct_cfg.preprocess,
                    db_struct_minute_bar=db_struct_cfg.minute_bar,
                )
        else:
            raise NotImplementedError(f"fclass = {args.fclass}")

        if fac is not None:
            from solutions.factor import CFactorNeu

            # --- raw factors
            fac.main_raw(
                bgn_date=bgn_date, stp_date=stp_date, calendar=calendar,
                call_multiprocess=not args.nomp, processes=args.processes,
            )

            # --- Neutralization
            neutralizer = CFactorNeu(
                ref_factor=fac,
                universe=proj_cfg.universe,
                db_struct_preprocess=db_struct_cfg.preprocess,
                db_struct_avlb=db_struct_cfg.available,
                neutral_by_instru_dir=proj_cfg.neutral_by_instru_dir,
            )
            neutralizer.main_neu(bgn_date=bgn_date, stp_date=stp_date, calendar=calendar)
    elif args.switch == "signals":
        if args.type == "facNeu":
            from solutions.signals import main_signals_from_factor_neu, main_signals_from_opt

            factors_neu = cfg_factors.get_factors_neu()
            main_signals_from_factor_neu(
                factors=factors_neu,
                factor_save_root_dir=proj_cfg.neutral_by_instru_dir,
                maws=proj_cfg.prd.wins,
                signal_save_dir=proj_cfg.sig_frm_fac_neu_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "mdlPrd":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests
            from solutions.signals import main_signals_from_mdl_prd

            factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)

            main_signals_from_mdl_prd(
                tests=test_mdls,
                mclrn_prd_dir=proj_cfg.mclrn_prd_dir,
                signal_save_dir=proj_cfg.sig_frm_mdl_prd_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "mdlOpt":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests, get_sim_args_mdl_prd, group_sim_args_by_factor_group
            from solutions.signals import main_signals_from_opt

            factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)
            sim_args_list = get_sim_args_mdl_prd(
                tests=test_mdls,
                signals_dir=proj_cfg.sig_frm_mdl_prd_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            grouped_sim_args = group_sim_args_by_factor_group(sim_args_list)
            main_signals_from_opt(
                grouped_sim_args=grouped_sim_args,
                input_sig_dir=proj_cfg.sig_frm_mdl_prd_dir,
                input_opt_dir=proj_cfg.opt_frm_mdl_prd_dir,
                signal_save_dir=proj_cfg.sig_frm_mdl_opt_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "grpOpt":
            from solutions.shared import get_sim_args_mdl_opt, group_sim_args_by_ret_prc
            from solutions.signals import main_signals_from_opt

            sim_args_list = get_sim_args_mdl_opt(
                factor_group_ids=list(proj_cfg.factor_groups),
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_mdl_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            grouped_sim_args = group_sim_args_by_ret_prc(sim_args_list)
            main_signals_from_opt(
                grouped_sim_args=grouped_sim_args,
                input_sig_dir=proj_cfg.sig_frm_mdl_opt_dir,
                input_opt_dir=proj_cfg.opt_frm_mdl_opt_dir,
                signal_save_dir=proj_cfg.sig_frm_grp_opt_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        else:
            raise ValueError(f"args.type == {args.type} is illegal")
    elif args.switch == "simulations":
        from solutions.simulations import main_simulations

        if args.type == "facNeu":
            from solutions.shared import get_sim_args_fac_neu

            sim_args_list = get_sim_args_fac_neu(
                factors=cfg_factors.get_factors_neu(),
                maws=proj_cfg.prd.wins,
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_fac_neu_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            main_simulations(
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_fac_neu_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "mdlPrd":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests, get_sim_args_mdl_prd

            factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)
            sim_args_list = get_sim_args_mdl_prd(
                tests=test_mdls,
                signals_dir=proj_cfg.sig_frm_mdl_prd_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            main_simulations(
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_mdl_prd_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "mdlOpt":
            from solutions.shared import get_sim_args_mdl_opt

            sim_args_list = get_sim_args_mdl_opt(
                factor_group_ids=list(proj_cfg.factor_groups),
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_mdl_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            main_simulations(
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_mdl_opt_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        elif args.type == "grpOpt":
            from solutions.shared import get_sim_args_grp_opt

            sim_args_list = get_sim_args_grp_opt(
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_grp_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST,
            )
            main_simulations(
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_grp_opt_dir,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
        else:
            raise ValueError(f"args.type == {args.type} is illegal")
    elif args.switch == "evaluations":
        from solutions.evaluations import main_evl_sims, main_plt_grouped_sim_args, plot_sim_args_list

        if args.type == "facNeu":
            from solutions.shared import get_sim_args_fac_neu, group_sim_args_by_factor_class

            sim_args_list = get_sim_args_fac_neu(
                factors=cfg_factors.get_factors_neu(),
                maws=proj_cfg.prd.wins,
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_fac_neu_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            main_evl_sims(
                sim_type=args.type,
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_fac_neu_dir,
                evl_save_dir=proj_cfg.evl_frm_fac_neu_dir,
                evl_save_file="evaluations_for_fac_neu.csv.gz",
                header_vars=["sharpe", "calmar", "sharpe+calmar"],
                sort_vars=["sharpe"],
                bgn_date=bgn_date,
                stp_date=stp_date,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
            # plot by group
            grouped_sim_args = group_sim_args_by_factor_class(sim_args_list, cfg_factors.get_mapper_name_to_class_neu())
            main_plt_grouped_sim_args(
                grouped_sim_args=grouped_sim_args,
                sim_save_dir=proj_cfg.sim_frm_fac_neu_dir,
                plt_save_dir=os.path.join(proj_cfg.evl_frm_fac_neu_dir, "plot-nav"),
                bgn_date=bgn_date,
                stp_date=stp_date,
            )
        elif args.type == "mdlPrd":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests, get_sim_args_mdl_prd, group_sim_args_by_factor_group

            factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)
            sim_args_list = get_sim_args_mdl_prd(
                tests=test_mdls,
                signals_dir=proj_cfg.sig_frm_mdl_prd_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB
            )
            main_evl_sims(
                sim_type=args.type,
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_mdl_prd_dir,
                evl_save_dir=proj_cfg.evl_frm_mdl_prd_dir,
                evl_save_file="evaluations_for_mdl_prd.csv.gz",
                header_vars=["sharpe+calmar", "sharpe", "calmar"],
                sort_vars=["sharpe+calmar"],
                bgn_date=bgn_date,
                stp_date=stp_date,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
            grouped_sim_args = group_sim_args_by_factor_group(sim_args_list)
            main_plt_grouped_sim_args(
                grouped_sim_args=grouped_sim_args,
                sim_save_dir=proj_cfg.sim_frm_mdl_prd_dir,
                plt_save_dir=os.path.join(proj_cfg.evl_frm_mdl_prd_dir, "plot-nav"),
                bgn_date=bgn_date, stp_date=stp_date,
            )
        elif args.type == "mdlOpt":
            from solutions.shared import get_sim_args_mdl_opt, group_sim_args_by_ret_prc

            sim_args_list = get_sim_args_mdl_opt(
                factor_group_ids=list(proj_cfg.factor_groups),
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_mdl_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            main_evl_sims(
                sim_type=args.type,
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_mdl_opt_dir,
                evl_save_dir=proj_cfg.evl_frm_mdl_opt_dir,
                evl_save_file="evaluations_for_mdl_opt.csv.gz",
                header_vars=["sharpe+calmar", "sharpe", "calmar"],
                sort_vars=["sharpe+calmar"],
                bgn_date=bgn_date,
                stp_date=stp_date,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
            grouped_sim_args = group_sim_args_by_ret_prc(sim_args_list)
            main_plt_grouped_sim_args(
                grouped_sim_args=grouped_sim_args,
                sim_save_dir=proj_cfg.sim_frm_mdl_opt_dir,
                plt_save_dir=os.path.join(proj_cfg.evl_frm_mdl_opt_dir, "plot-nav"),
                bgn_date=bgn_date, stp_date=stp_date,
            )
        elif args.type == "grpOpt":
            from solutions.shared import get_sim_args_grp_opt

            sim_args_list = get_sim_args_grp_opt(
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_grp_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST,
            )
            main_evl_sims(
                sim_type=args.type,
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_grp_opt_dir,
                evl_save_dir=proj_cfg.evl_frm_grp_opt_dir,
                evl_save_file="evaluations_for_grp_opt.csv.gz",
                header_vars=["sharpe+calmar", "sharpe", "calmar"],
                sort_vars=["sharpe+calmar"],
                bgn_date=bgn_date,
                stp_date=stp_date,
                call_multiprocess=not args.nomp,
                processes=args.processes,
            )
            plot_sim_args_list(
                fig_name="Cls.Opn",
                sim_args_list=sim_args_list,
                sim_save_dir=proj_cfg.sim_frm_grp_opt_dir,
                plt_save_dir=os.path.join(proj_cfg.evl_frm_grp_opt_dir, "plot-nav"),
                bgn_date=bgn_date, stp_date=stp_date,
            )
        else:
            raise ValueError(f"args.type == {args.type} is illegal")
    elif args.switch == "mclrn":
        factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
        if args.type == "parse":
            from solutions.mclrn_mdl_parser import parse_model_configs

            parse_model_configs(
                models=proj_cfg.mclrn,
                rets=proj_cfg.get_neu_test_rets_prd(),
                factor_groups=factor_groups,
                trn_wins=proj_cfg.trn.wins,
                cfg_mdl_dir=proj_cfg.mclrn_dir,
                cfg_mdl_file=proj_cfg.mclrn_cfg_file,
            )
        elif args.type == "trnprd":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests
            from solutions.mclrn_mdl_trn_prd import main_train_and_predict

            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)
            main_train_and_predict(
                tests=test_mdls,
                cv=proj_cfg.cv,
                factors_save_root_dir=proj_cfg.neutral_by_instru_dir,
                tst_ret_save_root_dir=proj_cfg.test_return_dir,
                db_struct_avlb=db_struct_cfg.available,
                mclrn_mdl_dir=proj_cfg.mclrn_mdl_dir,
                mclrn_prd_dir=proj_cfg.mclrn_prd_dir,
                universe=proj_cfg.universe,
                bgn_date=bgn_date,
                stp_date=stp_date,
                calendar=calendar,
                call_multiprocess=not args.nomp,
                processes=args.processes,
                verbose=args.verbose,
            )
        else:
            raise ValueError(f"args.type == {args.type} is illegal")
    elif args.switch == "optimize":
        from solutions.optimize import main_optimize

        if args.type == "mdlPrd":
            from solutions.mclrn_mdl_parser import load_config_models
            from solutions.shared import gen_model_tests, get_sim_args_mdl_prd, group_sim_args_by_factor_group

            factor_groups = cfg_factors.get_factor_groups(proj_cfg.factor_groups, "NEU")
            config_models = load_config_models(cfg_mdl_dir=proj_cfg.mclrn_dir, cfg_mdl_file=proj_cfg.mclrn_cfg_file)
            test_mdls = gen_model_tests(config_models=config_models, factor_groups=factor_groups)
            sim_args_list = get_sim_args_mdl_prd(
                tests=test_mdls,
                signals_dir=proj_cfg.sig_frm_mdl_prd_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB
            )
            grouped_sim_args = group_sim_args_by_factor_group(sim_args_list)
            main_optimize(
                grouped_sim_args=grouped_sim_args,
                sim_save_dir=proj_cfg.sim_frm_mdl_prd_dir,
                lbd=proj_cfg.optimize["lbd"],
                win=proj_cfg.optimize["win"],
                save_dir=proj_cfg.opt_frm_mdl_prd_dir,
                bgn_date=bgn_date, stp_date=stp_date, calendar=calendar,
            )
        elif args.type == "mdlOpt":
            from solutions.shared import get_sim_args_mdl_opt, group_sim_args_by_ret_prc

            sim_args_list = get_sim_args_mdl_opt(
                factor_group_ids=list(proj_cfg.factor_groups),
                rets=proj_cfg.get_raw_test_rets(),
                signals_dir=proj_cfg.sig_frm_mdl_opt_dir,
                ret_dir=proj_cfg.test_return_dir,
                cost=proj_cfg.const.COST_SUB,
            )
            grouped_sim_args = group_sim_args_by_ret_prc(sim_args_list)
            main_optimize(
                grouped_sim_args=grouped_sim_args,
                sim_save_dir=proj_cfg.sim_frm_mdl_opt_dir,
                lbd=proj_cfg.optimize["lbd"],
                win=proj_cfg.optimize["win"],
                save_dir=proj_cfg.opt_frm_mdl_opt_dir,
                bgn_date=bgn_date, stp_date=stp_date, calendar=calendar,
            )
        else:
            raise ValueError(f"args.type == {args.type} is illegal")
    else:
        raise ValueError(f"args.switch = {args.switch} is illegal")
