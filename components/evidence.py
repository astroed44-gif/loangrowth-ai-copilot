"""
Evidence Panel: maps evidence_type to the appropriate chart/table renderer.
Called from app.py whenever st.session_state["evidence_type"] changes.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from components.charts import (
    funnel_chart,
    scatter_quality_chart,
    platform_comparison_chart,
    creative_quality_bar,
    ad_quality_table_chart,
)
from data.metrics import enrich_ad_quality_view, platform_summary


def render_evidence(evidence_type: str, evidence_data: dict, data: dict, filters: dict):
    st.markdown(
        '<div class="evidence-panel-title">'
        '<span class="dot"></span> Evidence Panel</div>',
        unsafe_allow_html=True,
    )

    if evidence_type == "funnel":
        _render_funnel(evidence_data, data, filters)
    elif evidence_type == "scatter":
        _render_scatter(data, filters)
    elif evidence_type == "platform":
        _render_platform(evidence_data, data, filters)
    elif evidence_type == "creative":
        _render_creative(evidence_data, data, filters)
    elif evidence_type == "copy_gen":
        _render_copy_gen(evidence_data)
    else:
        _render_ad_table(data, filters)


def _render_ad_table(data: dict, filters: dict):
    from data.loader import apply_filters
    df = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    fig = ad_quality_table_chart(df)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    # action summary badges
    if "recommended_action" in df.columns:
        counts = df["recommended_action"].value_counts().to_dict()
        cols = st.columns(len(counts))
        for i, (action, count) in enumerate(counts.items()):
            action_cls = action.replace(" ", "-") if action else "Unknown"
            cols[i].markdown(
                f'<div style="text-align:center">'
                f'<span class="action-badge action-{action_cls}">{action}</span>'
                f'<div style="font-size:18px;font-weight:700;color:#111827;margin-top:4px">{count}</div>'
                f'<div style="font-size:10px;color:#9CA3AF">ads</div></div>',
                unsafe_allow_html=True,
            )


def _render_funnel(evidence_data: dict, data: dict, filters: dict):
    from data.loader import apply_filters
    from data.metrics import funnel_stages
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    attribution = data["attribution"]
    onboarding = data["onboarding"]
    loan = data["loan_outcomes"]
    repayment = data["repayment"]

    # aggregate across all filtered ads
    all_user_ids = []
    for _, row in aq.iterrows():
        ad_id = row.get("ad_id")
        uids = attribution[attribution["ad_id"] == ad_id]["user_id"].tolist()
        all_user_ids.extend(uids)

    if not all_user_ids:
        st.info("No user data for current filter selection.")
        return

    stages = funnel_stages(all_user_ids, onboarding, loan, repayment)
    fig = funnel_chart(stages)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # drop-off table
    rows = []
    vals = list(stages.values())
    keys = list(stages.keys())
    for i in range(1, len(keys)):
        prev = vals[i - 1]
        curr = vals[i]
        drop = round((1 - curr / prev) * 100, 1) if prev > 0 else 0.0
        rows.append({"Stage": keys[i], "Users": curr, "Drop from prev": f"{drop}%"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_scatter(data: dict, filters: dict):
    from data.loader import apply_filters
    df = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    fig = scatter_quality_chart(df)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Bubble size = spend. Ideal ads: low CPI + high repayment rate (top-left quadrant).")


def _render_platform(evidence_data: dict, data: dict, filters: dict):
    from data.loader import apply_filters
    df = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    ps = platform_summary(df)
    fig = platform_comparison_chart(ps)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    # spend + installs summary
    if "spend" in ps.columns and "installs" in ps.columns:
        cols = st.columns(len(ps))
        for i, (_, row) in enumerate(ps.iterrows()):
            cols[i].metric(
                row["platform"],
                f"₹{float(row['spend']):,.0f} spend",
                f"{int(row['installs'])} installs",
            )


def _render_creative(evidence_data: dict, data: dict, filters: dict):
    from agents.tools import analyze_creative_patterns
    result = analyze_creative_patterns(data, filters)
    table = result.get("table")
    if table is not None and not table.empty:
        fig = creative_quality_bar(table)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        display = table.copy()
        for col in ["avg_quality", "avg_repayment", "avg_approval", "avg_kyc"]:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"{x:.3f}")
        if "total_spend" in display.columns:
            display["total_spend"] = display["total_spend"].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No creative data available for current filters.")


def _render_copy_gen(evidence_data: dict):
    winning = evidence_data.get("winning_creatives", [])
    copy_text = evidence_data.get("generated_copies", "")

    if winning:
        st.markdown('<p class="section-label-sm">Winning Creative Patterns</p>', unsafe_allow_html=True)
        df_win = pd.DataFrame(winning)
        display_cols = [c for c in ["creative_name", "copy_angle", "trust_level",
                                     "urgency_level", "repayment_rate", "creative_quality_score"]
                        if c in df_win.columns]
        if display_cols:
            for col in ["repayment_rate", "creative_quality_score"]:
                if col in df_win.columns:
                    df_win[col] = df_win[col].apply(lambda x: f"{float(x):.3f}" if x else "—")
            st.dataframe(df_win[display_cols], use_container_width=True, hide_index=True)

    if copy_text:
        st.markdown('<p class="section-label-sm" style="margin-top:12px">Generated Copy Variants</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;'
            f'padding:12px 14px;font-size:13px;line-height:1.8;color:#374151;'
            f'white-space:pre-wrap">{copy_text}</div>',
            unsafe_allow_html=True,
        )
