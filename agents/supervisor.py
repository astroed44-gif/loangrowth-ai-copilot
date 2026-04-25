"""
Supervisor agent: synthesizes multi-agent outputs and generates the weekly briefing.
"""
from __future__ import annotations
import json
import re
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from data.metrics import top_ads_by_quality, ads_to_pause, enrich_ad_quality_view

_SYNTHESIZER_SYSTEM = """You are the head of performance marketing for a digital lending app in India.
You receive insights from multiple specialist agents and must synthesize them into a single clear answer.

Your response MUST be valid JSON in this exact shape:
{
  "decision": "<one bold sentence — the main answer>",
  "why": "<2-3 sentences explaining the reasoning>",
  "evidence": "<key data points that support this, with numbers. If the user asked for ad copies, include the actual generated ad copies here line by line>",
  "recommended_action": "<Scale | Pause | Test | Investigate>",
  "action_items": ["<specific action 1>", "<specific action 2>", "<specific action 3>"],
  "confidence": <float 0.0-1.0>,
  "evidence_type": "<ad_table | funnel | scatter | creative | copy_gen | platform>",
  "evidence_note": "<one sentence describing what the evidence panel should show>"
}

Be specific. Use ₹ for currency. Name actual ads when relevant.
CRITICAL RULE FOR COPIES: If the agent output contains generated ad copies, you MUST include the actual copy text in the `evidence` field or `decision` field so they are not lost. DO NOT summarize them away!
evidence_type mapping:
- performance/borrower_quality questions → "ad_table" or "scatter"
- funnel questions → "funnel"
- creative questions → "creative"
- copy_gen questions → "copy_gen"
- platform comparison → "platform"
"""

_BRIEFING_SYSTEM = """You are a weekly marketing analyst. Given ad quality data, produce a weekly briefing.
Respond ONLY with valid JSON:
{
  "scale_these": [{"ad_name": "...", "quality_score": 0.0, "copy_angle": "...", "reason": "..."}],
  "pause_these": [{"ad_name": "...", "quality_score": 0.0, "copy_angle": "...", "reason": "..."}],
  "funnel_alert": "<one sentence about the biggest funnel drop>",
  "test_next_week": "<one specific hypothesis to test next week>"
}
Scale: top 3 by quality score. Pause: bottom 3. Be specific and data-driven.
"""


def synthesize(agent_outputs: list[dict], question: str, llm: ChatOpenAI, history: list = None) -> dict:
    from langchain_core.messages import AIMessage
    if len(agent_outputs) == 1 and agent_outputs[0].get("agent") == "chitchat_agent":
        return {
            "decision": agent_outputs[0]["insight"],
            "why": "", "evidence": "",
            "recommended_action": "Chat",
            "action_items": [],
            "confidence": 1.0,
            "evidence_type": "ad_table",
            "evidence_data": {},
            "agent_trace": agent_outputs,
        }

    insights = "\n\n".join(
        f"[{o['agent']}]\n{o['insight']}" for o in agent_outputs
    )
    prompt = f"User question: {question}\n\nAgent insights:\n{insights}"

    messages = [SystemMessage(content=_SYNTHESIZER_SYSTEM)]
    if history:
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    raw = response.content.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            result["agent_trace"] = agent_outputs
            return result
        except json.JSONDecodeError:
            pass
    # fallback: return raw text wrapped in structure
    return {
        "decision": raw[:200],
        "why": "",
        "evidence": "",
        "recommended_action": "Investigate",
        "action_items": [],
        "confidence": 0.5,
        "evidence_type": "ad_table",
        "evidence_note": "See ad quality scorecard",
        "agent_trace": agent_outputs,
    }


def generate_weekly_briefing(_llm_placeholder: str, _data_hash: str, aq_json: str) -> dict:
    """
    Cached for 1 hour. _llm_placeholder and _data_hash are cache key helpers.
    aq_json is the serialized ad_quality_view DataFrame.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key, max_tokens=1024)

    aq_data = json.loads(aq_json)
    summary_lines = []
    for ad in aq_data[:24]:
        summary_lines.append(
            f"- {ad.get('ad_name', 'N/A')} | Quality: {ad.get('creative_quality_score', 'N/A')} "
            f"| Action: {ad.get('recommended_action', 'N/A')} "
            f"| Copy: {ad.get('copy_angle', 'N/A')} "
            f"| Repayment: {ad.get('repayment_rate', 'N/A')} "
            f"| Default: {ad.get('default_rate', 'N/A')}"
        )
    context = "\n".join(summary_lines)
    prompt = f"Weekly ad quality summary for {len(aq_data)} ads:\n{context}"
    response = llm.invoke([SystemMessage(content=_BRIEFING_SYSTEM), HumanMessage(content=prompt)])
    raw = response.content.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {
        "scale_these": [],
        "pause_these": [],
        "funnel_alert": "Unable to generate briefing.",
        "test_next_week": "—",
    }


def build_briefing_from_data(df: pd.DataFrame) -> dict:
    """Fast local fallback for weekly briefing when API is unavailable."""
    df = enrich_ad_quality_view(df)
    top3 = top_ads_by_quality(df, n=3)
    bot3 = ads_to_pause(df, n=3)
    scale = [
        {
            "ad_name": r["ad_name"],
            "quality_score": round(float(r["creative_quality_score"]), 3),
            "copy_angle": r.get("copy_angle", ""),
            "reason": f"Repayment {r.get('repayment_rate', 0)*100:.0f}%, Approval {r.get('approval_rate', 0)*100:.0f}%",
        }
        for _, r in top3.iterrows()
    ]
    pause = [
        {
            "ad_name": r["ad_name"],
            "quality_score": round(float(r["creative_quality_score"]), 3),
            "copy_angle": r.get("copy_angle", ""),
            "reason": f"Repayment {r.get('repayment_rate', 0)*100:.0f}%, Default {r.get('default_rate', 0)*100:.0f}%",
        }
        for _, r in bot3.iterrows()
    ]
    funnel_alert = "Check KYC drop-off on urgency-heavy creatives — high CTR ads may be attracting unqualified users."
    test = "Test a trust-led creative (testimonial + EMI planner) targeting salaried users aged 25-35 in Tier-1 cities."
    return {
        "scale_these": scale,
        "pause_these": pause,
        "funnel_alert": funnel_alert,
        "test_next_week": test,
    }
