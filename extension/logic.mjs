/**
 * Privacy-focused, explainable browser indicators, NOT a malware classifier.
 * Only scheme + hostname are retained. No paths, passwords or query parameters.
 */
export const MAX_EVENTS = 200;
export const DEFAULTS = Object.freeze({
  enabled: false,
  alerts: false,
  retentionDays: 14,
  events: []
});

export function analyzeAddress(raw) {
  if (typeof raw !== "string") return {level: "UNAVAILABLE", host: "", scheme: "", reasons: ["No accessible browser address."]};
  let url;
  try { url = new URL(raw); } catch {
    return {level: "UNAVAILABLE", host: "", scheme: "", reasons: ["Address could not be analyzed."]};
  }
  const scheme = url.protocol.replace(":", "").toLowerCase();
  if (scheme !== "http" && scheme !== "https") {
    return {level: "UNAVAILABLE", host: "", scheme, reasons: ["This browser page is outside HTTP/HTTPS monitoring."]};
  }
  const host = url.hostname.toLowerCase().slice(0, 253);
  if (!host) return {level: "UNAVAILABLE", host: "", scheme, reasons: ["Missing website hostname."]};
  const reasons = [];
  if (scheme === "http") reasons.push("This page uses HTTP rather than HTTPS. Information may be exposed in transit.");
  if (host.split(".").some(part => part.startsWith("xn--"))) {
    reasons.push("The domain contains encoded internationalized characters; verify the spelling.");
  }
  if (/^(?:\d{1,3}\.){3}\d{1,3}$/.test(host) || /^\[[\da-f:]+\]$/i.test(host)) {
    reasons.push("The site uses a numeric address; check that it is the destination you intended.");
  }
  if (scheme === "https") {
    reasons.push("HTTPS is used. Encryption alone does not establish that a site is trustworthy.");
  }
  return {level: reasons.some(r => !r.startsWith("HTTPS is")) ? "REVIEW" : "INFORMATIONAL", host, scheme, reasons};
}

export function sanitizeSettings(value) {
  const days = Number(value?.retentionDays);
  return {
    enabled: value?.enabled === true,
    alerts: value?.alerts === true,
    retentionDays: [1, 7, 14, 30].includes(days) ? days : DEFAULTS.retentionDays
  };
}

export function pruneEvents(events, days, now = Date.now()) {
  if (!Array.isArray(events)) return [];
  const cutoff = now - days * 86400000;
  return events.filter(item =>
    item && typeof item.host === "string" &&
    ["http", "https"].includes(item.scheme) &&
    ["REVIEW", "INFORMATIONAL"].includes(item.level) &&
    Number.isFinite(item.at) && item.at >= cutoff && item.at <= now
  ).slice(-MAX_EVENTS);
}

export function makeEvent(address, at = Date.now()) {
  const result = analyzeAddress(address);
  if (result.level === "UNAVAILABLE") return null;
  return {at, scheme: result.scheme, host: result.host, level: result.level, reasons: result.reasons};
}
