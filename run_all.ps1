$bgn_date = "20120104"
$bgn_date_ml = "20170201" # machine learning bgn date
$bgn_date_sig = "20170703" # signal bgn date
$bgn_date_sim = "20180102" # simulation bgn date
$stp_date = "20241008"

# ------------------------
# --- remove existence ---
# ------------------------
Remove-Item -Recurse E:\Data\Projects\CTA_ML_Tushare_V2\*

# ----------------------------
# --- exectue all projects ---
# ----------------------------

# --- prepare
python main.py --bgn $bgn_date --stp $stp_date available
python main.py --bgn $bgn_date --stp $stp_date market
python main.py --bgn $bgn_date --stp $stp_date test_return
