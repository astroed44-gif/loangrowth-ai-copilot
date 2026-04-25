"""
Specialist agents — each wraps a tool call + LLM reasoning pass.
"""
from __future__ import annotations
import pandas as pd
from langchain_openai import ChatOpenAI


def _df_to_records(obj):
    """Convert a DataFrame to a list of dicts, or return obj unchanged."""
    if isinstance(obj, pd.DataFrame):
        return obj.round(3).to_dict(orient="records")
    return obj or []
from langchain_core.messages import SystemMessage, HumanMessage
from agents.tools import (
    analyze_ad_performance,
    analyze_funnel_dropoffs,
    analyze_creative_patterns,
    analyze_borrower_quality,
    compare_platforms,
    get_winning_creatives,
)

_CHITCHAT_SYS = """You are a friendly AI marketing assistant for a digital lending app in India.
The user said something conversational. Reply warmly in 1-2 sentences, remind them what you can help with
(ad performance, funnel analysis, creative strategy, borrower quality, copy generation), and invite a follow-up question.
Do NOT output JSON. Do NOT mention any ad names or specific data."""

_PERFORMANCE_SYS = """You are a performance marketing analyst for a digital lending app in India.
Given ad performance data, identify the top and bottom performing ads by quality score
(which factors in KYC completion, approval rate, repayment rate, and default rate — not just CPI).
Be concise. Focus on actionable insights. Use ₹ for currency."""

_CREATIVE_SYS = """You are a creative strategist for a digital lending app.
Given creative pattern data, identify which copy angles, hooks, and trust/urgency levels
correlate with high borrower quality (KYC completion + repayment rate).
Distinguish between creatives that get cheap installs vs those that get good borrowers."""

_FUNNEL_SYS = """You are a growth analyst specializing in mobile app funnels for lending apps.
Given funnel drop-off data, identify where users are dropping out most and what that implies
(clickbait = high CTR but low KYC; loan offer mismatch = high approval but low disbursal)."""

_BORROWER_QUALITY_SYS = """You are a credit risk and marketing analyst for a digital lending app.
Given borrower quality data (repayment, default, approval rates), identify which ads are attracting
genuinely creditworthy borrowers vs just cheap installs. Focus on profitability, not just volume."""

_COPY_GEN_SYS = """You are a performance marketing copywriter for a digital lending app in India.
Given the winning creative patterns (high borrower quality, high repayment), write 5 new ad copy variants.
Format: numbered list. Each variant: Hook | Body (1 line) | CTA. Keep under 30 words each."""

_PLATFORM_SYS = """You are a media buyer for a digital lending app running campaigns on Meta and Google.
Compare platform-level performance — not just CPI and spend, but downstream borrower quality.
Recommend budget allocation based on quality-adjusted CAC."""


def _filter_ctx(filters: dict) -> str:
    parts = []
    if filters.get("platforms"):    parts.append(f"Platform: {', '.join(filters['platforms'])}")
    if filters.get("copy_angles"):  parts.append(f"Copy Angle: {', '.join(filters['copy_angles'])}")
    if filters.get("campaigns"):    parts.append(f"Campaign: {', '.join(filters['campaigns'])}")
    if filters.get("adsets"):       parts.append(f"Adset: {', '.join(filters['adsets'])}")
    return ("Active filters: " + " | ".join(parts) + "\n\n") if parts else ""

def _build_messages(sys_prompt: str, question: str, history: list = None) -> list:
    from langchain_core.messages import AIMessage
    msgs = [SystemMessage(content=sys_prompt)]
    if history:
        for msg in history:
            if msg.get("role") == "user":
                msgs.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                msgs.append(AIMessage(content=msg.get("content", "")))
    msgs.append(HumanMessage(content=question))
    return msgs


def run_chitchat_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    response = llm.invoke(_build_messages(_CHITCHAT_SYS, question, history))
    return {
        "agent": "chitchat_agent",
        "insight": response.content,
        "data_summary": {},
        "tables_used": [],
        "tools_called": [],
    }


def run_performance_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    tool_result = analyze_ad_performance(data, filters)
    prompt = f"{_filter_ctx(filters)}User question: {question}\n\nData:\n{tool_result['summary']}"
    response = llm.invoke(_build_messages(_PERFORMANCE_SYS, prompt, history))
    return {
        "agent": "performance_agent",
        "insight": response.content,
        "data_summary": {"table": _df_to_records(tool_result.get("table"))},
        "tables_used": tool_result["tables_used"],
        "tools_called": [tool_result["tool"]],
    }


def run_creative_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    tool_result = analyze_creative_patterns(data, filters)
    prompt = f"{_filter_ctx(filters)}User question: {question}\n\nData:\n{tool_result['summary']}"
    response = llm.invoke(_build_messages(_CREATIVE_SYS, prompt, history))
    return {
        "agent": "creative_agent",
        "insight": response.content,
        "data_summary": {"table": _df_to_records(tool_result.get("table"))},
        "tables_used": tool_result["tables_used"],
        "tools_called": [tool_result["tool"]],
    }


def run_funnel_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    tool_result = analyze_funnel_dropoffs(data, filters)
    prompt = f"{_filter_ctx(filters)}User question: {question}\n\nData:\n{tool_result['summary']}"
    response = llm.invoke(_build_messages(_FUNNEL_SYS, prompt, history))
    return {
        "agent": "funnel_agent",
        "insight": response.content,
        "data_summary": {"funnel_data": tool_result.get("funnel_data", [])},
        "tables_used": tool_result["tables_used"],
        "tools_called": [tool_result["tool"]],
    }


def run_borrower_quality_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    tool_result = analyze_borrower_quality(data, filters)
    prompt = f"{_filter_ctx(filters)}User question: {question}\n\nData:\n{tool_result['summary']}"
    response = llm.invoke(_build_messages(_BORROWER_QUALITY_SYS, prompt, history))
    return {
        "agent": "borrower_quality_agent",
        "insight": response.content,
        "data_summary": {
            "scale_ads": tool_result.get("scale_ads", []),
            "pause_ads": tool_result.get("pause_ads", []),
        },
        "tables_used": tool_result["tables_used"],
        "tools_called": [tool_result["tool"]],
    }


def run_copy_gen_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    winners = get_winning_creatives(data, filters, top_n=3)
    import json
    context = json.dumps(winners, ensure_ascii=False, indent=2)
    prompt = (
        f"{_filter_ctx(filters)}User request: {question}\n\n"
        f"Top performing creatives (by borrower quality):\n{context}\n\n"
        "Generate 5 new ad copy variants inspired by these winning patterns."
    )
    response = llm.invoke(_build_messages(_COPY_GEN_SYS, prompt, history))
    return {
        "agent": "copy_gen_agent",
        "insight": response.content,
        "data_summary": {"winning_creatives": winners},
        "tables_used": ["ad_quality_view", "creative_library"],
        "tools_called": ["get_winning_creatives"],
    }


def run_platform_agent(data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> dict:
    tool_result = compare_platforms(data, filters)
    prompt = f"{_filter_ctx(filters)}User question: {question}\n\nData:\n{tool_result['summary']}"
    response = llm.invoke(_build_messages(_PLATFORM_SYS, prompt, history))
    return {
        "agent": "platform_comparison_agent",
        "insight": response.content,
        "data_summary": {"table": _df_to_records(tool_result.get("table"))},
        "tables_used": tool_result["tables_used"],
        "tools_called": [tool_result["tool"]],
    }


AGENT_DISPATCH = {
    "performance": run_performance_agent,
    "creative": run_creative_agent,
    "funnel": run_funnel_agent,
    "borrower_quality": run_borrower_quality_agent,
    "copy_gen": run_copy_gen_agent,
    "platform_comparison": run_platform_agent,
    "chitchat": run_chitchat_agent,
}


def run_agents(agent_names: list[str], data: dict, filters: dict, question: str, llm: ChatOpenAI, history: list = None) -> list[dict]:
    outputs = []
    for name in agent_names:
        fn = AGENT_DISPATCH.get(name)
        if fn:
            outputs.append(fn(data, filters, question, llm, history))
    return outputs
