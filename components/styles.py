"""Custom CSS for the LoanGrowth AI Copilot — clean SaaS design."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
.stApp { background: #F5F6FA !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* ── Top Navbar ─────────────────────────────────────── */
.top-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #FFFFFF;
    border-bottom: 1px solid #E9EAEC;
    padding: 0 20px;
    height: 58px;
    margin: -4rem -4rem 0 -4rem;
    padding-left: 24px;
    padding-right: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.navbar-left { display: flex; align-items: center; gap: 10px; }
.navbar-logo {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #4F46E5, #7C3AED);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
}
.navbar-title { font-size: 15px; font-weight: 700; color: #111827; letter-spacing: -0.2px; }
.navbar-badge {
    background: #EDE9FE; color: #4F46E5;
    font-size: 10px; font-weight: 700;
    padding: 2px 8px; border-radius: 100px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.navbar-right { display: flex; align-items: center; gap: 10px; }
.nav-icon-btn {
    width: 34px; height: 34px;
    border-radius: 9px;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 15px; position: relative;
}
.nav-notif-dot {
    position: absolute; top: 5px; right: 5px;
    width: 7px; height: 7px;
    background: #EF4444; border-radius: 50%;
    border: 2px solid white;
}
.nav-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 13px; font-weight: 600;
}

/* ── Sidebar ─────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E9EAEC !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] .stMarkdown p {
    color: #374151 !important; font-size: 13px !important;
}
.sidebar-filter-label {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600;
    color: #9CA3AF; text-transform: uppercase;
    letter-spacing: 0.6px; margin-bottom: 4px; margin-top: 6px;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #EDE9FE !important; color: #4F46E5 !important;
    border-radius: 6px !important; font-size: 11px !important;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span {
    color: #4F46E5 !important;
}
.sidebar-footer {
    font-size: 11px; color: #9CA3AF; line-height: 1.7; margin-top: 8px;
}
.sidebar-footer span { color: #4F46E5; font-weight: 600; }

/* ── Page Header ─────────────────────────────────────── */
.page-header-row {
    display: flex; align-items: flex-start;
    justify-content: space-between;
    padding: 20px 0 14px 0;
}
.page-header-left h2 {
    font-size: 21px; font-weight: 700; color: #111827;
    margin: 0 0 3px 0; letter-spacing: -0.3px;
}
.page-header-left p {
    font-size: 13px; color: #6B7280; margin: 0;
}
.date-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 9px; padding: 7px 13px;
    font-size: 12px; color: #374151; font-weight: 500;
    white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* ── Metric Cards ────────────────────────────────────── */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #F1F2F4;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    display: flex; align-items: flex-start; gap: 12px;
    height: 100%;
}
.metric-icon {
    width: 42px; height: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 19px; flex-shrink: 0;
}
.mi-purple { background: #EDE9FE; }
.mi-blue   { background: #DBEAFE; }
.mi-green  { background: #D1FAE5; }
.mi-yellow { background: #FEF3C7; }
.mi-pink   { background: #FCE7F3; }
.mi-violet { background: #F3E8FF; }
.metric-body { flex: 1; min-width: 0; }
.metric-label { font-size: 11px; font-weight: 500; color: #9CA3AF; margin-bottom: 4px; }
.metric-value {
    font-size: 20px; font-weight: 700; color: #111827;
    line-height: 1.1; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.metric-sub { font-size: 11px; color: #D1D5DB; margin-top: 3px; }

/* ── Chat container ──────────────────────────────────── */
.chat-box {
    background: #FFFFFF;
    border: 1px solid #F1F2F4;
    border-radius: 16px;
    padding: 24px 20px 16px 20px;
    min-height: 460px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── Welcome screen ──────────────────────────────────── */
.welcome-center {
    display: flex; flex-direction: column;
    align-items: center; text-align: center;
    padding: 16px 0 20px 0;
}
.robot-wrap {
    position: relative; display: inline-block;
    font-size: 76px; margin-bottom: 18px;
}
.speech-bubble {
    position: absolute; top: -6px; right: -38px;
    background: #4F46E5; color: white;
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 12px 12px 12px 4px;
    white-space: nowrap; box-shadow: 0 2px 6px rgba(79,70,229,0.35);
}
.welcome-title {
    font-size: 17px; font-weight: 700; color: #111827; margin-bottom: 6px;
}
.welcome-sub {
    font-size: 13px; color: #6B7280; line-height: 1.65;
    max-width: 360px; margin-bottom: 22px;
}

/* ── Suggested chips (2×2) ───────────────────────────── */
.chip-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; width: 100%; max-width: 500px;
    margin: 0 auto 4px auto;
}
.s-chip {
    background: #FAFAFA; border: 1px solid #E9EAEC;
    border-radius: 10px; padding: 10px 13px;
    font-size: 12px; font-weight: 500; color: #374151;
    display: flex; align-items: center; gap: 8px;
    cursor: pointer; transition: all 0.15s;
}
.s-chip:hover { background: #EEF2FF; border-color: #A5B4FC; color: #4F46E5; }
.s-chip-icon { font-size: 14px; }

/* Chat disclaimer */
.chat-disclaimer {
    text-align: center; font-size: 11px; color: #D1D5DB; margin-top: 8px;
}

/* ── Chat messages ───────────────────────────────────── */
.msg-user { display: flex; justify-content: flex-end; margin: 10px 0; }
.msg-user .bubble {
    background: #4F46E5; color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 15px; font-size: 13px;
    max-width: 80%; line-height: 1.55;
}
.msg-ai { display: flex; justify-content: flex-start; margin: 10px 0; gap: 8px; }
.msg-ai .avatar {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, #4F46E5, #7C3AED);
    border-radius: 50%; display: flex;
    align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; margin-top: 2px;
}
.msg-ai .bubble {
    background: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 4px 18px 18px 18px;
    padding: 14px 16px; font-size: 13px;
    max-width: 90%; line-height: 1.65;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── Answer card ─────────────────────────────────────── */
.answer-card { font-size: 13px; line-height: 1.7; }
.answer-card .section-header {
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.8px;
    color: #9CA3AF; margin: 10px 0 4px 0;
}
.answer-card .decision-text {
    font-size: 14px; font-weight: 600;
    color: #111827; line-height: 1.4;
}
.answer-card .divider {
    border: none; border-top: 1px solid #F3F4F6; margin: 8px 0;
}
.confidence-bar-bg {
    height: 6px; background: #F3F4F6; border-radius: 3px;
    overflow: hidden; width: 120px;
    display: inline-block; vertical-align: middle;
}
.confidence-bar-fill {
    height: 6px;
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    border-radius: 3px;
}

/* ── Action badges ───────────────────────────────────── */
.action-badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 100px; font-size: 11px;
    font-weight: 600; text-transform: uppercase;
}
.action-Scale       { background: #D1FAE5; color: #065F46; }
.action-Pause       { background: #FEE2E2; color: #991B1B; }
.action-Test        { background: #FEF3C7; color: #92400E; }
.action-Investigate { background: #EDE9FE; color: #3730A3; }
.action-Monitor     { background: #E0F2FE; color: #075985; }

/* ── Right panel: Help card ──────────────────────────── */
.help-card {
    background: linear-gradient(145deg, #EEF2FF 0%, #F5F3FF 100%);
    border: 1px solid #E0E7FF;
    border-radius: 16px; padding: 20px;
    margin-bottom: 14px; position: relative; overflow: hidden;
}
.help-card-title {
    font-size: 13px; font-weight: 700; color: #1E1B4B;
    margin-bottom: 14px;
}
.help-item {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: #374151; font-weight: 500;
    margin-bottom: 9px;
}
.help-check {
    width: 18px; height: 18px;
    background: #4F46E5; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 9px; flex-shrink: 0;
}
.help-robot {
    position: absolute; right: 10px; bottom: 8px;
    font-size: 58px; opacity: 0.85;
}

/* ── Right panel: Quick Insights ────────────────────── */
.insights-card {
    background: #FFFFFF;
    border: 1px solid #F1F2F4;
    border-radius: 16px; padding: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.insights-header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 14px;
}
.insights-title {
    font-size: 13px; font-weight: 700; color: #111827;
    display: flex; align-items: center; gap: 6px;
}
.insight-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 0; border-bottom: 1px solid #F9FAFB;
}
.insight-item:last-child { border-bottom: none; }
.insight-icon {
    width: 32px; height: 32px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}
.ii-green  { background: #D1FAE5; }
.ii-yellow { background: #FEF3C7; }
.ii-blue   { background: #DBEAFE; }
.insight-text { font-size: 12px; color: #374151; line-height: 1.55; }
.insight-text strong { color: #111827; }

/* ── Evidence panel ──────────────────────────────────── */
.evidence-panel {
    background: #FFFFFF; border: 1px solid #F1F2F4;
    border-radius: 16px; padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.evidence-panel-title {
    font-size: 11px; font-weight: 600; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 6px;
}
.evidence-panel-title .dot {
    width: 6px; height: 6px;
    background: #4F46E5; border-radius: 50%;
    display: inline-block;
}

/* ── Briefing items ──────────────────────────────────── */
.briefing-item {
    font-size: 12px; color: #111827;
    padding: 4px 0; border-bottom: 1px solid #F3F4F6;
    display: flex; justify-content: space-between;
    align-items: center; gap: 8px;
}
.briefing-item:last-child { border-bottom: none; }
.briefing-item .ad-name { font-weight: 500; flex: 1; }
.briefing-item .score { font-size: 11px; font-weight: 600; color: #4F46E5; white-space: nowrap; }
.section-label-sm {
    font-size: 11px; font-weight: 600; color: #9CA3AF;
    text-transform: uppercase; letter-spacing: 0.8px; margin: 0 0 6px 0;
}

/* ── Trace badges ────────────────────────────────────── */
.trace-agent-badge {
    display: inline-block; background: #EDE9FE; color: #3730A3;
    border-radius: 4px; padding: 1px 6px;
    font-size: 11px; font-weight: 500; margin: 2px;
}
.trace-tool-badge {
    display: inline-block; background: #E0F2FE; color: #075985;
    border-radius: 4px; padding: 1px 6px;
    font-size: 11px; font-weight: 500; margin: 2px;
}

/* ── Misc ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 2px; }
.stButton > button { border-radius: 8px !important; font-size: 12px !important; font-weight: 500 !important; }
.stDataFrame { border-radius: 8px; overflow: hidden; }
.streamlit-expanderHeader { font-size: 12px !important; color: #6B7280 !important; }
.stSelectbox label, .stMultiSelect label { font-size: 11px !important; color: #9CA3AF !important; font-weight: 600 !important; }
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
