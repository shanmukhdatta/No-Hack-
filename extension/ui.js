const $ = id => document.getElementById(id);

async function send(type, settings) {
  const response = await chrome.runtime.sendMessage({type, settings});
  if (response?.error) throw new Error(response.error);
  return response;
}

function message(text) {
  $("message").textContent = text;
  $("message").classList.toggle("hidden", !text);
}

function showView(view) {
  for (const panel of document.querySelectorAll("[data-panel]")) {
    panel.classList.toggle("hidden", panel.dataset.panel !== view);
  }
  for (const tab of document.querySelectorAll("[data-view]")) {
    const active = tab.dataset.view === view;
    tab.classList.toggle("selected", active);
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
}

function renderEvents(items) {
  const root = $("events");
  root.replaceChildren();
  if (!items.length) {
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = "No saved browser navigation signals.";
    root.append(p);
    return;
  }
  for (const item of items.slice().reverse().slice(0, 40)) {
    const div = document.createElement("div");
    div.className = "event";
    const host = document.createElement("div");
    host.className = "host";
    host.textContent = item.host;
    const detail = document.createElement("div");
    detail.className = "meta";
    detail.textContent = item.level + " · " + item.scheme.toUpperCase() + " · " + new Date(item.at).toLocaleString();
    div.append(host, detail);
    root.append(div);
  }
}

function renderAssessments(assessments) {
  const root = $("ml-assessments");
  root.replaceChildren();
  if (!assessments?.length) {
    const node = document.createElement("p");
    node.className = "muted small";
    node.textContent = "No verified local ML assessments available.";
    root.append(node);
    return;
  }
  const allowed = new Set(["NORMAL", "KNOWN_THREAT", "NOVEL_ANOMALY", "UNCERTAIN"]);
  for (const assessment of assessments.slice(0, 10)) {
    if (!allowed.has(assessment?.state)) continue;
    const item = document.createElement("div");
    item.className = "event";
    const risk = Number.isInteger(assessment.risk_score) &&
      assessment.risk_score >= 0 && assessment.risk_score <= 100
      ? String(assessment.risk_score) : "unavailable";
    item.textContent = assessment.state +
      (assessment.attack_family ? " · Family " + String(assessment.attack_family) : "") +
      " · Risk index " + risk + "/100 · " +
      String(assessment.observed_at || "unknown time");
    root.append(item);
  }
}

function renderCurrent(current) {
  $("current-host").textContent = current.host || "Unsupported or restricted page";
  $("current-level").textContent =
    current.level === "REVIEW" ? "Review connection indicators" :
    current.level === "INFORMATIONAL" ? "Information only" : "Not available";
  $("current-level").className = "signal " + current.level.toLowerCase();
  $("current-explanation").textContent =
    "Browser URL indicators only. No machine-learning attack classification has been performed.";
  $("reasons").replaceChildren();
  for (const reason of current.reasons || []) {
    const li = document.createElement("li");
    li.textContent = reason;
    $("reasons").append(li);
  }
}

async function refresh() {
  const [state, current] = await Promise.all([send("GET_STATE"), send("GET_ACTIVE")]);
  $("monitor-label").textContent = state.enabled ? "Enabled" : "Paused";
  $("monitor-label").classList.toggle("on", state.enabled);
  $("monitor-toggle").textContent = state.enabled ? "Pause" : "Enable";
  $("alert-toggle").checked = state.alerts;
  $("retention").value = String(state.retentionDays);
  renderEvents(state.events || []);
  renderCurrent(current);
}

async function action(callback) {
  try { message(""); await callback(); await refresh(); }
  catch (err) { message("Unable to complete action: " + String(err?.message || err)); }
}

document.querySelectorAll("[data-view]").forEach(tab => tab.addEventListener("click", () => showView(tab.dataset.view)));
$("monitor-toggle").addEventListener("click", () => action(async () => {
  const state = await send("GET_STATE");
  await send("SET_SETTINGS", {enabled: !state.enabled});
}));
$("clear-events").addEventListener("click", () => action(() => send("CLEAR_EVENTS")));
$("alert-toggle").addEventListener("change", () => action(() => send("SET_SETTINGS", {alerts: $("alert-toggle").checked})));
$("retention").addEventListener("change", () => action(() => send("SET_SETTINGS", {retentionDays: Number($("retention").value)})));
$("check-companion").addEventListener("click", () => action(async () => {
  const result = await send("COMPANION_STATUS");
  $("companion-result").textContent = result.connected
    ? "Companion connected. Capture dependencies: " +
      (result.capture?.live_capture_ready ? "detected" : "not fully detected") +
      ". " + (result.model_loaded === true ? "Model connected." : "Model not connected — install and score with a verified local model.")
    : result.reason;
  const predictions = result.connected ? await send("COMPANION_ASSESSMENTS") : null;
  renderAssessments(predictions?.assessments || []);
}));
if ($("open-dashboard")) $("open-dashboard").addEventListener("click", () => chrome.runtime.openOptionsPage());
void action(refresh);
