import test from "node:test";
import assert from "node:assert/strict";
import {analyzeAddress, makeEvent, pruneEvents, sanitizeSettings, MAX_EVENTS} from "../logic.mjs";

test("HTTPS is informational but never claims security", () => {
  const result = analyzeAddress("https://Example.org/login?password=do-not-store");
  assert.equal(result.level, "INFORMATIONAL");
  assert.equal(result.host, "example.org");
  assert.equal(JSON.stringify(result).includes("do-not-store"), false);
  assert.match(result.reasons.join(" "), /does not establish/);
});
test("HTTP is flagged for review without claiming malware", () => {
  const result = analyzeAddress("http://example.org/path");
  assert.equal(result.level, "REVIEW");
  assert.match(result.reasons[0], /HTTP/);
});
test("encoded hostname and numeric host are review signals", () => {
  assert.equal(analyzeAddress("https://xn--e1afmkfd.example").level, "REVIEW");
  assert.equal(analyzeAddress("https://192.168.1.1/").level, "REVIEW");
});
test("non-web and malformed addresses do not create events", () => {
  assert.equal(makeEvent("chrome://extensions"), null);
  assert.equal(makeEvent("not a url"), null);
  assert.equal(analyzeAddress(undefined).level, "UNAVAILABLE");
});
test("settings default to opt-out and enforce allowlisted retention", () => {
  assert.deepEqual(sanitizeSettings({enabled:"true", alerts:1, retentionDays:999}),
    {enabled:false, alerts:false, retentionDays:14});
  assert.equal(sanitizeSettings({enabled:true, retentionDays:7}).enabled, true);
});
test("event retention is bounded and ignores malformed events", () => {
  const now = 1_800_000_000_000;
  const sample = makeEvent("https://example.com", now);
  assert.ok(sample);
  const previous = {...sample, at: now - 31 * 86400000};
  const events = pruneEvents([previous, ...Array(250).fill(sample), {host:"bad"}], 30, now);
  assert.equal(events.length, MAX_EVENTS);
  assert.equal(events.every(x => x.host === "example.com"), true);
});
