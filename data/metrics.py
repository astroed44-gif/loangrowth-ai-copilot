import pandas as pd
import numpy as np


def borrower_quality_score(row: pd.Series) -> float:
    kyc = row.get("kyc_completion_rate", 0) or 0
    approval = row.get("approval_rate", 0) or 0
    repayment = row.get("repayment_rate", 0) or 0
    profitability = row.get("avg_profitability_score", 0) or 0
    default = row.get("default_rate", 0) or 0
    profitability_norm = min(profitability / 10.0, 1.0)
    score = (
        0.25 * kyc
        + 0.25 * approval
        + 0.25 * repayment
        + 0.15 * profitability_norm
        - 0.10 * default
    )
    return round(max(0.0, min(1.0, score)), 3)


def enrich_ad_quality_view(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "creative_quality_score" not in df.columns:
        df["creative_quality_score"] = df.apply(borrower_quality_score, axis=1)
    else:
        # normalize from 0-100 scale to 0-1 if needed
        df["creative_quality_score"] = pd.to_numeric(df["creative_quality_score"], errors="coerce").fillna(0)
        if df["creative_quality_score"].max() > 1.0:
            df["creative_quality_score"] = df["creative_quality_score"] / 100.0
    # percentage columns for display
    for col in ["kyc_completion_rate", "application_rate", "approval_rate",
                "disbursal_rate", "repayment_rate", "default_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def funnel_stages(
    user_ids: list,
    onboarding_df: pd.DataFrame,
    loan_df: pd.DataFrame,
    repayment_df: pd.DataFrame,
) -> dict:
    ob = onboarding_df[onboarding_df["user_id"].isin(user_ids)]
    lo = loan_df[loan_df["user_id"].isin(user_ids)]
    rq = repayment_df[repayment_df["user_id"].isin(user_ids)]
    installs = len(user_ids)
    app_opened = int(ob["app_opened"].sum()) if "app_opened" in ob.columns else installs
    kyc_done = int(ob["kyc_completed"].sum()) if "kyc_completed" in ob.columns else 0
    applied = int(lo["loan_applied"].sum()) if "loan_applied" in lo.columns else 0
    approved = int(lo["loan_approved"].sum()) if "loan_approved" in lo.columns else 0
    disbursed = int(lo["loan_disbursed"].sum()) if "loan_disbursed" in lo.columns else 0
    repaid = int((rq["repayment_status"] == "Paid").sum()) if "repayment_status" in rq.columns else 0
    return {
        "Installs": installs,
        "App Opened": app_opened,
        "KYC Completed": kyc_done,
        "Applied": applied,
        "Approved": approved,
        "Disbursed": disbursed,
        "Repaid": repaid,
    }


def platform_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["platform", "spend", "installs", "cpi", "kyc_completion_rate",
            "approval_rate", "repayment_rate", "default_rate", "avg_profitability_score",
            "creative_quality_score"]
    available = [c for c in cols if c in df.columns]
    grp = df[available].groupby("platform")
    agg = {c: "mean" for c in available if c not in ("platform", "spend", "installs")}
    agg["spend"] = "sum"
    agg["installs"] = "sum"
    return grp.agg({k: v for k, v in agg.items() if k in available}).reset_index().round(3)


def top_ads_by_quality(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    score_col = "creative_quality_score" if "creative_quality_score" in df.columns else None
    if score_col is None:
        return df.head(n)
    return df.nlargest(n, score_col)


def ads_to_pause(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    score_col = "creative_quality_score" if "creative_quality_score" in df.columns else None
    if score_col is None:
        return df.head(n)
    return df.nsmallest(n, score_col)
