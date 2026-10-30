import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const page = fs.readFileSync(fileURLToPath(new URL('../../admin.html', import.meta.url)), 'utf8');
const script = page.match(/<script>([\s\S]*?)<\/script>/)[1];

function element() {
  const classes = new Set();
  return { children: [], style: {}, textContent: '', innerText: '--', value: 'all', attributes: {}, listeners: {},
    addEventListener(name, callback) { this.listeners[name] = callback; },
    classList: { toggle(name, on) { on ? classes.add(name) : classes.delete(name); } },
    appendChild(child) { this.children.push(child); return child; },
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
    removeChild(child) { this.children = this.children.filter(c => c !== child); },
    setAttribute(name, value) { this.attributes[name] = value; }, click() {} };
}
function environment(records = [], options = {}) {
  const elements = new Map();
  let mode = options.mode || 'good', lastBlob = null, downloadLink = null;
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  get('sortOrder').value = 'arrival';
  const context = vm.createContext({ Date, Map, Number, String, Blob, AbortController, console,
    setTimeout: options.fastTimeout ? (fn, ms) => setTimeout(fn, Math.min(ms, 5)) : setTimeout,
    clearTimeout, setInterval() {}, alert() {},
    URL: { createObjectURL(blob) { lastBlob = blob; return 'blob:fixture'; }, revokeObjectURL() {} },
    document: { getElementById: get, createElement(tag) { const e = element(); if (tag === 'a') downloadLink = e; return e; }, body: element() },
    fetch: async (url, request) => {
      if (mode === 'never') return new Promise((resolve, reject) => request.signal.addEventListener('abort', () => reject(new Error('timeout'))));
      if (mode === 'fail') throw new Error('fixture disconnect');
      let output = records;
      const headers = { 'X-Recent-Limit': '20', 'X-Recorded-Since-Boot': '25' };
      if (options.clock) Object.assign(headers, { 'X-Hub-Uptime-Ms': String(options.uptimeMs ?? 200000), 'X-Hub-Session': String(options.session ?? 777) });
      if (options.history) {
        const query = new URL(url, 'http://fixture').searchParams;
        const page = Number(query.get('page') || 1);
        const snapshot = Number(query.get('snapshot') || records.length);
        if (mode === 'expired' || (options.failPage && page === options.failPage)) return { ok: false, status: 409 };
        const retained = Math.min(snapshot, 200);
        const end = snapshot - (page - 1) * 20;
        output = records.filter(m => m.arrival > Math.max(snapshot - retained, end - 20) && m.arrival <= end);
        Object.assign(headers, { 'X-History-Capacity': '200', 'X-History-Retained': String(retained),
          'X-History-Pages': String(Math.max(1, Math.ceil(retained / 20))),
          'X-History-Snapshot': String(snapshot), 'X-Hub-Session': '777', 'X-Recorded-Since-Boot': String(records.length) });
      }
      return { ok: true, headers: { get(name) { return options.noHeaders ? null : headers[name] ?? null; } },
               json: async () => mode === 'invalid' ? { invalid: true } : JSON.parse(JSON.stringify(output)) };
    } });
  vm.runInContext(script, context);
  return { context, get, setMode(value) { mode = value; }, getBlob: () => lastBlob, getDownload: () => downloadLink };
}
const settle = () => new Promise(resolve => setImmediate(resolve));
const records = Array.from({ length: 20 }, (_, index) => ({
  id: index + 6, arrival: index + 6, priority: index < 5 ? 1 : 3,
  originNode: 2, origin: 'V2', packetType: 2, rxTime: 1000 * (index + 6),
  latencyMs: 13000, location: 'Indoor', message: index === 0 ? '=test' : 'Pilot', route: 'V2 -> V1'
}));
const live = environment(records);
await settle();
assert.equal(live.get('metricTotal').innerText, 20, 'Cards count the recent view, not the cumulative counter');
assert(live.get('historyNotice').textContent.includes('25 received since restart'));
assert(live.get('historyNotice').textContent.includes('Pagination unavailable'));
assert(!page.includes('id="metricLatency"'), 'Timing note must not occupy a fifth metric card');
assert(page.includes('Delivery timing requires verified paired logs'));
assert(live.get('sosList').children[0].textContent.includes('V2#0010'));
let firstRow = live.get('incidentTableBody').children[0];
assert.equal(firstRow.children.length, 5, 'Five main cells instead of ten crowded columns');
assert.equal(firstRow.children[2].textContent, 'V2#0006');
assert.equal(firstRow.children[1].children[0].textContent, 'Indoor');
assert.equal(firstRow.children[1].children[1].textContent, '=test');
assert(firstRow.children[3].textContent.includes('after hub restart'));
const disclosure = firstRow.children[4].children[0];
assert.equal(disclosure.open, false);
assert(disclosure.children[1].children.some(e => e.textContent.includes('V2 -> V1')));
assert(disclosure.children[1].children.some(e => e.textContent.includes('not verified delivery delay')));
disclosure.open = true; disclosure.listeners.toggle();
await live.context.refreshLiveIncidents();
assert.equal(live.get('incidentTableBody').children[0], firstRow, 'Unchanged polls must preserve focus and open disclosure DOM');
live.get('priorityFilter').value = '3';
live.context.renderTable();
assert.equal(live.get('incidentTableBody').children.length, 15);
live.get('priorityFilter').value = '2';
live.context.renderTable();
assert(live.get('incidentTableBody').children[0].children[0].textContent.includes('match this filter'));
live.get('priorityFilter').value = 'all';
live.get('sortOrder').value = 'newest';
live.context.renderTable();
assert.equal(live.get('incidentTableBody').children[0].children[2].textContent, 'V2#0025');
live.get('sortOrder').value = 'arrival'; live.context.renderTable();
firstRow = live.get('incidentTableBody').children[0];
assert.equal(firstRow.children[4].children[0].open, true, 'Disclosure remains open after sorting/filtering');
const originalMessage = records[0].message;
records[0].message = '<img src=x onerror=alert(1)>\n' + 'Long report '.repeat(20);
await live.context.refreshLiveIncidents();
firstRow = live.get('incidentTableBody').children[0];
assert.equal(firstRow.children[1].children[1].textContent, records[0].message, 'Render full report text literally');
assert.equal(firstRow.children[4].children[0].open, true, 'Details stay open when new data changes the view');
records[0].message = originalMessage;
await live.context.refreshLiveIncidents();
live.get('sortOrder').value = 'priority'; live.context.renderTable();
assert.equal(live.get('incidentTableBody').children[0].children[0].children[0].textContent, 'Medical SOS');
live.context.exportToCSV();
const csv = await live.getBlob().text();
assert(csv.includes('page_view_only'));
assert(csv.includes('Unverified_Clock_Difference_ms'));
assert(csv.includes('V2#0006'));
assert(csv.includes("'=test"), 'Spreadsheet formula-looking report text is escaped');
assert(live.getDownload().attributes.download.includes('Page_Reports'));
live.setMode('fail');
await live.context.refreshLiveIncidents();
assert(live.get('liveStatus').textContent.includes('showing saved view'));
assert.equal(live.get('metricTotal').innerText, 20, 'Connection loss must not reset prior counts to a claimed zero');
assert.equal(vm.runInContext('liveFetchInProgress', live.context), false);
live.setMode('good');
await live.context.refreshLiveIncidents();
assert(live.get('liveStatus').textContent.includes('Connected'));

const failed = environment([], { mode: 'fail' });
await settle();
assert.equal(failed.get('metricTotal').innerText, '--');
assert(failed.get('sosTitle').textContent.includes('unavailable'));
assert(failed.get('incidentTableBody').children[0].children[0].textContent.includes('unavailable'));
const empty = environment([], { noHeaders: true });
await settle();
assert.equal(empty.get('metricTotal').innerText, 0);
assert(!empty.get('historyNotice').textContent.includes('out of 0'));
assert(empty.get('incidentTableBody').children[0].children[0].textContent.includes('returned no recent'));
const timeout = environment([], { mode: 'never', fastTimeout: true });
await new Promise(resolve => setTimeout(resolve, 20));
assert(timeout.get('liveStatus').textContent.includes('unavailable'));
assert.equal(vm.runInContext('liveFetchInProgress', timeout.context), false);
timeout.setMode('good');
await timeout.context.refreshLiveIncidents();
assert(timeout.get('liveStatus').textContent.includes('Connected'));
const invalid = environment([], { mode: 'invalid' });
await settle();
assert(invalid.get('liveStatus').textContent.includes('unavailable'));
const invalidRow = environment([null]);
await settle();
assert.equal(invalidRow.get('metricTotal').innerText, '--');
assert(invalidRow.get('liveStatus').textContent.includes('unavailable'));
console.log('Dashboard checks passed: recent vs cumulative scope, complete references, honest timing, export scope, empty/error/stale states, timeout and recovery.');

const historyRecords = Array.from({ length: 120 }, (_, i) => ({ ...records[i % 20], id: i + 1, arrival: i + 1, rxTime: i * 1000 }));
const history = environment(historyRecords, { history: true });
await settle();
assert.equal(history.get('metricTotal').innerText, 20);
assert.equal(history.get('pageStatus').textContent, 'Page 1 of 6');
assert(history.get('historyNotice').textContent.includes('120/200 stored'));
assert.equal(history.get('incidentTableBody').children[0].children[2].textContent, 'V2#0101');
await history.context.changeHistoryPage(1);
assert.equal(history.get('pageStatus').textContent, 'Page 2 of 6');
assert(history.get('liveStatus').textContent.includes('Saved view'));
assert.equal(history.get('incidentTableBody').children[0].children[2].textContent, 'V2#0081');
await history.context.exportRetainedHistory();
const historyCSV = await history.getBlob().text();
assert.equal(historyCSV.split('\n').length, 121);
assert(historyCSV.includes('retained_history_snapshot'));
assert(historyCSV.includes('V2#0001') && historyCSV.includes('V2#0120'));
assert(history.getDownload().attributes.download.includes('Retained_History'));
history.setMode('expired');
await history.context.changeHistoryPage(1);
assert.equal(history.get('pageStatus').textContent, 'Page 2 of 6', 'Failed navigation keeps the previous page and records');
assert(history.get('liveStatus').textContent.includes('Return to latest'));
history.setMode('good');
await history.context.showLatestReports();
assert.equal(history.get('pageStatus').textContent, 'Page 1 of 6');
assert.equal(vm.runInContext('historyFrozen', history.context), false);
const interruptedExport = environment(historyRecords, { history: true, failPage: 2 });
await settle();
await interruptedExport.context.exportRetainedHistory();
assert.equal(interruptedExport.getBlob(), null, 'Never download an incomplete history export');
assert(interruptedExport.get('exportStatus').textContent.includes('No partial CSV'));
assert.equal(interruptedExport.get('exportHistoryBtn').disabled, false);
const overflowRecords = Array.from({ length: 205 }, (_, i) => ({ ...records[i % 20], id: i + 1, arrival: i + 1, rxTime: i * 1000 }));
const overflow = environment(overflowRecords, { history: true });
await settle();
assert(overflow.get('historyNotice').textContent.includes('5 older reports'));
await overflow.context.exportRetainedHistory();
assert.equal((await overflow.getBlob().text()).split('\n').length, 201);
console.log('History checks passed: 120 reports across six pages, stable snapshots, complete export, expired snapshot recovery, 200-record cap and no partial export.');

const clocked = environment(records, { clock: true });
await settle();
const clockRow = clocked.get('incidentTableBody').children[0];
assert(clockRow.children[3].textContent.includes('PHT'));
assert(clockRow.children[3].children.some(e => e.textContent === 'Delivery duration: unavailable'));
const clockDetails = clockRow.children[4].children[0].children[1].children;
assert(clockDetails.some(e => e.textContent === 'Estimated received time (PHT)'));
assert(clockDetails.some(e => /\d{4}/.test(e.textContent) && /[AP]M/.test(e.textContent)));
await clocked.context.refreshLiveIncidents();
assert.equal(clocked.get('incidentTableBody').children[0], clockRow, 'Stable clock anchor preserves unchanged DOM');
const rebootOptions = { clock: true, session: 777 };
const rebooted = environment(records, rebootOptions);
await settle();
rebootOptions.session = 778;
await rebooted.context.refreshLiveIncidents();
assert.equal(vm.runInContext('receiptClock.session', rebooted.context), 778, 'New boot replaces the previous clock anchor even with identical records');
rebootOptions.clock = false;
await rebooted.context.refreshLiveIncidents();
assert.equal(vm.runInContext('receiptClock', rebooted.context), null, 'Missing clock headers invalidate the previous estimate');

const base = Date.UTC(2026, 9, 28, 12, 45, 0);
const clock = clocked.context.makeReceiptClock(100000, 777, base, base + 200, 100, 300);
assert.equal(clock.uncertaintyMs, 100);
assert.equal(clocked.context.estimatedReceiptMs({ rxTime: 95000 }, clock), base - 4900);
assert.equal(clocked.context.estimatedReceiptMs({ rxTime: 100001 }, clock), null, 'No future receipts');
assert.equal(clocked.context.makeReceiptClock(null, 777, base, base, 0, 0), null);
assert.equal(clocked.context.makeReceiptClock(100, null, base, base, 0, 0), null);
assert.equal(clocked.context.makeReceiptClock(100, 777, base, base + 3000, 0, 3000), null, 'Reject slow clock samples');
assert.equal(clocked.context.makeReceiptClock(100, 777, base, base + 60000, 0, 100), null, 'Reject in-flight device-clock jumps');
const longClock = clocked.context.makeReceiptClock(5000000000, 778, base, base, 0, 0);
assert.equal(clocked.context.estimatedReceiptMs({ rxTime: 4999999000 }, longClock), base - 1000, '64-bit uptime survives millis wrap');
vm.runInContext('receiptClock = null', clocked.context);
clocked.context.renderTable();
assert(clocked.get('incidentTableBody').children[0].children[3].textContent.includes('after hub restart'), 'No stale clock after invalidation');
console.log('Receipt-clock checks passed: PHT estimate, full date, RTT bound, missing/invalid clocks, future receipts, 64-bit uptime and honest latency.');
