import pandas as pd
import os

XLSX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "loangrowth_ai_dummy_data_v2.xlsx")

_DATA_CACHE = None


def load_data() -> dict[str, pd.DataFrame]:
    global _DATA_CACHE
    if _DATA_CACHE is not None:
        return _DATA_CACHE
    xl = pd.ExcelFile(XLSX_PATH)
    sheets = {
        "ads_perf": xl.parse("Ads_Performance"),
        "creative_lib": xl.parse("Creative_Library"),
        "attribution": xl.parse("Attribution_Events"),
        "onboarding": xl.parse("App_Onboarding"),
        "loan_outcomes": xl.parse("Loan_Outcomes"),
        "repayment": xl.parse("Repayment_Quality"),
        "ad_quality_view": xl.parse("Ad_Quality_View"),
    }
    # normalise column names
    for key, df in sheets.items():
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        sheets[key] = df
    _DATA_CACHE = sheets
    return sheets


def get_filter_options(data: dict) -> dict:
    aq = data["ad_quality_view"]
    return {
        "platforms": sorted(aq["platform"].dropna().unique().tolist()),
        "campaigns": sorted(aq["campaign_name"].dropna().unique().tolist()),
        "adsets": sorted(aq["adset_name"].dropna().unique().tolist()),
        "copy_angles": sorted(aq["copy_angle"].dropna().unique().tolist()),
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df.copy()
    if filters.get("platforms"):
        out = out[out["platform"].isin(filters["platforms"])]
    if filters.get("campaigns"):
        out = out[out["campaign_name"].isin(filters["campaigns"])]
    if filters.get("adsets"):
        out = out[out["adset_name"].isin(filters["adsets"])]
    if filters.get("copy_angles"):
        out = out[out["copy_angle"].isin(filters["copy_angles"])]
    return out
