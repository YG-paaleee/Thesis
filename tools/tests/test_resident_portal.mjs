import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const page = fs.readFileSync(fileURLToPath(new URL('../../index.html', import.meta.url)), 'utf8');
const script = page.match(/<script>([\s\S]*?)<\/script>/)[1];
const secret = fs.readFileSync(fileURLToPath(new URL('../../include/aes_crypto.h', import.meta.url)), 'utf8')
  .match(/#define COMMUNITY_ACCESS_CREDENTIAL "([^"]+)"/)[1];
assert(!page.includes(secret), 'Community credential must not be embedded in the resident page');
assert(!script.includes('console.log("[Preview/submission error]"'), 'Do not log credential payloads');

function environment(response, nodeInfo = { nodeId: 2, role: 'mini_hub', radioState: 'ready', maxClients: 10, connectedClients: 2 }, options = {}) {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, { value: '', style: {}, setAttribute() {}, reset() {} });
    return elements.get(id);
  }
  const context = vm.createContext({ TextEncoder, Date, TypeError, console, AbortController,
    setTimeout: options.setTimeout || setTimeout, clearTimeout, setInterval() {}, confirm: options.confirm || (() => true),
    document: { getElementById: element },
    fetch: async (url, init) => url === '/api/node_info'
      ? { ok: true, json: async () => nodeInfo }
      : options.submit ? options.submit(init) : { ok: true, text: async () => JSON.stringify(response) } });
  vm.runInContext(script, context);
  element('credential').value = 'operator-provided-code';
  element('location').value = 'Indoor';
  element('message').value = 'Pilot test';
  if (!options.unselected) context.selectPriority(1);
  return { context, element };
}

for (const status of ['queued', 'delivered_local']) {
  const { context, element } = environment({ status, ref: 'V1#1234', priority: 3 });
  context.selectedPriority = 3;
  context.submitForm({ preventDefault() {} });
  context.selectedPriority = 1; // UI selection changes while response is pending
  await new Promise(resolve => setImmediate(resolve));
  assert(element('statusBox').innerHTML.includes('Routine update'), 'Use the server-accepted priority');
  assert(element('statusBox').innerHTML.includes(status === 'queued' ? 'Accepted by this node' : 'Recorded at the main hub'));
  context.handleDisconnect();
  assert(element('statusBox').innerHTML.includes(status === 'queued' ? 'not yet confirmed' : 'recorded on this main hub'));
  assert(element('statusBox').innerHTML.includes('V1#1234'), 'Keep reference visible after Wi-Fi instructions');
}
const { context, element } = environment({ status: 'queued', ref: 'V2#1234', priority: 3 });
context.clearForm();
assert.equal(element('credential').value, '');
assert.equal(context.selectedPriority, 0, 'Clear form must not default to Medical SOS');
let categoryCalls = 0;
const noCategory = environment({}, undefined, { unselected: true, submit: async () => { categoryCalls++; } });
assert.equal(noCategory.context.selectedPriority, 0);
await noCategory.context.submitForm({ preventDefault() {} });
assert.equal(categoryCalls, 0);
assert(noCategory.element('statusBox').innerHTML.includes('choose a report category'));
for (const priority of [1, 2, 3]) {
  let sent;
  const chosen = environment({}, undefined, { submit: async init => {
    sent = JSON.parse(init.body);
    return { ok: true, text: async () => JSON.stringify({ status: 'queued', ref: 'V2#1234', priority: sent.priority }) };
  }});
  chosen.context.selectPriority(priority);
  for (const value of [1, 2, 3]) assert.equal(chosen.element('priority-' + value).checked, value === priority);
  await chosen.context.submitForm({ preventDefault() {} });
  assert.equal(sent.priority, priority, 'Every category must preserve its firmware priority');
}
assert.equal((page.match(/type="radio" name="priority"/g) || []).length, 3);
assert(!page.includes('user-scalable=no'));
assert(!page.includes('Priority Queue'));
assert(!page.includes('(k=1)'));
console.log('Category checks passed: explicit choice required, all three payload priorities preserved, native radio controls and no Medical SOS default after reset.');
for (const [nodeId, role] of [[1, 'main_hub'], [3, 'mini_hub'], [6, 'edge']]) {
  context.applyNodeInfo({ nodeId, role, radioState: 'ready', maxClients: 10, connectedClients: 2 });
  assert(element('nodeIdentity').textContent.includes('V' + nodeId));
  assert(element('wifiCapacity').textContent.includes('2 of 10'));
  assert(element('networkStatus').textContent.includes('not yet confirmed'));
}
context.applyNodeInfo({ nodeId: 2, role: 'mini_hub', radioState: 'paused', maxClients: 10, connectedClients: 0 });
assert(element('networkStatus').textContent.includes('paused'));
context.applyNodeInfo({ nodeId: 2, role: 'mini_hub', radioState: 'unavailable', maxClients: 10, connectedClients: 0 });
assert(element('networkStatus').textContent.includes('unavailable'));
assert.throws(() => context.applyNodeInfo({ nodeId: 8 }));
const badMetadata = environment({}, null);
await new Promise(resolve => setImmediate(resolve));
assert(badMetadata.element('networkStatus').textContent.includes('unavailable'));
assert.equal(badMetadata.context.nodeInfoRequestActive, false);
assert(!page.includes('Mini Hub 3'));
assert(!page.includes('Wi-Fi supports up to 25'));
console.log('Resident portal checks passed: submission status, accepted priority, node roles, radio states, actual capacity, invalid metadata and no embedded passcode.');

let calls = 0, release;
const pending = environment({}, undefined, { submit: () => {
  calls++;
  return new Promise(resolve => { release = resolve; });
}});
const event = { preventDefault() {} };
const first = pending.context.submitForm(event);
pending.context.submitForm(event);
pending.context.clearForm();
assert.equal(calls, 1, 'Repeat submit must not start another request');
assert.equal(pending.element('message').value, 'Pilot test');
release({ ok: true, text: async () => JSON.stringify({ status: 'queued', ref: 'V2#1234', priority: 1 }) });
await first;
await pending.context.submitForm(event);
assert.equal(calls, 1, 'Identical confirmed report must not be sent again');
assert(pending.element('statusBox').innerHTML.includes('V2#1234'));

let allowRetry = false, recover = false;
const timed = environment({}, undefined, {
  setTimeout: (fn, ms) => setTimeout(fn, ms === 10000 ? 1 : ms),
  confirm: () => allowRetry,
  submit: init => { calls++;
    if (recover) return Promise.resolve({ ok: true, text: async () => JSON.stringify({ status: 'queued', ref: 'V2#9999', priority: 1 }) });
    return new Promise((resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(Object.assign(new Error('timeout'), { name: 'AbortError' })));
  }); }
});
await timed.context.submitForm(event);
assert.equal(timed.context.submissionActive, false);
assert.equal(timed.element('sendBtn').disabled, false);
assert(timed.element('statusBox').innerHTML.includes('Acceptance unknown'));
assert(timed.element('statusBox').innerHTML.includes('may already have accepted'));
assert.equal(timed.element('message').value, 'Pilot test');
const beforeRetry = calls;
await timed.context.submitForm(event);
assert.equal(calls, beforeRetry, 'Cancelled uncertain retry must not send');
allowRetry = true;
await timed.context.submitForm(event);
assert.equal(calls, beforeRetry + 1, 'Explicit retry is allowed after warning');
recover = true;
await timed.context.submitForm(event);
assert.equal(timed.context.submissionUncertain, false);
assert(timed.element('statusBox').innerHTML.includes('V2#9999'));

for (const mode of ['rejected', 'malformed', 'network']) {
  const failed = environment({}, undefined, { submit: async () => {
    if (mode === 'network') throw new TypeError('offline');
    return { ok: mode !== 'rejected', status: 503, text: async () => mode === 'rejected'
      ? JSON.stringify({ status: 'error', message: 'Queue full <test>' }) : 'not-json' };
  }});
  await failed.context.submitForm(event);
  assert.equal(failed.context.submissionActive, false);
  assert.equal(failed.element('message').value, 'Pilot test');
  assert.equal(failed.context.submissionUncertain, mode !== 'rejected');
  if (mode === 'rejected') assert(failed.element('statusBox').innerHTML.includes('&lt;test&gt;'));
}
console.log('Submission checks passed: timeout, repeat-click guard, retained text/reference, explicit rejection, uncertain retry warning and recovery.');

for (const [location, message, valid] of [
  ['L'.repeat(83), 'M'.repeat(117), true],
  ['L'.repeat(84), 'Help', false],
  ['L', 'M'.repeat(200), false],
  ['ñ'.repeat(41) + 'L', 'M'.repeat(117), true],
  ['ñ'.repeat(42), 'Help', false],
  ['L', '🚑'.repeat(49) + 'abc', true],
  ['L', '🚑'.repeat(50), false],
  ['Purok 3', 'Kailangan po ng tulong. May nasugatan.', true],
  ['L', 'e\u0301'.repeat(66) + 'a', true],
  ['L', 'e\u0301'.repeat(67), false],
  ['L', 'Help\u0000hidden', false],
  ['   ', 'Help', false],
  ['L', '   ', false]
]) {
  let submitted = null;
  const form = environment({}, undefined, { submit: async init => {
    submitted = JSON.parse(init.body);
    return { ok: true, text: async () => JSON.stringify({ status: 'queued', ref: 'V2#1234', priority: 1 }) };
  }});
  form.element('location').value = location;
  form.element('message').value = message;
  form.context.updateByteCount();
  assert.equal(form.element('location').value, location, 'Counting must preserve the entire location');
  assert.equal(form.element('message').value, message, 'Counting must not truncate a message or split emoji');
  await form.context.submitForm(event);
  assert.equal(submitted !== null, valid, 'Browser limits must match firmware UTF-8 byte limits');
  if (valid) assert.equal(submitted.message, message.trim());
  assert.equal(form.element('message').value, message, 'Rejection or acceptance must preserve entered text');
}
const edited = environment({ status: 'queued', ref: 'V2#1234', priority: 1 });
edited.element('message').value = '🚑'.repeat(60);
assert(edited.context.updateByteCount().error);
edited.element('message').value = 'Help';
assert.equal(edited.context.updateByteCount().error, '');
await edited.context.submitForm(event);
assert(edited.element('statusBox').innerHTML.includes('V2#1234'));
console.log('Input checks passed: 83-byte location, 200-byte shared budget, ASCII/Filipino/accented/emoji boundaries, preserved text, whitespace and edit recovery.');
