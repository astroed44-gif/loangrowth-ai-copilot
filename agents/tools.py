"""
Pandas-backed tool functions for LangChain agents.
Each tool receives a filters dict and returns a human-readable string summary
that the LLM can reason over.
"""
from __future__ import annotations

import json
import pandas as pd
from data.metrics import (
    funnel_stages, platform_summary, top_ads_by_quality, ads_to_pause, enrich_ad_quality_view
)


def _fmt_pct(v) -> str:
    try:
        return f"{float(v)*100:.1f}%"
    except Exception:
        return str(v)


def _fmt_inr(v) -> str:
    try:
        return f"₹{float(v):,.0f}"
    except Exception:
        return str(v)


def analyze_ad_performance(data: dict, filters: dict) -> dict:
    from data.loader import apply_filters
    df = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    ranked = df.sort_values("creative_quality_score", ascending=False)[
        ["ad_name", "platform", "spend", "installs", "cpi",
         "kyc_completion_rate", "approval_rate", "repayment_rate",
         "default_rate", "creative_quality_score", "recommended_action"]
    ].head(10)
    rows = []
    for _, r in ranked.iterrows():
        rows.append({
            "ad": r["ad_name"],
            "platform": r["platform"],
            "spend": _fmt_inr(r["spend"]),
            "cpi": _fmt_inr(r["cpi"]),
            "kyc": _fmt_pct(r["kyc_completion_rate"]),
            "approval": _fmt_pct(r["approval_rate"]),
            "repayment": _fmt_pct(r["repayment_rate"]),
            "quality_score": round(float(r["creative_quality_score"]), 3),
            "action": r.get("recommended_action", "—"),
        })
    total_spend = _fmt_inr(df["spend"].sum())
    avg_cpi = _fmt_inr(df["cpi"].mean())
    avg_quality = round(float(df["creative_quality_score"].mean()), 3)
    summary = (
        f"Analyzed {len(df)} ads. Total spend: {total_spend}. "
        f"Avg CPI: {avg_cpi}. Avg quality score: {avg_quality}.\n"
        f"Top ads by quality:\n{json.dumps(rows, ensure_ascii=False, indent=2)}"
    )
    return {
        "summary": summary,
        "table": ranked.reset_index(drop=True),
        "tables_used": ["ad_quality_view"],
        "tool": "analyze_ad_performance",
    }


def analyze_funnel_dropoffs(data: dict, filters: dict) -> dict:
    from data.loader import apply_filters
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    attribution = data["attribution"]
    onboarding = data["onboarding"]
    loan = data["loan_outcomes"]
    repayment = data["repayment"]

    results = []
    for _, row in aq.iterrows():
        ad_id = row.get("ad_id")
        user_ids = attribution[attribution["ad_id"] == ad_id]["user_id"].tolist()
        if not user_ids:
            continue
        stages = funnel_stages(user_ids, onboarding, loan, repayment)
        installs = stages["Installs"]
        drops = {}
        prev = installs
        for stage, count in list(stages.items())[1:]:
            pct = round((1 - count / prev) * 100, 1) if prev > 0 else 0
            drops[stage] = {"count": count, "drop_from_prev_%": pct}
            prev = count
        results.append({
            "ad": row.get("ad_name", ad_id),
            "platform": row.get("platform", ""),
            "installs": installs,
            "funnel": drops,
        })

    worst_drop_stage = "KYC Completed"
    insights = []
    for r in results:
        kyc_drop = r["funnel"].get("KYC Completed", {}).get("drop_from_prev_%", 0)
        if kyc_drop > 40:
            insights.append(f"  • {r['ad']}: {kyc_drop}% KYC drop (clickbait risk)")
    summary = (
        f"Funnel analysis across {len(results)} ads.\n"
        + (("\n".join(insights) + "\n") if insights else "No major drop anomalies detected.\n")
        + f"Full funnel data:\n{json.dumps(results[:6], indent=2)}"
    )
    return {
        "summary": summary,
        "funnel_data": results,
        "tables_used": ["attribution", "app_onboarding", "loan_outcomes", "repayment_quality"],
        "tool": "analyze_funnel_dropoffs",
    }


def analyze_creative_patterns(data: dict, filters: dict) -> dict:
    from data.loader import apply_filters
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    cl = data["creative_lib"]
    merged = aq.merge(
        cl[["creative_id", "hook", "target_persona"]].rename(columns={"creative_id": "creative_id_cl"}),
        left_on="creative_id", right_on="creative_id_cl", how="left"
    )
    angle_stats = (
        merged.groupby("copy_angle")
        .agg(
            ads=("ad_id", "count"),
            avg_quality=("creative_quality_score", "mean"),
            avg_repayment=("repayment_rate", "mean"),
            avg_approval=("approval_rate", "mean"),
            avg_kyc=("kyc_completion_rate", "mean"),
            total_spend=("spend", "sum"),
        )
        .round(3)
        .reset_index()
        .sort_values("avg_quality", ascending=False)
    )
    rows = angle_stats.to_dict(orient="records")
    summary = (
        f"Creative pattern analysis across {len(aq)} ads, {len(angle_stats)} copy angles.\n"
        f"Best performing angle by quality: {rows[0]['copy_angle']} "
        f"(score {rows[0]['avg_quality']}, repayment {_fmt_pct(rows[0]['avg_repayment'])})\n"
        f"Worst performing: {rows[-1]['copy_angle']} "
        f"(score {rows[-1]['avg_quality']}, repayment {_fmt_pct(rows[-1]['avg_repayment'])})\n"
        f"Full breakdown:\n{json.dumps(rows, ensure_ascii=False, indent=2)}"
    )
    return {
        "summary": summary,
        "table": angle_stats,
        "tables_used": ["ad_quality_view", "creative_library"],
        "tool": "analyze_creative_patterns",
    }


def analyze_borrower_quality(data: dict, filters: dict) -> dict:
    from data.loader import apply_filters
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    scale = aq[aq["recommended_action"].str.lower().str.contains("scale", na=False)]
    pause = aq[aq["recommended_action"].str.lower().str.contains("pause", na=False)]
    high_default = aq[aq["default_rate"] > 0.1].sort_values("default_rate", ascending=False)
    top_repayment = aq.nlargest(3, "repayment_rate")[["ad_name", "repayment_rate", "default_rate", "creative_quality_score"]]
    rows = top_repayment.to_dict(orient="records")
    summary = (
        f"Borrower quality across {len(aq)} ads.\n"
        f"Scale candidates: {len(scale)} ads. Pause candidates: {len(pause)} ads.\n"
        f"High default (>10%) ads: {len(high_default)}.\n"
        f"Top 3 by repayment rate:\n{json.dumps(rows, ensure_ascii=False, indent=2)}\n"
        f"Avg repayment rate: {_fmt_pct(aq['repayment_rate'].mean())}\n"
        f"Avg default rate: {_fmt_pct(aq['default_rate'].mean())}"
    )
    return {
        "summary": summary,
        "scale_ads": scale[["ad_name", "creative_quality_score", "repayment_rate"]].to_dict(orient="records"),
        "pause_ads": pause[["ad_name", "creative_quality_score", "repayment_rate"]].to_dict(orient="records"),
        "tables_used": ["ad_quality_view"],
        "tool": "analyze_borrower_quality",
    }


def compare_platforms(data: dict, filters: dict) -> dict:
    from data.loader import apply_filters
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    ps = platform_summary(aq)
    rows = ps.to_dict(orient="records")
    summary = (
        f"Platform comparison (Meta vs Google):\n"
        f"{json.dumps(rows, ensure_ascii=False, indent=2)}"
    )
    return {
        "summary": summary,
        "table": ps,
        "tables_used": ["ad_quality_view"],
        "tool": "compare_platforms",
    }


def get_winning_creatives(data: dict, filters: dict, top_n: int = 3) -> list[dict]:
    from data.loader import apply_filters
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    top = top_ads_by_quality(aq, n=top_n)
    return top[["creative_id", "creative_name", "copy_angle", "trust_level",
                "urgency_level", "repayment_rate", "creative_quality_score"]].to_dict(orient="records")
