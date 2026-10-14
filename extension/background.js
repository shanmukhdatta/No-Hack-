import {DEFAULTS, analyzeAddress, makeEvent, pruneEvents, sanitizeSettings} from "./logic.mjs";

const HOST_NAME = "org.nohack.companion";
let serial = Promise.resolve();

async function snapshot() {
  const raw = await chrome.storage.local.get(["enabled", "alerts", "retentionDays", "events"]);
  const settings = sanitizeSettings(raw);
  return {...settings, events: pruneEvents(raw.events ?? [], settings.retentionDays)};
}

async function saveNavigation(url, tabId) {
  const candidate = makeEvent(url);
  if (!candidate) return;
  // Serialize read/modify/write cycles from concurrent navigation events.
  serial = serial.catch(() => {}).then(async () => {
    const state = await snapshot();
    if (!state.enabled) return;
    const events = pruneEvents([...state.events, candidate], state.retentionDays);
    await chrome.storage.local.set({events});
    if (Number.isInteger(tabId) && tabId >= 0) {
      const warn = state.alerts && candidate.level === "REVIEW" && candidate.scheme === "http";
      await chrome.action.setBadgeText({text: warn ? "!" : "", tabId});
      if (warn) await chrome.action.setBadgeBackgroundColor({color: "#B45309", tabId});
    }
  });
  await serial;
}

chrome.runtime.onInstalled.addListener(async () => {
  const previous = await chrome.storage.local.get(null);
  const missing = {};
  for (const [key, value] of Object.entries(DEFAULTS)) if (!(key in previous)) missing[key] = value;
  if (Object.keys(missing).length) await chrome.storage.local.set(missing);
});

chrome.webNavigation.onCommitted.addListener(details => {
  if (details.frameId === 0) void saveNavigation(details.url, details.tabId);
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (!msg || typeof msg.type !== "string") throw new Error("Invalid message");
    switch (msg.type) {
      case "GET_STATE":
        return snapshot();
      case "GET_ACTIVE": {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        const active = tabs[0]?.url;
        return analyzeAddress(active);
      }
      case "SET_SETTINGS": {
        const state = await snapshot();
        const next = sanitizeSettings({...state, ...msg.settings});
        await chrome.storage.local.set(next);
        if (!next.enabled) {
          await chrome.action.setBadgeText({text: ""});
        }
        return snapshot();
      }
      case "CLEAR_EVENTS":
        await chrome.storage.local.set({events: []});
        return snapshot();
      case "COMPANION_STATUS":
        // Read-only handshake; never starts capture or returns invented ML risk.
        try {
          const result = await chrome.runtime.sendNativeMessage(HOST_NAME, {type: "status"});
          if (!result || result.ok !== true) return {connected: false, reason: "Companion responded with an error."};
          return {connected: true, ...result};
        } catch {
          return {connected: false, reason: "Windows companion is not registered or available."};
        }
      default:
        throw new Error("Unknown message type");
    }
  })().then(sendResponse, err => sendResponse({error: String(err?.message ?? err)}));
  return true;
});

chrome.runtime.onStartup.addListener(async () => {
  const state = await snapshot();
  await chrome.storage.local.set({events: state.events});
});
