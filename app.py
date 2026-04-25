"""LoanGrowth AI Copilot — Flask web server.
Run: python3 app.py
"""
from __future__ import annotations
import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
_data_cache = None
_llm_cache = None


def _get_data() -> dict:
    global _data_cache
    if _data_cache is None:
        from data.loader import load_data
        _data_cache = load_data()
    return _data_cache


def _get_llm():
    global _llm_cache
    if _llm_cache is None:
        key = os.getenv("OPENAI_API_KEY", "")
        if key:
            from langchain_openai import ChatOpenAI
            _llm_cache = ChatOpenAI(model="gpt-4o", api_key=key, max_tokens=2048)
    return _llm_cache


def _pct(v) -> str:
    try:
        return f"{float(v) * 100:.1f}%"
    except Exception:
        return "—"


def _inr(v) -> str:
    try:
        return f"₹{float(v):,.0f}"
    except Exception:
        return "—"


def _compute_metrics(aq) -> dict:
    return {
        "total_spend":    _inr(aq["spend"].sum())                       if "spend"                  in aq.columns else "—",
        "total_installs": f"{int(aq['installs'].sum()):,}"              if "installs"               in aq.columns else "—",
        "avg_cpi":        _inr(aq["cpi"].mean())                        if "cpi"                    in aq.columns else "—",
        "avg_approval":   _pct(aq["approval_rate"].mean())              if "approval_rate"          in aq.columns else "—",
        "avg_repayment":  _pct(aq["repayment_rate"].mean())             if "repayment_rate"         in aq.columns else "—",
        "avg_quality":    f"{aq['creative_quality_score'].mean():.3f}"  if "creative_quality_score" in aq.columns else "—",
    }


def _compute_insights(aq) -> list:
    out = []
    try:
        if "platform" in aq.columns and "cpi" in aq.columns:
            p = aq.groupby("platform")["cpi"].mean().sort_values()
            if len(p) >= 2:
                ch, pr = p.index[0], p.index[1]
                diff = abs(p.iloc[1] - p.iloc[0]) / p.iloc[1] * 100
                out.append({"icon": "📈", "color": "green",
                            "text": f"<b>{ch} ads have {diff:.0f}% lower CPI</b> compared to {pr} this period"})
    except Exception:
        pass
    try:
        if "approval_rate" in aq.columns and "week" in aq.columns:
            bw = aq.groupby("week")["approval_rate"].mean().sort_index()
            if len(bw) >= 2:
                d = (bw.iloc[-1] - bw.iloc[0]) * 100
                sign = "dropped" if d < 0 else "improved"
                out.append({"icon": "⚠️" if d < 0 else "✅", "color": "yellow" if d < 0 else "green",
                            "text": f"Approval rate <b>{sign} {abs(d):.1f}%</b> in Week {bw.index[-1]} vs Week {bw.index[0]}"})
    except Exception:
        pass
    try:
        if "occupation" in aq.columns and "repayment_rate" in aq.columns:
            occ = aq.groupby("occupation")["repayment_rate"].mean()
            top, rate = occ.idxmax(), occ.max()
            out.append({"icon": "👥", "color": "blue",
                        "text": f"<b>{top}</b> show the highest repayment rate (<b>{rate * 100:.0f}%</b>)"})
    except Exception:
        pass
    return out


@app.route("/")
def index():
    from data.loader import get_filter_options
    from data.metrics import enrich_ad_quality_view
    data = _get_data()
    fo = get_filter_options(data)
    aq = enrich_ad_quality_view(data["ad_quality_view"])
    try:
        weeks = sorted(aq["week"].unique().tolist()) if "week" in aq.columns else []
        date_label = f"Weeks {weeks[0]}–{weeks[-1]}" if weeks else "Last 3 Weeks"
    except Exception:
        date_label = "Last 3 Weeks"
    return render_template(
        "index.html",
        filter_options=fo,
        metrics=_compute_metrics(aq),
        quick_insights=_compute_insights(aq),
        date_label=date_label,
    )


@app.route("/api/metrics", methods=["POST"])
def api_metrics():
    from data.loader import apply_filters
    from data.metrics import enrich_ad_quality_view
    data = _get_data()
    filters = (request.json or {}).get("filters", {})
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))
    return jsonify({"metrics": _compute_metrics(aq), "quick_insights": _compute_insights(aq)})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    from flask import Response
    import json
    from agents.router import route_query
    from agents.specialists import AGENT_DISPATCH
    from agents.supervisor import synthesize

    body = request.json or {}
    question = body.get("question", "")
    filters = body.get("filters", {})
    history = body.get("history", [])
    data, llm = _get_data(), _get_llm()

    if not llm:
        def err_gen():
            yield f"data: {json.dumps({'status': 'complete', 'result': {'decision': '⚠️ No OpenAI API key found. Add OPENAI_API_KEY to your Vercel Environment Variables and redeploy.', 'why': '', 'evidence': '', 'recommended_action': 'Investigate', 'action_items': ['Go to Vercel Dashboard', 'Add OPENAI_API_KEY in Settings > Environment Variables', 'Redeploy the project'], 'confidence': 0.0, 'evidence_type': 'ad_table', 'evidence_data': {}, 'agent_trace': []}})}\n\n"
        return Response(err_gen(), content_type='text/event-stream')

    def generate():
        try:
            yield f"data: {json.dumps({'status': 'progress', 'message': '🔀 Routing your question...'})}\n\n"
            route = route_query(question, llm, history)
            suggested = route.get("suggested_agents", ["performance"])
            
            outputs = []
            for agent_name in suggested:
                yield f"data: {json.dumps({'status': 'progress', 'message': f'⚙️ Running {agent_name}...'})}\n\n"
                fn = AGENT_DISPATCH.get(agent_name)
                if fn:
                    outputs.append(fn(data, filters, question, llm, history))

            yield f"data: {json.dumps({'status': 'progress', 'message': '✨ Synthesizing insights...'})}\n\n"
            answer = synthesize(outputs, question, llm, history)
            answer["route"] = route

            if answer.get("evidence_type") == "copy_gen" or "copy_gen" in suggested:
                answer["evidence_type"] = "copy_gen"
                for t in answer.get("agent_trace", []):
                    if t.get("agent") == "copy_gen_agent":
                        answer["evidence_data"] = {
                            "winning_creatives": t["data_summary"].get("winning_creatives", []),
                            "generated_copies": t.get("insight", ""),
                        }
                        break

            yield f"data: {json.dumps({'status': 'complete', 'result': answer})}\n\n"
        except Exception as e:
            app.logger.error("Chat error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), content_type='text/event-stream')


@app.route("/api/evidence", methods=["POST"])
def api_evidence():
    from data.loader import apply_filters
    from data.metrics import enrich_ad_quality_view, platform_summary
    body = request.json or {}
    ev_type = body.get("type", "ad_table")
    filters = body.get("filters", {})
    data = _get_data()
    aq = enrich_ad_quality_view(apply_filters(data["ad_quality_view"], filters))

    if ev_type == "platform":
        ps = platform_summary(aq)
        return jsonify(ps.round(3).to_dict(orient="records"))

    if ev_type == "funnel":
        from data.metrics import funnel_stages
        attr = data["attribution"]
        all_uids: list = []
        for _, row in aq.iterrows():
            ad_id = row.get("ad_id")
            uids = attr[attr["ad_id"] == ad_id]["user_id"].tolist()
            all_uids.extend(uids)
        stages = funnel_stages(all_uids, data["onboarding"], data["loan_outcomes"], data["repayment"])
        return jsonify(stages)

    if ev_type == "creative":
        from agents.tools import analyze_creative_patterns
        result = analyze_creative_patterns(data, filters)
        table = result.get("table")
        if table is not None and not table.empty:
            return jsonify(table.round(3).to_dict(orient="records"))
        return jsonify([])

    if ev_type == "scatter":
        cols = ["ad_name", "cpi", "repayment_rate", "spend", "platform"]
        avail = [c for c in cols if c in aq.columns]
        return jsonify(aq[avail].round(3).to_dict(orient="records"))

    # default: ad_table
    display_cols = ["ad_name", "platform", "copy_angle", "spend", "installs", "cpi",
                    "kyc_completion_rate", "approval_rate", "repayment_rate", "creative_quality_score"]
    avail = [c for c in display_cols if c in aq.columns]
    return jsonify(aq[avail].round(3).to_dict(orient="records"))


if __name__ == "__main__":
    print("\n🚀  LoanGrowth AI Copilot  →  http://localhost:5000\n")
    app.run(debug=True, port=5000, threaded=True)
