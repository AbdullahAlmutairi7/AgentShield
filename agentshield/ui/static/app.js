let selectedSessionId = null;
let selectedEvent = null;

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return await res.json();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function badge(sev) {
  return `<span class="badge ${sev}">${sev}</span>`;
}

function trustClass(trust) {
  if (trust === "DANGER" || trust === "HIGH_RISK") return "trust-high";
  if (trust === "SUSPICIOUS") return "trust-medium";
  return "trust-normal";
}

function rowClass(item) {
  if (item.blocked) return "row-blocked";
  if ((item.risk_score || 0) >= 0.5) return "row-highrisk";
  return "";
}

function currentFilters() {
  return {
    severity: document.getElementById("severity-filter")?.value || "all",
    trust: document.getElementById("trust-filter")?.value || "all",
    blockedOnly: document.getElementById("blocked-only")?.checked || false,
  };
}

function applyEventFilters(events) {
  const filters = currentFilters();
  return events.filter((ev) => {
    if (filters.blockedOnly && !ev.blocked) return false;
    if (filters.severity !== "all" && ev.severity !== filters.severity) return false;
    if (filters.trust !== "all" && (ev.trust_grade || "NORMAL") !== filters.trust) return false;
    return true;
  });
}

function applySessionFilters(sessions) {
  const filters = currentFilters();
  return sessions.filter((s) => {
    if (filters.blockedOnly && !(s.blocked_count > 0)) return false;
    if (filters.trust !== "all" && (s.max_trust_grade || "NORMAL") !== filters.trust) return false;
    return true;
  });
}

function renderAlerts(alerts) {
  const box = document.getElementById("alerts-list");
  box.innerHTML = "";
  for (const alert of alerts) {
    const div = document.createElement("div");
    div.className = "alert-item";
    div.innerHTML = `
      <strong>${alert.summary}</strong>
      <div>${badge(alert.severity)} · ${alert.event_type}</div>
      <div class="meta">Session: ${alert.session_id}</div>
      <div class="meta">${alert.reason || ""}</div>
    `;
    box.appendChild(div);
  }
}

function renderMiniSessionList(id, sessions, labelField = "max_risk_score") {
  const box = document.getElementById(id);
  box.innerHTML = "";
  if (!sessions.length) {
    box.innerHTML = "<p>No data.</p>";
    return;
  }

  for (const s of sessions) {
    const div = document.createElement("div");
    div.className = "mini-item";
    div.innerHTML = `
      <strong>${s.session_id}</strong>
      <div class="meta">Events: ${s.event_count} · Blocked: ${s.blocked_count}</div>
      <div class="meta">${labelField === "max_risk_score" ? "Risk" : "Blocked"}: ${s[labelField] || 0}</div>
    `;
    box.appendChild(div);
  }
}

function renderBreakdown(boxId, data) {
  const box = document.getElementById(boxId);
  box.innerHTML = "";

  const entries = Object.entries(data || {});
  if (!entries.length) {
    box.innerHTML = "<p>No data.</p>";
    return;
  }

  for (const [key, value] of entries) {
    const div = document.createElement("div");
    div.className = "detail-row";
    div.innerHTML = `<span class="detail-label">${key}:</span>${value}`;
    box.appendChild(div);
  }
}

function renderTimeline(events) {
  const box = document.getElementById("timeline-list");
  box.innerHTML = "";
  for (const ev of events.slice(0, 8)) {
    const div = document.createElement("div");
    div.className = "timeline-item";
    div.innerHTML = `
      <strong>${ev.summary}</strong>
      <div>${badge(ev.severity)} · ${ev.event_type}</div>
      <div class="meta">${ev.created_at}</div>
      <div class="meta">Session: ${ev.session_id}</div>
    `;
    box.appendChild(div);
  }
}

function renderRecentEvents(events) {
  const body = document.getElementById("recent-events-body");
  body.innerHTML = "";
  for (const ev of events) {
    const row = document.createElement("tr");
    row.className = rowClass(ev);
    row.innerHTML = `
      <td>${ev.created_at}</td>
      <td>${ev.session_id}</td>
      <td>${ev.event_type}</td>
      <td>${badge(ev.severity)}</td>
      <td>${ev.risk_score ?? 0}</td>
      <td>${ev.summary}</td>
    `;
    body.appendChild(row);
  }
}

async function loadOperatorLog() {
  const logs = await fetchJSON("/api/operator/actions?limit=20");
  const box = document.getElementById("operator-log-box");

  if (!logs.length) {
    box.innerHTML = "<p>No operator actions yet.</p>";
    return;
  }

  box.innerHTML = "";
  for (const entry of logs) {
    const div = document.createElement("div");
    div.className = "log-entry";
    div.innerHTML = `
      <div><strong>${entry.action_type}</strong></div>
      <div class="meta">Session: ${entry.session_id}</div>
      <div class="meta">${entry.timestamp}</div>
    `;
    box.appendChild(div);
  }
}

async function loadSessionDetail(sessionId) {
  const detail = await fetchJSON(`/api/dashboard/session/${encodeURIComponent(sessionId)}`);
  const session = detail.session;
  const events = detail.events || [];
  selectedSessionId = sessionId;

  const box = document.getElementById("session-detail-box");
  if (!session) {
    box.innerHTML = "<p>No session detail available.</p>";
    return;
  }

  const pills = [];
  if (session.quarantined) pills.push(`<span class="state-pill quarantined">QUARANTINED</span>`);
  if (session.reviewed) pills.push(`<span class="state-pill reviewed">REVIEWED</span>`);

  box.innerHTML = `
    <h3>${session.session_id}</h3>
    <div class="detail-row"><span class="detail-label">Agent:</span>${session.agent_name || session.agent_id}</div>
    <div class="detail-row"><span class="detail-label">Events:</span>${session.event_count}</div>
    <div class="detail-row"><span class="detail-label">Blocked:</span>${session.blocked_count}</div>
    <div class="detail-row"><span class="detail-label">Max Risk:</span>${session.max_risk_score}</div>
    <div class="detail-row"><span class="detail-label">Max Drift:</span>${session.max_drift_score}</div>
    <div class="detail-row"><span class="detail-label">Trust:</span><span class="${trustClass(session.max_trust_grade || 'NORMAL')}">${session.max_trust_grade || 'NORMAL'}</span></div>
    <div class="detail-row"><span class="detail-label">Started:</span>${session.started_at}</div>
    <div class="detail-row"><span class="detail-label">Last Seen:</span>${session.last_seen_at}</div>
    <div class="detail-row">${pills.join(" ")}</div>
  `;

  renderSessionEvents(events);
}

function renderSessionEvents(events) {
  const body = document.getElementById("session-events-body");
  body.innerHTML = "";

  for (const ev of events) {
    const row = document.createElement("tr");
    row.className = `${rowClass(ev)} event-row-clickable`;
    row.innerHTML = `
      <td>${ev.created_at}</td>
      <td>${ev.event_type}</td>
      <td>${badge(ev.severity)}</td>
      <td>${ev.risk_score ?? 0}</td>
      <td>${ev.decision}</td>
      <td>${ev.summary}</td>
    `;
    row.addEventListener("click", () => renderEventSpotlight(ev));
    body.appendChild(row);
  }
}

function renderEventSpotlight(ev) {
  selectedEvent = ev;
  const box = document.getElementById("event-spotlight-box");
  box.innerHTML = `
    <h3>${ev.event_type}</h3>
    <div class="detail-row"><span class="detail-label">Time:</span>${ev.created_at}</div>
    <div class="detail-row"><span class="detail-label">Session:</span>${ev.session_id}</div>
    <div class="detail-row"><span class="detail-label">Severity:</span>${ev.severity}</div>
    <div class="detail-row"><span class="detail-label">Verdict:</span>${ev.verdict}</div>
    <div class="detail-row"><span class="detail-label">Decision:</span>${ev.decision}</div>
    <div class="detail-row"><span class="detail-label">Risk Score:</span>${ev.risk_score ?? 0}</div>
    <div class="detail-row"><span class="detail-label">Trust Grade:</span>${ev.trust_grade || "NORMAL"}</div>
    <div class="detail-row"><span class="detail-label">Summary:</span>${ev.summary}</div>
    <div class="detail-row"><span class="detail-label">Reason:</span>${ev.reason || "-"}</div>
    <div class="detail-row"><span class="detail-label">Path:</span>${ev.path || "-"}</div>
    <div class="detail-row"><span class="detail-label">Tool:</span>${ev.tool_name || "-"}</div>
    <div class="detail-row"><span class="detail-label">Drift:</span>${ev.drift_score ?? "-"}</div>
  `;
}

function renderSessions(sessions) {
  const body = document.getElementById("sessions-body");
  body.innerHTML = "";

  for (const s of sessions) {
    const trust = s.max_trust_grade || "NORMAL";
    const row = document.createElement("tr");
    row.className = `${(s.blocked_count > 0)
      ? "row-blocked"
      : ((s.max_risk_score || 0) >= 0.5 ? "row-highrisk" : "")} session-row-clickable`;

    row.innerHTML = `
      <td>${s.session_id}</td>
      <td>${s.event_count}</td>
      <td>${s.blocked_count}</td>
      <td>${s.max_risk_score ?? 0}</td>
      <td>${s.max_drift_score ?? 0}</td>
      <td class="${trustClass(trust)}">${trust}</td>
    `;
    row.addEventListener("click", () => loadSessionDetail(s.session_id));
    body.appendChild(row);
  }
}

async function quarantineSelectedSession() {
  if (!selectedSessionId) return;
  await fetchJSON(`/api/operator/session/${encodeURIComponent(selectedSessionId)}/quarantine`, { method: "POST" });
  await loadDashboard();
  await loadOperatorLog();
  await loadSessionDetail(selectedSessionId);
}

async function reviewSelectedSession() {
  if (!selectedSessionId) return;
  await fetchJSON(`/api/operator/session/${encodeURIComponent(selectedSessionId)}/review`, { method: "POST" });
  await loadDashboard();
  await loadOperatorLog();
  await loadSessionDetail(selectedSessionId);
}

async function releaseSelectedSession() {
  if (!selectedSessionId) return;
  await fetchJSON(`/api/operator/session/${encodeURIComponent(selectedSessionId)}/release`, { method: "POST" });
  await loadDashboard();
  await loadOperatorLog();
  await loadSessionDetail(selectedSessionId);
}

function clearSpotlight() {
  selectedEvent = null;
  const box = document.getElementById("event-spotlight-box");
  box.innerHTML = `<p>Select an event from the session timeline below.</p>`;
}

async function loadDashboard() {
  try {
    const summary = await fetchJSON("/api/dashboard/summary");
    const eventsRaw = await fetchJSON("/api/dashboard/recent-events?limit=20");
    const sessionsRaw = await fetchJSON("/api/dashboard/sessions?limit=20");
    const alerts = await fetchJSON("/api/dashboard/alerts?limit=10");

    const events = applyEventFilters(eventsRaw);
    const sessions = applySessionFilters(sessionsRaw);

    setText("total-events", summary.totals.events);
    setText("blocked-events", summary.totals.blocked_events);
    setText("sessions-count", summary.totals.sessions);
    setText("high-risk-sessions", summary.totals.high_risk_sessions);
    setText("alerts-count", summary.totals.alerts);
    setText("max-risk-score", summary.totals.max_risk_score);
    setText("last-refresh", new Date().toLocaleTimeString());
    setText("refresh-note", `Auto-refreshing · ${new Date().toLocaleTimeString()}`);

    renderAlerts(alerts);
    renderMiniSessionList("top-risky-box", summary.top_risky_sessions || [], "max_risk_score");
    renderMiniSessionList("top-blocked-box", summary.top_blocked_sessions || [], "blocked_count");
    renderBreakdown("source-breakdown-box", summary.breakdowns.by_source_layer || {});
    renderBreakdown("severity-breakdown-box", summary.breakdowns.by_severity || {});
    renderTimeline(eventsRaw);
    renderRecentEvents(events);
    renderSessions(sessions);

    if (selectedSessionId) {
      await loadSessionDetail(selectedSessionId);
    }

    await loadOperatorLog();
  } catch (err) {
    console.error(err);
    setText("refresh-note", "Refresh failed");
  }
}

function renderExportResult(result) {
  const box = document.getElementById("export-results-box");
  if (!box) return;

  const lines = [];
  lines.push(`<div class="detail-row"><span class="detail-label">Report Type:</span>${result.report_type}</div>`);
  lines.push(`<div class="detail-row"><span class="detail-label">Generated At:</span>${result.generated_at}</div>`);

  if (result.session_id) {
    lines.push(`<div class="detail-row"><span class="detail-label">Session:</span>${result.session_id}</div>`);
  }
  if (result.count !== undefined) {
    lines.push(`<div class="detail-row"><span class="detail-label">Count:</span>${result.count}</div>`);
  }
  if (result.event_count !== undefined) {
    lines.push(`<div class="detail-row"><span class="detail-label">Event Count:</span>${result.event_count}</div>`);
  }
  if (result.json_path) {
    lines.push(`<div class="detail-row"><span class="detail-label">JSON:</span>${result.json_path}</div>`);
  }
  if (result.csv_path) {
    lines.push(`<div class="detail-row"><span class="detail-label">CSV:</span>${result.csv_path}</div>`);
  }

  box.innerHTML = lines.join("");
}

async function exportSummary() {
  const result = await fetchJSON("/api/reports/dashboard-summary", { method: "POST" });
  renderExportResult(result);
}

async function exportEvents() {
  const result = await fetchJSON("/api/reports/recent-events?limit=200", { method: "POST" });
  renderExportResult(result);
}

async function exportAlerts() {
  const result = await fetchJSON("/api/reports/alerts?limit=200", { method: "POST" });
  renderExportResult(result);
}

async function exportSessions() {
  const result = await fetchJSON("/api/reports/sessions?limit=200", { method: "POST" });
  renderExportResult(result);
}

async function exportSelectedSession() {
  if (!selectedSessionId) {
    const box = document.getElementById("export-results-box");
    if (box) box.innerHTML = "<p>Select a session first.</p>";
    return;
  }
  const result = await fetchJSON(`/api/reports/session/${encodeURIComponent(selectedSessionId)}`, { method: "POST" });
  renderExportResult(result);
}

function bindControls() {
  document.getElementById("refresh-btn")?.addEventListener("click", loadDashboard);
  document.getElementById("severity-filter")?.addEventListener("change", loadDashboard);
  document.getElementById("trust-filter")?.addEventListener("change", loadDashboard);
  document.getElementById("blocked-only")?.addEventListener("change", loadDashboard);
  document.getElementById("quarantine-btn")?.addEventListener("click", quarantineSelectedSession);
  document.getElementById("review-btn")?.addEventListener("click", reviewSelectedSession);
  document.getElementById("release-btn")?.addEventListener("click", releaseSelectedSession);
  document.getElementById("clear-spotlight-btn")?.addEventListener("click", clearSpotlight);
  document.getElementById("export-summary-btn")?.addEventListener("click", exportSummary);
  document.getElementById("export-events-btn")?.addEventListener("click", exportEvents);
  document.getElementById("export-alerts-btn")?.addEventListener("click", exportAlerts);
  document.getElementById("export-sessions-btn")?.addEventListener("click", exportSessions);
  document.getElementById("export-session-btn")?.addEventListener("click", exportSelectedSession);
}

bindControls();
loadDashboard();
setInterval(loadDashboard, 5000);
