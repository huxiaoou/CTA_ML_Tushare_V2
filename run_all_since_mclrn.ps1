$bgn_date = "20120104"
$bgn_date_sig = "20170703" # signal bgn date
$bgn_date_sim = "20180102" # simulation bgn date
$stp_date = "20241008"

$bgn_date_ml = "20170201" # machine learning bgn date
$bgn_date_mdl_prd = "20170301"
$bgn_date_mdl_opt = "20170405"

# ------------------------
# --- remove existence ---
# ------------------------
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\mclrn
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sig_frm_mdl_prd
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sim_frm_mdl_prd
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\evl_frm_mdl_prd
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\opt_frm_mdl_prd
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sig_frm_mdl_opt
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sim_frm_mdl_opt
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\evl_frm_mdl_opt
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\opt_frm_mdl_opt
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sig_frm_grp_opt
remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\sim_frm_grp_opt
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\evl_frm_grp_opt


# --- machine learning
python main.py --bgn $bgn_date_ml --stp $stp_date mclrn --type parse
python main.py --bgn $bgn_date_ml --stp $stp_date --processes 12 mclrn --type trnprd

# --- calculate signals, simulations and optimization for each machine learning models
python main.py --bgn $bgn_date_mdl_prd --stp $stp_date signals --type mdlPrd
python main.py --bgn $bgn_date_mdl_prd --stp $stp_date simulations --type mdlPrd
python main.py --bgn $bgn_date_mdl_prd --stp $stp_date evaluations --type mdlPrd
python main.py --bgn $bgn_date_mdl_prd --stp $stp_date optimize --type mdlPrd # give weights for each (trn_win, prd_win)

# --- calculate signals, simulations and optimization for each factor group
python main.py --bgn $bgn_date_mdl_opt --stp $stp_date signals --type mdlOpt
python main.py --bgn $bgn_date_mdl_opt --stp $stp_date simulations --type mdlOpt
python main.py --bgn $bgn_date_mdl_opt --stp $stp_date evaluations --type mdlOpt
python main.py --bgn $bgn_date_mdl_opt --stp $stp_date optimize --type mdlOpt # give weights for each factor_group

# --- calculate signals, simulations and optimization for each price type
python main.py --bgn $bgn_date_sim --stp $stp_date signals --type grpOpt
python main.py --bgn $bgn_date_sim --stp $stp_date simulations --type grpOpt
python main.py --bgn $bgn_date_sim --stp $stp_date evaluations --type grpOpt
