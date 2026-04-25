"""
Plotly chart builders for the Evidence Panel.
All charts use the warm-gray / indigo design system.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

_INDIGO = "#4F46E5"
_SCALE_COLOR = "#10B981"
_PAUSE_COLOR = "#EF4444"
_TEST_COLOR = "#F59E0B"
_INVESTIGATE_COLOR = "#4F46E5"
_MONITOR_COLOR = "#0EA5E9"

ACTION_COLOR_MAP = {
    "scale": _SCALE_COLOR,
    "pause": _PAUSE_COLOR,
    "test": _TEST_COLOR,
    "investigate": _INVESTIGATE_COLOR,
    "monitor": _MONITOR_COLOR,
    "needs more data": "#8B5CF6",
    "test variants": _TEST_COLOR,
}

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#374151"),
    margin=dict(l=12, r=12, t=36, b=12),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#E5E7EB",
        font=dict(size=12, family="Inter"),
    ),
)


def _action_color(action: str) -> str:
    if not action:
        return "#9CA3AF"
    return ACTION_COLOR_MAP.get(action.lower().strip(), "#9CA3AF")


def funnel_chart(funnel_data: dict) -> go.Figure:
    """
    funnel_data: {"Install": n, "App Opened": n, ...}
    """
    stages = list(funnel_data.keys())
    values = [int(v) for v in funnel_data.values()]
    colors = [_INDIGO] + [f"rgba(79,70,229,{0.85 - i*0.1})" for i in range(1, len(stages))]
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=colors, line=dict(width=0)),
        connector=dict(line=dict(color="#E5E7EB", width=1)),
        textfont=dict(size=12, family="Inter"),
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Funnel: Install → Repayment", font=dict(size=13, color="#111827"), x=0.01),
        height=340,
    )
    return fig


def scatter_quality_chart(df: pd.DataFrame) -> go.Figure:
    """
    X = CPI, Y = repayment_rate, bubble size = spend, color = recommended_action
    """
    df = df.copy()
    df["_color"] = df["recommended_action"].apply(_action_color)
    df["_size"] = (df["spend"].fillna(0) / df["spend"].max() * 40 + 8).clip(8, 48)
    df["_label"] = df["ad_name"].str.replace(r" Ad AD\d+", "", regex=True)

    fig = go.Figure()
    actions = df["recommended_action"].fillna("Unknown").unique()
    for action in actions:
        sub = df[df["recommended_action"].fillna("Unknown") == action]
        fig.add_trace(go.Scatter(
            x=sub["cpi"],
            y=sub["repayment_rate"],
            mode="markers+text",
            name=action,
            text=sub["_label"],
            textposition="top center",
            textfont=dict(size=9, color="#6B7280"),
            marker=dict(
                size=sub["_size"],
                color=sub["_color"],
                opacity=0.8,
                line=dict(width=1, color="white"),
            ),
            customdata=sub[["ad_name", "spend", "kyc_completion_rate",
                             "approval_rate", "creative_quality_score"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "CPI: ₹%{x:.0f}<br>"
                "Repayment: %{y:.1%}<br>"
                "Spend: ₹%{customdata[1]:,.0f}<br>"
                "KYC: %{customdata[2]:.1%}<br>"
                "Approval: %{customdata[3]:.1%}<br>"
                "Quality: %{customdata[4]:.3f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Spend vs Borrower Quality", font=dict(size=13, color="#111827"), x=0.01),
        xaxis=dict(
            title="CPI (₹)", gridcolor="#F3F4F6", linecolor="#E5E7EB",
            tickprefix="₹", zeroline=False,
        ),
        yaxis=dict(
            title="Repayment Rate", gridcolor="#F3F4F6", linecolor="#E5E7EB",
            tickformat=".0%", zeroline=False,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=11),
        ),
        height=360,
    )
    return fig


def platform_comparison_chart(platform_df: pd.DataFrame) -> go.Figure:
    """Side-by-side bar chart: Meta vs Google on key metrics."""
    metrics = ["kyc_completion_rate", "approval_rate", "repayment_rate", "default_rate"]
    labels = ["KYC %", "Approval %", "Repayment %", "Default %"]
    available = [m for m in metrics if m in platform_df.columns]
    labels = [labels[metrics.index(m)] for m in available]
    fig = go.Figure()
    colors = [_INDIGO, _SCALE_COLOR, _TEST_COLOR, _PAUSE_COLOR, _MONITOR_COLOR]
    for i, (col, label) in enumerate(zip(available, labels)):
        fig.add_trace(go.Bar(
            name=label,
            x=platform_df["platform"],
            y=platform_df[col],
            marker_color=colors[i % len(colors)],
            text=[f"{v:.0%}" for v in platform_df[col]],
            textposition="outside",
            textfont=dict(size=10),
        ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Meta vs Google: Borrower Quality", font=dict(size=13, color="#111827"), x=0.01),
        barmode="group",
        yaxis=dict(tickformat=".0%", gridcolor="#F3F4F6", zeroline=False),
        xaxis=dict(gridcolor="#F3F4F6"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        height=320,
    )
    return fig


def creative_quality_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: copy angle vs avg quality score."""
    cols = ["copy_angle", "avg_quality", "avg_repayment"]
    available = [c for c in cols if c in df.columns]
    if "copy_angle" not in available:
        # try to detect groupby result
        df = df.copy()
    df_sorted = df.sort_values("avg_quality" if "avg_quality" in df.columns else df.columns[1])
    y_col = "copy_angle" if "copy_angle" in df.columns else df.columns[0]
    x_col = "avg_quality" if "avg_quality" in df.columns else df.columns[1]
    fig = go.Figure(go.Bar(
        x=df_sorted[x_col],
        y=df_sorted[y_col],
        orientation="h",
        marker=dict(
            color=df_sorted[x_col],
            colorscale=[[0, "#FEE2E2"], [0.5, "#EDE9FE"], [1, "#4F46E5"]],
            showscale=False,
        ),
        text=[f"{v:.3f}" for v in df_sorted[x_col]],
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Copy Angle → Borrower Quality", font=dict(size=13, color="#111827"), x=0.01),
        xaxis=dict(title="Avg Quality Score", gridcolor="#F3F4F6", zeroline=False),
        yaxis=dict(title="", gridcolor="rgba(0,0,0,0)"),
        height=max(200, len(df_sorted) * 36 + 80),
    )
    return fig


def ad_quality_table_chart(df: pd.DataFrame) -> go.Figure:
    """Plotly table for ad quality scorecard (used inside evidence panel)."""
    display_cols = {
        "ad_name": "Ad",
        "platform": "Platform",
        "spend": "Spend",
        "cpi": "CPI",
        "kyc_completion_rate": "KYC%",
        "approval_rate": "Approv%",
        "repayment_rate": "Repay%",
        "default_rate": "Default%",
        "creative_quality_score": "Quality",
        "recommended_action": "Action",
    }
    available = {k: v for k, v in display_cols.items() if k in df.columns}
    sub = df[list(available.keys())].copy()
    for pct_col in ["kyc_completion_rate", "approval_rate", "repayment_rate", "default_rate"]:
        if pct_col in sub.columns:
            sub[pct_col] = sub[pct_col].apply(lambda x: f"{x*100:.0f}%")
    for money_col in ["spend", "cpi"]:
        if money_col in sub.columns:
            sub[money_col] = sub[money_col].apply(lambda x: f"₹{float(x):,.0f}")
    if "creative_quality_score" in sub.columns:
        sub["creative_quality_score"] = sub["creative_quality_score"].apply(lambda x: f"{float(x):.3f}")
    action_colors = []
    if "recommended_action" in sub.columns:
        for a in sub["recommended_action"]:
            c = _action_color(str(a) if a else "")
            action_colors.append(c)
    header_vals = list(available.values())
    cell_vals = [sub[k].tolist() for k in available.keys()]
    cell_fill = ["white"] * len(available)
    if "recommended_action" in available:
        idx = list(available.keys()).index("recommended_action")
        cell_fill[idx] = action_colors
    fig = go.Figure(go.Table(
        columnwidth=[180, 70, 70, 60, 55, 60, 60, 60, 60, 90],
        header=dict(
            values=[f"<b>{h}</b>" for h in header_vals],
            fill_color="#F9FAFB",
            align="left",
            font=dict(size=11, color="#374151"),
            line_color="#E5E7EB",
            height=32,
        ),
        cells=dict(
            values=cell_vals,
            fill_color=cell_fill,
            align="left",
            font=dict(size=11, color="#111827"),
            line_color="#F3F4F6",
            height=30,
        ),
    ))
    layout = dict(_LAYOUT_BASE)
    layout["margin"] = dict(l=0, r=0, t=36, b=0)
    fig.update_layout(
        **layout,
        title=dict(text="Ad Quality Scorecard", font=dict(size=13, color="#111827"), x=0.01),
        height=max(300, len(sub) * 32 + 80),
    )
    return fig
