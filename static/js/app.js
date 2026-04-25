/* ═══════════════════════════════════════════════════════
   LoanGrowth AI Copilot — Frontend App
   ═══════════════════════════════════════════════════════ */

'use strict';

// ── State ──────────────────────────────────────────────
const state = {
  filters: {
    platforms: [],
    campaigns: [],
    adsets: [],
    copy_angles: [],
    weeks: [],
    occupations: [],
    loan_purposes: [],
    risk_bands: [],
  },
  messages: [],
  isLoading: false,
  hasMessages: false,
};

// ── Filter definitions ─────────────────────────────────
const FILTER_DEFS = [
  { key: 'platforms',     optKey: 'platforms',     label: 'All Platforms', defaultAll: true },
  { key: 'campaigns',     optKey: 'campaigns',     label: 'All Campaigns' },
  { key: 'adsets',        optKey: 'adsets',        label: 'All Adsets' },
  { key: 'copy_angles',   optKey: 'copy_angles',   label: 'All Copy Angles' },
];

// ═══════════════════════════════════════════════════════
//  CUSTOM MULTI-SELECT  (FS = FilterSelect)
// ═══════════════════════════════════════════════════════
const FS = (() => {
  const _states = {}; // key → { selected: Set, options: [], def }

  function init(def, options) {
    const { key, label, defaultAll } = def;
    _states[key] = {
      selected: new Set(defaultAll ? options : []),
      options,
      label,
    };

    // Build dropdown options
    const dd = document.getElementById(`dd-${key}`);
    if (!dd) return;
    dd.innerHTML = options.map(opt => `
      <div class="fs-option${defaultAll ? ' selected' : ''}" data-value="${escHtml(opt)}" data-key="${key}">
        ${escHtml(opt)}
      </div>
    `).join('');

    dd.querySelectorAll('.fs-option').forEach(el => {
      el.addEventListener('click', e => {
        e.stopPropagation();
        _toggle(key, el.dataset.value, el);
      });
    });

    _renderChips(key);
    // Sync to state
    state.filters[key] = _selected(key);
  }

  function toggle(key) {
    const dd = document.getElementById(`dd-${key}`);
    const wrap = document.getElementById(`fs-${key}`);
    if (!dd || !wrap) return;

    const isOpen = !dd.classList.contains('hidden');
    // Close all
    document.querySelectorAll('.fs-dropdown').forEach(d => d.classList.add('hidden'));
    document.querySelectorAll('.filter-select-wrap').forEach(w => w.classList.remove('open'));

    if (!isOpen) {
      dd.classList.remove('hidden');
      wrap.classList.add('open');
    }
  }

  function _toggle(key, value, el) {
    const s = _states[key];
    if (!s) return;
    if (s.selected.has(value)) {
      s.selected.delete(value);
      el.classList.remove('selected');
    } else {
      s.selected.add(value);
      el.classList.add('selected');
    }
    _renderChips(key);
    state.filters[key] = _selected(key);
    onFiltersChange();
  }

  function deselect(key, value) {
    const s = _states[key];
    if (!s) return;
    s.selected.delete(value);
    const el = document.querySelector(`#dd-${key} [data-value="${CSS.escape(value)}"]`);
    el?.classList.remove('selected');
    _renderChips(key);
    state.filters[key] = _selected(key);
    onFiltersChange();
  }

  function _selected(key) {
    const s = _states[key];
    if (!s) return [];
    const allSelected = s.selected.size === s.options.length;
    // If all selected or none selected → send empty (= no filter)
    return (allSelected || s.selected.size === 0) ? [] : Array.from(s.selected);
  }

  function _renderChips(key) {
    const s = _states[key];
    const el = document.getElementById(`chips-${key}`);
    if (!s || !el) return;

    if (s.selected.size === 0 || s.selected.size === s.options.length) {
      el.innerHTML = `<span class="fs-placeholder">${escHtml(s.label)}</span>`;
    } else {
      el.innerHTML = Array.from(s.selected).map(v => `
        <span class="fs-chip">${escHtml(v)}
          <span class="fs-chip-x" onclick="event.stopPropagation();FS.deselect('${key}','${escHtml(v).replace(/'/g, "\\'")}')">×</span>
        </span>
      `).join('');
    }
  }

  function reset() {
    Object.keys(_states).forEach(key => {
      const s = _states[key];
      s.selected = new Set();
      document.querySelectorAll(`#dd-${key} .fs-option`).forEach(el => el.classList.remove('selected'));
      _renderChips(key);
      state.filters[key] = [];
    });
  }

  // Close on outside click
  document.addEventListener('click', e => {
    if (!e.target.closest('.filter-select-wrap')) {
      document.querySelectorAll('.fs-dropdown').forEach(d => d.classList.add('hidden'));
      document.querySelectorAll('.filter-select-wrap').forEach(w => w.classList.remove('open'));
    }
  });

  return { init, toggle, deselect, reset };
})();

// ═══════════════════════════════════════════════════════
//  FILTERS INIT
// ═══════════════════════════════════════════════════════
function initFilters() {
  const fo = window.INIT.filterOptions;
  FILTER_DEFS.forEach(def => {
    const opts = fo[def.optKey] || [];
    FS.init(def, opts);
  });

  document.getElementById('reset-all-btn')?.addEventListener('click', () => {
    FS.reset();
    onFiltersChange();
  });
}

// ── Debounced filter change handler ────────────────────
let _filterTimer = null;
function onFiltersChange() {
  clearTimeout(_filterTimer);
  _filterTimer = setTimeout(refreshMetrics, 400);
}

async function refreshMetrics() {
  try {
    const res = await fetch('/api/metrics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filters: state.filters }),
    });
    const data = await res.json();
    updateMetricDisplay(data.metrics);
    updateInsights(data.quick_insights || []);
  } catch (err) {
    console.error('Metrics refresh failed:', err);
  }
}

function updateMetricDisplay(m) {
  if (!m) return;
  setText('m-total-spend', m.total_spend);
  setText('m-installs',    m.total_installs);
  setText('m-cpi',         m.avg_cpi);
  setText('m-approval',    m.avg_approval);
  setText('m-repayment',   m.avg_repayment);
  setText('m-quality',     m.avg_quality);
}

function updateInsights(insights) {
  const el = document.getElementById('quick-insights-list');
  if (!el) return;
  if (!insights.length) {
    el.innerHTML = '<div class="insight-empty">Ask a question to generate insights.</div>';
    return;
  }
  el.innerHTML = insights.map(ins => `
    <div class="insight-item fade-in">
      <div class="insight-icon ii-${escHtml(ins.color)}">${ins.icon}</div>
      <div class="insight-text">${ins.text}</div>
    </div>
  `).join('');
}

// ═══════════════════════════════════════════════════════
//  CHAT
// ═══════════════════════════════════════════════════════
function initChat() {
  const input = document.getElementById('chat-input');
  input?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
}

function handleSend() {
  const input = document.getElementById('chat-input');
  const q = (input?.value || '').trim();
  if (!q || state.isLoading) return;
  input.value = '';
  sendMessage(q);
}

function submitChip(question) {
  sendMessage(question);
}

async function sendMessage(question) {
  if (state.isLoading) return;
  state.isLoading = true;
  state.hasMessages = true;

  showChatView();
  appendUserMessage(question);
  
  const typingId = appendTypingIndicator('Thinking...');
  document.getElementById('evidence-panel-container').innerHTML = ''; // Clear evidence panel

  try {
    // Append user message to state
    state.messages.push({ role: 'user', content: question });

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        question, 
        filters: state.filters,
        history: state.messages.slice(-6) // Send latest 3 conversations (6 messages)
      }),
    });
    
    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // keep the last incomplete chunk

      for (const part of parts) {
        if (part.startsWith('data: ')) {
          const jsonStr = part.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.status === 'progress') {
              updateTypingIndicator(typingId, data.message);
            } else if (data.status === 'complete') {
              removeTypingIndicator(typingId);
              appendAIMessage(data.result);
              // Store AI response in state.messages
              const aiText = [data.result.decision, data.result.why, data.result.evidence, data.result.recommended_action].filter(Boolean).join('\n');
              state.messages.push({ role: 'assistant', content: aiText });
              if (data.result.evidence_type && data.result.evidence_data) {
                renderEvidence(data.result.evidence_type, data.result.evidence_data);
              }
            } else if (data.status === 'error') {
              removeTypingIndicator(typingId);
              appendErrorMessage(data.message);
            }
          } catch (e) {
            console.error('Error parsing SSE json:', e, jsonStr);
          }
        }
      }
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendErrorMessage();
    console.error('Chat error:', err);
  } finally {
    state.isLoading = false;
    setSendBtnState(false);
  }
}

function clearChat() {
  state.messages = [];
  state.hasMessages = false;
  document.getElementById('chat-messages').innerHTML = '';
  document.getElementById('evidence-panel-container').innerHTML = '';
  document.getElementById('welcome-state')?.classList.remove('hidden');
  document.getElementById('chat-messages')?.classList.add('hidden');
}

async function renderEvidence(type, data) {
  const container = document.getElementById('evidence-panel-container');
  if (!container) return;

  container.innerHTML = `
    <div class="evidence-panel-title">
      <span class="dot" style="display:inline-block;width:8px;height:8px;background:#4F46E5;border-radius:50%;margin-right:8px"></span>
      Evidence Panel
    </div>
    <div id="evidence-content" style="background:white;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin-bottom:20px"></div>
  `;
  
  const content = document.getElementById('evidence-content');
  content.innerHTML = '<div style="text-align:center;color:#6B7280;padding:20px">Loading evidence data...</div>';

  if (type === 'copy_gen') {
    let html = '';
    const winning = data.winning_creatives || [];
    const copies = data.generated_copies || '';
    
    if (winning.length > 0) {
      html += '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:#374151">Winning Creative Patterns</div>';
      html += '<table style="width:100%;font-size:12px;text-align:left;border-collapse:collapse;margin-bottom:16px">';
      html += '<tr style="border-bottom:1px solid #E5E7EB;color:#6B7280"><th>Name</th><th>Angle</th><th>Repayment Rate</th><th>Quality Score</th></tr>';
      winning.forEach(w => {
        html += `<tr style="border-bottom:1px solid #F3F4F6">
          <td style="padding:6px 0">${escHtml(w.creative_name)}</td>
          <td style="padding:6px 0">${escHtml(w.copy_angle)}</td>
          <td style="padding:6px 0">${parseFloat(w.repayment_rate).toFixed(3)}</td>
          <td style="padding:6px 0">${parseFloat(w.creative_quality_score).toFixed(3)}</td>
        </tr>`;
      });
      html += '</table>';
    }
    
    if (copies) {
      html += '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:#374151">Generated Copy Variants</div>';
      html += `<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px;font-size:13px;line-height:1.6;color:#374151;white-space:normal;" class="markdown-body">${marked.parse(copies)}</div>`;
    }
    
    content.innerHTML = html;
  } else {
    // For charts, we fetch from /api/evidence
    try {
      const res = await fetch('/api/evidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: type, filters: state.filters }),
      });
      const evidenceData = await res.json();
      
      content.innerHTML = '<div id="plotly-container" style="width:100%;height:300px"></div>';
      const pData = [];
      const layout = { margin: { t: 10, r: 10, b: 30, l: 40 }, autosize: true };

      if (type === 'ad_table') {
        content.innerHTML = '<div style="overflow-x:auto"><table id="ev-table" style="width:100%;font-size:12px;text-align:left;border-collapse:collapse"><tr style="border-bottom:1px solid #E5E7EB;color:#6B7280"><th>Ad Name</th><th>Platform</th><th>Angle</th><th>Spend</th><th>CPI</th><th>Repayment</th></tr></table></div>';
        const tbl = document.getElementById('ev-table');
        evidenceData.forEach(r => {
          tbl.innerHTML += `<tr style="border-bottom:1px solid #F3F4F6"><td style="padding:6px 0">${escHtml(r.ad_name)}</td><td>${escHtml(r.platform)}</td><td>${escHtml(r.copy_angle)}</td><td>₹${r.spend}</td><td>₹${r.cpi}</td><td>${r.repayment_rate}</td></tr>`;
        });
      } else if (type === 'platform') {
        pData.push({ x: evidenceData.map(d => d.platform), y: evidenceData.map(d => d.spend), type: 'bar', name: 'Spend' });
        Plotly.newPlot('plotly-container', pData, layout, {displayModeBar: false});
      } else if (type === 'funnel') {
        const keys = Object.keys(evidenceData);
        const vals = Object.values(evidenceData);
        pData.push({ type: 'funnel', y: keys, x: vals, textinfo: "value+percent initial" });
        Plotly.newPlot('plotly-container', pData, layout, {displayModeBar: false});
      } else if (type === 'scatter') {
        pData.push({ x: evidenceData.map(d => d.cpi), y: evidenceData.map(d => d.repayment_rate), mode: 'markers', text: evidenceData.map(d => d.ad_name), marker: { size: evidenceData.map(d => Math.max(5, (d.spend || 0)/1000)) } });
        layout.xaxis = { title: 'CPI (₹)' };
        layout.yaxis = { title: 'Repayment Rate' };
        Plotly.newPlot('plotly-container', pData, layout, {displayModeBar: false});
      } else if (type === 'creative') {
        pData.push({ x: evidenceData.map(d => d.copy_angle || d.creative_name), y: evidenceData.map(d => d.avg_quality), type: 'bar', name: 'Quality Score' });
        Plotly.newPlot('plotly-container', pData, layout, {displayModeBar: false});
      }
    } catch (err) {
      console.error('Evidence render error:', err);
      content.innerHTML = '<div style="color:#991B1B">Failed to load evidence chart.</div>';
    }
  }
}

// ── Show chat vs welcome ────────────────────────────────
function showChatView() {
  document.getElementById('welcome-state')?.classList.add('hidden');
  document.getElementById('chat-messages')?.classList.remove('hidden');
  setSendBtnState(true);
}

function setSendBtnState(loading) {
  const btn = document.getElementById('send-btn');
  if (!btn) return;
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="6" stroke="white" stroke-width="2" stroke-dasharray="28" stroke-dashoffset="0"><animateTransform attributeName="transform" type="rotate" from="0 9 9" to="360 9 9" dur="0.8s" repeatCount="indefinite"/></circle></svg>'
    : '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M16 2L2 9l5 2 2 5 7-14z" fill="white"/></svg>';
}

// ── Message rendering ───────────────────────────────────
function appendUserMessage(text) {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.className = 'msg-user fade-in';
  el.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  container.appendChild(el);
  scrollToBottom(container);
}

function appendTypingIndicator(initialMessage = 'Thinking...') {
  const container = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  const el = document.createElement('div');
  el.id = id;
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="avatar" style="width:32px;height:32px;background:#EEF2FF;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px">🤖</div>
    <div class="typing-text" style="margin-left:12px;font-size:13px;color:#6B7280;display:flex;align-items:center">
      <span class="typing-msg">${escHtml(initialMessage)}</span>
      <div class="typing-dots" style="margin-left:8px;margin-top:0">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  container.appendChild(el);
  scrollToBottom(container);
  return id;
}

function updateTypingIndicator(id, message) {
  const el = document.getElementById(id);
  if (el) {
    const msgEl = el.querySelector('.typing-msg');
    if (msgEl) msgEl.textContent = message;
  }
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function appendAIMessage(answer) {
  const container = document.getElementById('chat-messages');
  const decision    = answer.decision || '';
  const why         = answer.why || '';
  const evidence    = answer.evidence || '';
  const recAction   = answer.recommended_action || '';
  const confidence  = parseFloat(answer.confidence || 0.5);
  const items       = answer.action_items || [];
  const trace       = answer.agent_trace || [];
  const pct         = Math.round(confidence * 100);
  const actionCls   = recAction.replace(/\s+/g, '-') || 'Investigate';

  let html = `
    <div class="msg-ai fade-in">
      <div class="avatar" style="width:32px;height:32px;background:#EEF2FF;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">🤖</div>
      <div style="flex:1;min-width:0">
        <div class="answer-card">
          <div class="answer-section-head">🎯 Decision</div>
          <div class="answer-decision markdown-body">${marked.parse(decision)}</div>
  `;

  if (why) {
    html += `<hr class="answer-divider"><div class="answer-section-head">📊 Why</div><div class="answer-body markdown-body">${marked.parse(why)}</div>`;
  }

  if (evidence) {
    html += `<hr class="answer-divider"><div class="answer-section-head">🔍 Evidence</div><div class="answer-body markdown-body">${marked.parse(evidence)}</div>`;
  }

  if (recAction) {
    html += `<hr class="answer-divider"><div class="answer-section-head">✅ Recommended Action</div>
    <span class="action-badge action-${escHtml(actionCls)}">${escHtml(recAction)}</span>`;
  }

  if (items.length) {
    html += `<ul style="padding-left:16px;font-size:12px;color:#374151;margin:8px 0 0">${items.map(i => `<li>${escHtml(i)}</li>`).join('')}</ul>`;
  }

  html += `
    <hr class="answer-divider">
    <div style="display:flex;align-items:center;gap:8px">
      <span style="font-size:11px;color:#9CA3AF">Confidence</span>
      <div class="confidence-bar-bg"><div class="confidence-bar-fill" style="width:${pct}%"></div></div>
      <span style="font-size:11px;color:#6B7280;font-weight:500">${pct}%</span>
    </div>
  </div>`;

  if (trace.length) {
    const traceId = 'trace-' + Date.now();
    html += `
      <div class="trace-expander">
        <div class="trace-toggle" onclick="document.getElementById('${traceId}').classList.toggle('hidden')">
          🔬 Show how this answer was generated <span style="font-size:9px">▼</span>
        </div>
        <div class="trace-body hidden" id="${traceId}">
          ${trace.map(t => `
            <div style="margin-bottom:10px">
              <div style="font-size:11px;color:#9CA3AF;margin-bottom:3px">Agent</div>
              <span class="trace-badge trace-agent">${escHtml(t.agent || '—')}</span>
              <div style="font-size:11px;color:#9CA3AF;margin:5px 0 3px">Tools</div>
              ${(t.tools_called || []).map(tl => `<span class="trace-badge trace-tool">${escHtml(tl)}</span>`).join('')}
              <div style="font-size:11px;color:#9CA3AF;margin:5px 0 3px">Tables</div>
              ${(t.tables_used || []).map(tb => `<span class="trace-badge trace-table">${escHtml(tb)}</span>`).join('')}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  html += `</div></div>`;

  const el = document.createElement('div');
  el.innerHTML = html;
  container.appendChild(el.firstElementChild);
  scrollToBottom(container);
}

function appendErrorMessage() {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.className = 'msg-ai fade-in';
  el.innerHTML = `
    <div class="avatar" style="width:32px;height:32px;background:#FEE2E2;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px">⚠️</div>
    <div class="answer-card" style="color:#991B1B">Something went wrong. Please try again.</div>
  `;
  container.appendChild(el);
  scrollToBottom(container);
}

function scrollToBottom(el) {
  el.scrollTop = el.scrollHeight;
}

// ═══════════════════════════════════════════════════════
//  UTILS
// ═══════════════════════════════════════════════════════
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '—';
}

// ═══════════════════════════════════════════════════════
//  BOOT
// ═══════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initFilters();
  initChat();
});
