"""
Routes a user question to one or more specialist agents.
Uses Claude to classify the intent.
"""
from __future__ import annotations
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

AGENT_TYPES = [
    "performance",
    "creative",
    "funnel",
    "borrower_quality",
    "copy_gen",
    "platform_comparison",
    "chitchat",
]

_ROUTER_SYSTEM = """You are a routing agent for a performance marketing copilot for a digital personal loan app.
Your job is not to answer the question.
Your job is to classify the user query into exactly one route:
PERFORMANCE, CREATIVE, FUNNEL, BORROWER_QUALITY, COPY_GENERATION, MULTI, GENERAL.

Return structured JSON only:
{
  "route": "...",
  "reason": "...",
  "suggested_agents": ["<type1>", "<type2>"]
}

Valid agent types for suggested_agents: performance, creative, funnel, borrower_quality, copy_gen, platform_comparison, chitchat.

Use MULTI when the query requires more than one dimension, such as scale/pause decisions, campaign diagnosis, weekly planning, or borrower-quality recommendations.
For "which ads to scale/pause" → route: MULTI, suggested_agents: ["performance", "borrower_quality"]
For funnel questions → route: FUNNEL, suggested_agents: ["funnel"]
For creative effectiveness → route: CREATIVE, suggested_agents: ["creative", "borrower_quality"]
For copy generation → route: COPY_GENERATION, suggested_agents: ["copy_gen"]
For platform questions → route: PERFORMANCE, suggested_agents: ["platform_comparison"]
For casual conversation/greetings → route: GENERAL, suggested_agents: ["chitchat"]
"""


def route_query(question: str, llm: ChatOpenAI, history: list = None) -> dict:
    from langchain_core.messages import AIMessage
    messages = [SystemMessage(content=_ROUTER_SYSTEM)]
    if history:
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
    messages.append(HumanMessage(content=question))
    
    response = llm.invoke(messages)
    raw = response.content.strip()
    # extract JSON even if wrapped in markdown
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            result["suggested_agents"] = [a for a in result.get("suggested_agents", []) if a in AGENT_TYPES]
            if not result["suggested_agents"]:
                result["suggested_agents"] = ["performance"]
            if "route" not in result:
                result["route"] = "PERFORMANCE"
            if "reason" not in result:
                result["reason"] = ""
            return result
        except json.JSONDecodeError:
            pass
    return {"route": "PERFORMANCE", "suggested_agents": ["performance"], "reason": "fallback to performance"}
