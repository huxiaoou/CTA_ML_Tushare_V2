import yaml
import os
from itertools import product
from husfort.qutility import check_and_makedirs
from typedef import TRets, TFactorGroups


def parse_model_configs(
        models: dict,
        rets: TRets,  # 6
        factor_groups: TFactorGroups,  # 10
        trn_wins: list[int],  # 4
        cfg_mdl_dir: str,
        cfg_mdl_file: str,
):
    path_config_models = os.path.join(cfg_mdl_dir, cfg_mdl_file)
    m, iter_args = 0, {}
    for ret, fac_grp_id, trn_win in product(rets, factor_groups, trn_wins):
        for model_type, model_args in models.items():
            iter_args[f"M{m:04d}"] = {
                "ret_name": ret.ret_name,
                "fac_grp": fac_grp_id,
                "trn_win": trn_win,
                "model_type": model_type,
                "model_args": model_args,
            }
            m += 1
    check_and_makedirs(cfg_mdl_dir)
    with open(path_config_models, "w+") as f:
        yaml.dump_all([iter_args], f)
    return 0


def load_config_models(cfg_mdl_dir: str, cfg_mdl_file: str) -> dict[str, dict]:
    model_config_path = os.path.join(cfg_mdl_dir, cfg_mdl_file)
    with open(model_config_path, "r") as f:
        config_models = yaml.safe_load(f)
    return config_models
