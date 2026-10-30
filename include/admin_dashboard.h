// Generated from admin.html by tools/sync_web_assets.py. Do not edit directly.
#ifndef ADMIN_DASHBOARD_H
#define ADMIN_DASHBOARD_H

#include <pgmspace.h>

const char ADMIN_DASHBOARD_HTML[] PROGMEM = R"ADMINDASHBOARD(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Barangay San Miguel - Main Emergency Command Dashboard (V1)</title>
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            padding: 16px;
            font-size: 13.5px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 14px;
            border-bottom: 1px solid #30363d;
            margin-bottom: 16px;
        }
        .header-title h1 {
            font-size: 20px;
            color: #58a6ff;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-title .subtitle {
            font-size: 12px;
            color: #8b949e;
            margin-top: 3px;
        }
        .header-badges {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 600;
        }
        .badge-mesh { background: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb; }
        .badge-crypto { background: #23863622; color: #3fb950; border: 1px solid #238636; }
        .badge-hub { background: #d2992222; color: #e3b341; border: 1px solid #d29922; }

        /* Metric Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        .metric-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px 14px;
        }
        .metric-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #8b949e;
            margin-bottom: 4px;
            font-weight: 600;
        }
        .metric-val {
            font-size: 22px;
            font-weight: 700;
            color: #f0f6fc;
        }
        .metric-val.sos { color: #f85149; }
        .metric-val.gen { color: #d29922; }
        .metric-val.rout { color: #58a6ff; }
        .metric-val.pdr { color: #3fb950; }

        /* Main 2-Column Grid */
        .main-layout {
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 16px;
        }
        @media (max-width: 900px) {
            .main-layout { grid-template-columns: 1fr; }
        }

        /* Topology & Controls Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .panel {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 14px;
        }
        .panel-header {
            font-size: 13px;
            font-weight: 700;
            color: #f0f6fc;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .node-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .node-row {
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 8px 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .node-name {
            font-weight: 600;
            color: #f0f6fc;
            font-size: 12.5px;
        }
        .node-role {
            font-size: 10.5px;
            color: #8b949e;
        }
        .node-telemetry {
            text-align: right;
            font-size: 11px;
            color: #7ee787;
        }
        .node-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }
        .dot-green { background: #3fb950; box-shadow: 0 0 6px #3fb95088; }
        .dot-yellow { background: #d29922; }
        .dot-red { background: #f85149; }

        /* Simulator controls */
        .btn-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .btn {
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            padding: 7px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s ease;
        }
        .btn:hover {
            background: #30363d;
            border-color: #8b949e;
            color: #f0f6fc;
        }
        .btn-sos {
            background: #da3633;
            color: #ffffff;
            border-color: #f85149;
        }
        .btn-sos:hover {
            background: #b62324;
        }
        .btn-export {
            background: #238636;
            color: #ffffff;
            border-color: #2ea043;
        }
        .btn-export:hover {
            background: #2ea043;
        }

        /* Message Table Section */
        .table-panel {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 14px;
            overflow-x: auto;
        }
        .table-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .filter-select {
            background: #0d1117;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 5px 8px;
            border-radius: 6px;
            font-size: 12px;
            outline: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            text-align: left;
        }
        th {
            background: #0d1117;
            color: #8b949e;
            padding: 9px 10px;
            font-weight: 600;
            border-bottom: 1px solid #30363d;
            white-space: nowrap;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #21262d;
            vertical-align: middle;
        }
        tr:hover td {
            background: #1c2128;
        }
        
        .p-badge {
            display: inline-block;
            padding: 3px 7px;
            border-radius: 4px;
            font-size: 10.5px;
            font-weight: 700;
            white-space: nowrap;
        }
        .p-sos { background: #f8514922; color: #ff7b72; border: 1px solid #f85149; }
        .p-gen { background: #d2992222; color: #e3b341; border: 1px solid #d29922; }
        .p-rout { background: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb; }

        .route-tag {
            font-family: monospace;
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #30363d;
            color: #79c0ff;
            font-size: 11px;
        }
        .latency-tag {
            font-weight: 600;
            color: #3fb950;
        }
        .crypto-tag {
            color: #7ee787;
            font-size: 10.5px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .msg-text {
            color: #f0f6fc;
            max-width: 260px;
            word-break: break-word;
        }
        .loc-text {
            color: #8b949e;
            font-size: 11px;
        }
        /* Emergency-first dashboard layout */
        body { background: radial-gradient(ellipse at top left, #162235 0, #0b1220 55%); color: #e6edf6; padding: clamp(14px, 2.4vw, 30px); }
        header { border-color: #273449; gap: 14px; flex-wrap: wrap; }
        .header-title h1 { color: #f4f7fb; font-size: clamp(21px, 2.2vw, 28px); }
        .badge { padding: 6px 11px; }
        .metrics-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 16px 0; }
        .metric-card { background: #111b2b; border-color: #26364d; border-radius: 12px; padding: 14px 16px; }
        .metric-card-sos { background: linear-gradient(145deg, #3b171e, #21151e); border-color: #a8313a; box-shadow: inset 3px 0 #ff5b62; }
        .metric-card-sos .metric-val { font-size: 28px; }
        .main-layout { grid-template-columns: minmax(0, 1fr); grid-template-areas: "incidents"; gap: 14px; }
        .table-panel { grid-area: incidents; background: #101a29; border-color: #26364d; border-radius: 12px; }
        .panel { background: #101a29; border-color: #26364d; border-radius: 12px; }
        .priority-alert { display: flex; align-items: flex-start; gap: 15px; margin: 16px 0; padding: 18px 20px; border: 1px solid #2e6848; border-left: 5px solid #3fb950; border-radius: 12px; background: #10251d; }
        .priority-alert.has-sos { border-color: #8f3039; border-left-color: #ff4d57; background: linear-gradient(110deg, #35171d, #241923); }
        .priority-alert-icon { flex: 0 0 38px; height: 38px; display: grid; place-items: center; border-radius: 50%; background: #1d6b3c; color: #fff; font-size: 22px; font-weight: 800; }
        .has-sos .priority-alert-icon { background: #d93643; }
        .priority-alert-label { color: #a7b7ca; font-size: 11px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
        .priority-alert h2 { margin: 3px 0 5px; color: #fff; font-size: clamp(18px, 2vw, 24px); }
        .priority-alert p { color: #c5d0de; line-height: 1.5; }
        .priority-alert-list { display: grid; gap: 7px; margin-top: 12px; padding-left: 18px; color: #fff; }
        .priority-alert-list li { line-height: 1.45; overflow-wrap: anywhere; }
        .priority-alert.is-clear .priority-alert-list { display: none; }
        .priority-alert.is-clear #sosSummary { margin: 0; }
        .metric-card, .panel, .table-panel { box-shadow: 0 8px 24px #0002; }
        .panel-header { font-size: 14px; }
        th { position: sticky; top: 0; z-index: 1; background: #172337; }
        .priority-row-sos td { background: #31191f; }
        .priority-row-sos td:first-child { border-left: 3px solid #ff4d57; }
        @media (max-width: 900px) {
            .metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .main-layout { grid-template-columns: minmax(0, 1fr); grid-template-areas: "incidents"; }
        }
        @media (max-width: 480px) {
            .metrics-grid { grid-template-columns: 1fr 1fr; }
            .priority-alert { padding: 14px; gap: 10px; }
            .priority-alert-icon { flex-basis: 32px; height: 32px; }
            .header-badges { flex-wrap: wrap; }
        }
        /* Five readable columns on laptops; labelled report cards on phones. */
        body { font-size: 16px; line-height: 1.5; }
        .table-panel { overflow: visible; min-width: 0; }
        .report-tools { display: flex; align-items: end; flex-wrap: wrap; gap: 12px; }
        .report-tools label { display: grid; gap: 4px; color: #c5d0de; font-size: 14px; }
        .filter-select, .btn { font-size: 14px; min-height: 44px; }
        .filter-select:focus-visible, .btn:focus-visible, summary:focus-visible { outline: 3px solid #79c0ff; outline-offset: 3px; }
        #liveStatus { display: block; margin: 10px 0; overflow-wrap: anywhere; }
        table { table-layout: fixed; font-size: 15px; }
        th, td { padding: 14px 10px; vertical-align: top; overflow-wrap: anywhere; }
        th { white-space: normal; position: static; }
        th:nth-child(1) { width: 16%; } th:nth-child(2) { width: 37%; }
        th:nth-child(3) { width: 16%; } th:nth-child(4) { width: 15%; } th:nth-child(5) { width: 16%; }
        .p-badge { font-size: 13px; white-space: normal; }
        .loc-text { font-size: 16px; color: #f0f6fc; font-weight: 750; margin-bottom: 6px; }
        .msg-text { max-width: none; font-size: 16px; white-space: pre-wrap; }
        .report-ref { font-weight: 700; color: #79c0ff; }
        .receipt-note, .technical-note { color: #aeb9c7; font-size: 13px; }
        .report-details summary { cursor: pointer; color: #79c0ff; padding: 4px 0; min-height: 44px; }
        .report-details dl { font-size: 13px; margin-top: 8px; }
        .report-details dt { color: #aeb9c7; margin-top: 8px; }
        .report-details dd { margin: 0; overflow-wrap: anywhere; color: #e6edf6; }
        @media (max-width: 760px) {
            body { padding: 12px; }
            .table-panel { padding: 12px; }
            table, tbody, tr, td { display: block; width: 100%; }
            thead { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip-path: inset(50%); }
            tbody tr { border: 1px solid #34445b; border-radius: 8px; margin: 14px 0; overflow: hidden; }
            td { border: 0; padding: 9px 12px; }
            td[data-label]::before { content: attr(data-label); display: block; font-size: 12px; font-weight: 700; color: #aeb9c7; margin-bottom: 3px; }
            .priority-row-sos { border-left: 4px solid #ff4d57; }
            .priority-row-sos td:first-child { border-left: 0; }
            .report-tools { width: 100%; }
            .report-tools label { flex: 1 1 160px; }
            .report-tools select { width: 100%; }
            .metric-card { padding: 12px; }
        }
    </style>
</head>
<body>

    <header>
        <div class="header-title">
            <h1>Main Hub Dashboard</h1>
            <div class="subtitle">Barangay San Miguel</div>
        </div>
        <div class="header-badges">
            <span class="badge badge-hub">Main hub V1</span>
        </div>
    </header>

    <section id="sosAlert" class="priority-alert" aria-live="polite" aria-atomic="true">
        <div class="priority-alert-icon" aria-hidden="true">!</div>
        <div>
            <div class="priority-alert-label">Medical reports</div>
            <h2 id="sosTitle">Checking recent reports...</h2>
            <p id="sosSummary">Waiting for hub data.</p>
            <ul id="sosList" class="priority-alert-list"></ul>
        </div>
    </section>

    <!-- Top Statistical Metrics (Chapter 4 Thesis Validation) -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Reports on this page</div>
            <div class="metric-val" id="metricTotal">--</div>
        </div>
        <div class="metric-card metric-card-sos">
            <div class="metric-label">Medical (this page)</div>
            <div class="metric-val sos" id="metricSOS">--</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">General (this page)</div>
            <div class="metric-val gen" id="metricGen">--</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Routine (this page)</div>
            <div class="metric-val rout" id="metricRout">--</div>
        </div>
    </div>

    <div class="main-layout">
        <div class="table-panel">
            <div class="table-controls">
                <div class="panel-header" style="margin:0;">
                    <span>Received reports</span>
                </div>
                <div class="report-tools">
                    <label for="sortOrder">Sort reports
                    <select id="sortOrder" class="filter-select" onchange="renderTable()">
                        <option value="arrival">Oldest first</option>
                        <option value="newest">Newest first</option>
                        <option value="priority">Medical first</option>
                    </select>
                    </label>
                    <label for="priorityFilter">Show category
                    <select id="priorityFilter" class="filter-select" onchange="renderTable()">
                        <option value="all">All categories</option>
                        <option value="1">Medical SOS</option>
                        <option value="2">General emergency</option>
                        <option value="3">Routine update</option>
                    </select>
                    </label>
                    <button type="button" class="btn btn-export" onclick="exportToCSV()">Export this page</button>
                    <button type="button" id="exportHistoryBtn" class="btn btn-export" onclick="exportRetainedHistory()">Export retained history</button>
                </div>
            </div>

            <span id="liveStatus" role="status">Connecting</span>
            <nav class="report-tools" aria-label="Report history pages">
                <button type="button" class="btn" id="newerPageBtn" onclick="changeHistoryPage(-1)" disabled>Newer page</button>
                <span id="pageStatus" role="status">Page unavailable</span>
                <button type="button" class="btn" id="olderPageBtn" onclick="changeHistoryPage(1)" disabled>Older page</button>
                <button type="button" class="btn" id="latestPageBtn" onclick="showLatestReports()">Latest / refresh</button>
            </nav>
            <p id="exportStatus" role="status" class="technical-note"></p>
            <p id="historyNotice" style="margin:12px 0; color:#aeb9c7; line-height:1.5;">Loading history...</p>
            <details class="report-details" style="margin:10px 0;">
                <summary>History &amp; timing notes</summary>
                <p class="technical-note">History clears on restart. Counts, filters and sorting apply to this page only. Keep complete research records through USB logging.</p>
                <p class="technical-note" id="timingNotice">Clock times are device-clock estimates in Philippine time (PHT). Without a clock reference, hub uptime is shown. Delivery timing requires verified paired logs.</p>
            </details>
            <table aria-label="Recent reports received at the main hub">
                <thead>
                    <tr>
                        <th scope="col">Category</th>
                        <th scope="col">Location &amp; report</th>
                        <th scope="col">Reference</th>
                        <th scope="col">Received at hub</th>
                        <th scope="col">Technical details</th>
                    </tr>
                </thead>
                <tbody id="incidentTableBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        let incidentLogs = [];
        let liveFetchInProgress = false;
        let hasLiveData = false;
        let lastLiveUpdateMs = null;
        let recentLimit = null;
        let recordedSinceBoot = null;
        const openReportDetails = new Set();
        let historyPage = 1, historyPages = 1, historySnapshot = null, historySession = null;
        let historyFrozen = false, historyCapacity = null, historyRetained = null;
        let historyExportActive = false;
        let receiptClock = null;

        function monotonicNow() {
            return typeof performance !== 'undefined' ? performance.now() : Date.now();
        }

        function makeReceiptClock(uptimeMs, session, wallStart, wallEnd, monoStart, monoEnd) {
            const rttMs = monoEnd - monoStart;
            if (!Number.isSafeInteger(uptimeMs) || uptimeMs < 0 ||
                !Number.isSafeInteger(session) || session < 0 || session > 4294967295 ||
                !Number.isFinite(wallStart) || !Number.isFinite(wallEnd) ||
                !Number.isFinite(rttMs) || rttMs < 0 || rttMs > 2000 ||
                Math.abs((wallEnd - wallStart) - rttMs) > 1000) return null;
            // The server sampled uptime somewhere inside this request's round trip.
            return { session, uptimeMs, epochMs: (wallStart + wallEnd) / 2, uncertaintyMs: rttMs / 2 };
        }

        function estimatedReceiptMs(report, clock = receiptClock) {
            if (!clock || !Number.isSafeInteger(report.rxTime) || report.rxTime < 0 || report.rxTime > clock.uptimeMs) return null;
            const epoch = clock.epochMs - (clock.uptimeMs - report.rxTime);
            return Number.isFinite(epoch) && Math.abs(epoch) <= 8640000000000000 ? epoch : null;
        }

        function receiptTimeText(report, full = false) {
            const epoch = estimatedReceiptMs(report);
            if (epoch == null) return null;
            const options = { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit', hour12: true };
            if (full) Object.assign(options, { year: 'numeric', month: 'short', day: 'numeric', second: '2-digit' });
            return new Date(epoch).toLocaleString('en-PH', options);
        }

        function updateMetrics() {
            const emergencies = incidentLogs.filter(m => m.packetType !== 1 && m.packetType !== 3);
            const total = emergencies.length;
            const k1 = emergencies.filter(m => m.priority === 1).length;
            const k2 = emergencies.filter(m => m.priority === 2).length;
            const k3 = emergencies.filter(m => m.priority === 3).length;

            document.getElementById('metricTotal').innerText = total;
            document.getElementById('metricSOS').innerText = k1;
            document.getElementById('metricGen').innerText = k2;
            document.getElementById('metricRout').innerText = k3;

            updateEmergencyNotice();
        }

        function updateEmergencyNotice() {
            const reports = incidentLogs
                .filter(m => m.priority === 1)
                .sort((a, b) => Number(b.arrival != null ? b.arrival : b.rxTime) - Number(a.arrival != null ? a.arrival : a.rxTime));
            const alert = document.getElementById('sosAlert');
            const list = document.getElementById('sosList');
            list.textContent = '';
            alert.classList.toggle('has-sos', reports.length > 0);
            alert.classList.toggle('is-clear', reports.length === 0);
            document.getElementById('sosTitle').textContent = reports.length
                ? `${reports.length} on this page`
                : 'None on this page';
            document.getElementById('sosSummary').textContent = reports.length
                ? `Latest ${Math.min(reports.length, 3)} below. Not an unresolved-case count.`
                : 'No received medical reports on this page. Not a case-status tracker.';
            reports.slice(0, 3).forEach(report => {
                const item = document.createElement('li');
                item.textContent = `${report.origin || `V${report.originNode}`}#${String(report.id).padStart(4, '0')} · ${report.location} — ${report.message}`;
                list.appendChild(item);
            });
        }

        function renderTable() {
            const filter = document.getElementById('priorityFilter').value;
            const tbody = document.getElementById('incidentTableBody');
            tbody.replaceChildren();
            const sortOrder = document.getElementById('sortOrder').value;
            // Arrival number from the hub (1 = first received); older firmware: fall back to receive time.
            const arrivalOf = m => m.arrival != null ? Number(m.arrival) : Number(m.rxTime);
            // Seconds after the previous message to arrive (computed over ALL messages, before filtering).
            const byArrival = incidentLogs.slice().sort((a, b) => arrivalOf(a) - arrivalOf(b));
            const gapSeconds = new Map();
            byArrival.forEach((m, i) => {
                if (i > 0) gapSeconds.set(m, (Number(m.rxTime) - Number(byArrival[i - 1].rxTime)) / 1000);
            });
            const comparators = {
                arrival: (a, b) => arrivalOf(a) - arrivalOf(b),
                newest: (a, b) => arrivalOf(b) - arrivalOf(a),
                priority: (a, b) => a.priority - b.priority || arrivalOf(a) - arrivalOf(b)
            };
            const filtered = incidentLogs.filter(m => filter === 'all' || m.priority == filter)
                .sort(comparators[sortOrder] || comparators.arrival);

            if (filtered.length === 0) {
                const row = document.createElement('tr');
                const cell = document.createElement('td');
                cell.colSpan = 5;
                cell.style.cssText = 'text-align:center; padding:24px; color:#8b949e;';
                cell.textContent = !hasLiveData ? 'Hub records are unavailable. Check the connection and sign-in.'
                    : incidentLogs.length ? 'No recent reports match this filter.' : 'The hub returned no recent report records.';
                row.appendChild(cell);
                tbody.appendChild(row);
                return;
            }

            const retainedKeys = new Set(incidentLogs.map(m => `${m.originNode}:${m.id}:${m.arrival}:${m.rxTime}`));
            for (const key of openReportDetails) if (!retainedKeys.has(key)) openReportDetails.delete(key);
            filtered.forEach(m => {
                const tr = document.createElement('tr');
                if (m.priority === 1) tr.className = 'priority-row-sos';
                const priorityCell = document.createElement('td');
                priorityCell.setAttribute('data-label', 'Category');
                const priorityBadge = document.createElement('span');
                priorityBadge.className = `p-badge ${m.priority === 1 ? 'p-sos' : m.priority === 2 ? 'p-gen' : 'p-rout'}`;
                priorityBadge.textContent = m.priority === 1 ? 'Medical SOS' : m.priority === 2 ? 'General emergency' : 'Routine update';
                priorityCell.appendChild(priorityBadge);

                const typeNames = ['SOS', 'HEARTBEAT', 'TELEMETRY', 'ACK'];
                const receivedSeconds = Number(m.rxTime) / 1000;
                const latencyMs = m.latencyMs == null ? NaN : Number(m.latencyMs);
                const gap = gapSeconds.get(m);
                const addCell = (label, className, text) => {
                    const cell = document.createElement('td');
                    cell.setAttribute('data-label', label);
                    cell.className = className || '';
                    if (text != null) cell.textContent = text;
                    tr.appendChild(cell);
                    return cell;
                };
                tr.appendChild(priorityCell);
                const reportCell = addCell('Location & report');
                const location = document.createElement('div');
                location.className = 'loc-text';
                location.textContent = m.location || 'Location not specified';
                const message = document.createElement('div');
                message.className = 'msg-text';
                message.textContent = m.message || '';
                reportCell.append(location, message);
                addCell('Reference', 'report-ref', `${m.origin || `V${m.originNode}`}#${String(m.id).padStart(4, '0')}`);
                const clockTime = receiptTimeText(m);
                const receipt = addCell('Received at hub', '', clockTime ? `~ ${clockTime} PHT` : Number.isFinite(receivedSeconds)
                    ? `${receivedSeconds.toFixed(1)} s after hub restart` : 'Time unavailable');
                const arrival = document.createElement('div');
                arrival.className = 'receipt-note';
                arrival.textContent = m.arrival != null ? `Arrival #${m.arrival}` : 'Arrival number unavailable';
                receipt.appendChild(arrival);
                const duration = document.createElement('div');
                duration.className = 'receipt-note';
                duration.textContent = 'Delivery duration: unavailable';
                receipt.appendChild(duration);
                const technicalCell = addCell('Technical details');
                const details = document.createElement('details');
                details.className = 'report-details';
                const key = `${m.originNode}:${m.id}:${m.arrival}:${m.rxTime}`;
                details.open = openReportDetails.has(key);
                details.addEventListener('toggle', () => {
                    if (details.open) openReportDetails.add(key); else openReportDetails.delete(key);
                });
                const summary = document.createElement('summary');
                summary.textContent = 'View details';
                const list = document.createElement('dl');
                const technical = [
                    ['Estimated received time (PHT)', receiptTimeText(m, true) || 'Unavailable — no clock reference'],
                    ['Time source', clockTime ? `Device-clock estimate; network uncertainty ±${Math.ceil(receiptClock.uncertaintyMs)} ms. Device clock and hub drift are not verified.` : 'Hub uptime only'],
                    ['Delivery duration', 'Unavailable — requires synchronized send/receive logs'],
                    ['Origin node', m.origin || `V${m.originNode}`],
                    ['Radio path', m.route || 'Unavailable'],
                    ['Packet type', typeNames[m.packetType] || 'UNKNOWN'],
                    ['Security', m.crypto || 'Not supplied'],
                    ['Clock difference (unverified)', Number.isFinite(latencyMs) && latencyMs >= 0 ? `${(latencyMs / 1000).toFixed(2)} s — not verified delivery delay` : 'Unavailable'],
                    ['Gap from preceding retained arrival', gap != null && gap >= 0 ? `${gap.toFixed(1)} s — not delivery delay` : 'Unavailable']
                ];
                technical.forEach(([label, value]) => {
                    const dt = document.createElement('dt'); dt.textContent = label;
                    const dd = document.createElement('dd'); dd.textContent = value;
                    list.append(dt, dd);
                });
                details.append(summary, list);
                technicalCell.appendChild(details);
                tbody.appendChild(tr);
            });
        }

        function exportToCSV(records = incidentLogs, scope = 'page_view_only', context = { session: historySession, snapshot: historySnapshot }) {
            if (records.length === 0) {
                alert("No received messages are available to export.");
                return;
            }
            const csvCell = value => {
                let text = String(value == null ? '' : value);
                if (typeof value === 'string' && /^[=+\-@\t\r]/.test(text)) text = "'" + text;
                return `"${text.replace(/"/g, '""')}"`;
            };
            const rows = [["Scope", "Hub_Session", "History_Snapshot", "Reference", "Arrival_No", "Message_ID", "Priority", "Packet_Type", "Origin_Node", "Path", "Unverified_Clock_Difference_ms", "Security", "Location", "Message", "Rx_Uptime_ms"]];
            records.forEach(m => {
                const packetType = ["SOS", "HEARTBEAT", "TELEMETRY", "ACK"][m.packetType] || "UNKNOWN";
                rows.push([scope, context.session, context.snapshot, `${m.origin || `V${m.originNode}`}#${String(m.id).padStart(4, '0')}`, m.arrival, m.id, m.priority, packetType, m.origin, m.route,
                    m.latencyMs, m.crypto, m.location, m.message, m.rxTime]);
            });

            const csv = rows.map(row => row.map(csvCell).join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `Brgy_San_Miguel_${scope === 'page_view_only' ? 'Page_Reports' : 'Retained_History'}_${Date.now()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        }

        async function readHistoryPage(page, snapshot = null, session = null) {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 8000);
            try {
                const query = `?page=${page}` + (snapshot == null ? '' : `&snapshot=${snapshot}&session=${session}`);
                const wallStart = Date.now(), monoStart = monotonicNow();
                const response = await fetch('/api/live_incidents' + query, { cache: 'no-store', signal: controller.signal });
                const wallEnd = Date.now(), monoEnd = monotonicNow();
                if (!response.ok) throw new Error(response.status === 409 ? 'History expired or hub restarted. Return to latest reports.' : `HTTP ${response.status}`);
                const records = await response.json();
                if (!Array.isArray(records) || records.some(m => !m ||
                    !Number.isInteger(m.originNode) || m.originNode < 1 || m.originNode > 6 ||
                    !Number.isInteger(m.id) || m.id < 0 || m.id > 65535 ||
                    !Number.isInteger(m.priority) || m.priority < 1 || m.priority > 3 ||
                    !Number.isFinite(m.rxTime) || m.rxTime < 0)) {
                    throw new Error('Invalid live incident response');
                }
                const headerNumber = name => {
                    const raw = response.headers.get(name);
                    return raw != null && /^\d+$/.test(raw) ? Number(raw) : null;
                };
                const meta = {
                    limit: headerNumber('X-Recent-Limit'), total: headerNumber('X-Recorded-Since-Boot'),
                    capacity: headerNumber('X-History-Capacity'), retained: headerNumber('X-History-Retained'),
                    pages: headerNumber('X-History-Pages'), snapshot: headerNumber('X-History-Snapshot'),
                    session: headerNumber('X-Hub-Session')
                };
                if (meta.capacity != null && (!Object.values(meta).every(Number.isSafeInteger) ||
                    meta.capacity < 1 || meta.limit < 1 || meta.session < 0 || meta.session > 4294967295 ||
                    meta.pages !== Math.max(1, Math.ceil(meta.retained / meta.limit)) || meta.pages < page ||
                    meta.retained !== Math.min(meta.snapshot, meta.capacity) || meta.total < meta.snapshot ||
                    records.length !== Math.min(meta.limit, meta.retained - (page - 1) * meta.limit) ||
                    records.some(m => !Number.isInteger(m.arrival) || m.arrival > meta.snapshot - (page - 1) * meta.limit ||
                        m.arrival < meta.snapshot - (page - 1) * meta.limit - records.length + 1) ||
                    new Set(records.map(m => m.arrival)).size !== records.length ||
                    (snapshot != null && (meta.snapshot !== snapshot || meta.session !== session)))) {
                    throw new Error('Invalid history pagination metadata');
                }
                const clock = makeReceiptClock(headerNumber('X-Hub-Uptime-Ms'), meta.session, wallStart, wallEnd, monoStart, monoEnd);
                return { records, meta, clock };
            } finally {
                clearTimeout(timer);
            }
        }

        function changeHistoryPage(delta) {
            const target = historyPage + delta;
            if (!hasLiveData || historySnapshot == null || target < 1 || target > historyPages) return;
            return refreshLiveIncidents(target, historySnapshot, historySession);
        }

        function showLatestReports() { return refreshLiveIncidents(1); }

        async function exportRetainedHistory() {
            if (historyExportActive) return;
            historyExportActive = true;
            const button = document.getElementById('exportHistoryBtn');
            const status = document.getElementById('exportStatus');
            button.disabled = true;
            status.textContent = 'Reading retained history...';
            try {
                const first = await readHistoryPage(1);
                if (first.meta.capacity == null) throw new Error('This firmware does not support complete retained-history export.');
                const records = first.records.slice();
                for (let page = 2; page <= first.meta.pages; page++) {
                    const next = await readHistoryPage(page, first.meta.snapshot, first.meta.session);
                    records.push(...next.records);
                }
                if (records.length !== first.meta.retained || new Set(records.map(m => m.arrival)).size !== records.length) {
                    throw new Error('Incomplete or duplicate history. No partial CSV was downloaded.');
                }
                if (!records.length) { status.textContent = 'No retained reports to export.'; return; }
                records.sort((a, b) => a.arrival - b.arrival);
                exportToCSV(records, 'retained_history_snapshot', first.meta);
                status.textContent = `Exported ${records.length} reports. History clears on restart; keep USB logs.`;
            } catch (error) {
                status.textContent = `Export failed: ${error.message} No partial CSV was downloaded.`;
            } finally {
                button.disabled = false;
                historyExportActive = false;
            }
        }

        async function refreshLiveIncidents(page = 1, snapshot = null, session = null) {
            if (liveFetchInProgress) return;
            liveFetchInProgress = true;
            for (const id of ['newerPageBtn', 'olderPageBtn', 'latestPageBtn']) document.getElementById(id).disabled = true;
            const status = document.getElementById('liveStatus');
            try {
                const { records, meta, clock } = await readHistoryPage(page, snapshot, session);
                // A stable anchor keeps unchanged rows from jumping on every poll.
                const clockChanged = (!receiptClock !== !clock) || (clock && receiptClock && clock.session !== receiptClock.session);
                if (clockChanged || !receiptClock) receiptClock = clock;
                if (receiptClock && records.some(m => m.rxTime > receiptClock.uptimeMs)) receiptClock = clock;
                const recordsChanged = clockChanged || !hasLiveData || JSON.stringify(records) !== JSON.stringify(incidentLogs);
                incidentLogs = records;
                hasLiveData = true;
                lastLiveUpdateMs = Date.now();
                recentLimit = meta.limit;
                recordedSinceBoot = meta.total;
                historyPage = page; historyPages = meta.pages || 1;
                historySnapshot = meta.snapshot; historySession = meta.session;
                historyCapacity = meta.capacity; historyRetained = meta.retained;
                historyFrozen = snapshot != null;
                document.getElementById('newerPageBtn').disabled = page <= 1;
                document.getElementById('olderPageBtn').disabled = page >= historyPages;
                document.getElementById('pageStatus').textContent = `Page ${page} of ${historyPages}`;
                status.textContent = `${historyFrozen ? 'Saved view · Latest / refresh to resume' : 'Connected · Live view'} · ${new Date(lastLiveUpdateMs).toLocaleTimeString()}`;
                status.style.color = '#3fb950';
                document.getElementById('historyNotice').textContent = `${records.length} on this page` +
                    (recordedSinceBoot == null ? '' : ` · ${recordedSinceBoot} received since restart`) +
                    (historyCapacity == null ? ' · Pagination unavailable.' : ` · ${historyRetained}/${historyCapacity} stored in this view · ${recentLimit}/page.`) +
                    (historyCapacity != null && recordedSinceBoot > historyCapacity ? ` ${recordedSinceBoot - historyCapacity} older reports replaced.` : '') +
                    ' History clears on restart.';
                if (recordsChanged) {
                    updateMetrics();
                    renderTable();
                }
            } catch (error) {
                status.textContent = hasLiveData
                    ? `Update unavailable · ${error.message} · showing saved view from ${new Date(lastLiveUpdateMs).toLocaleTimeString()}`
                    : 'Hub records unavailable · check connection and sign-in';
                status.style.color = '#ff7b72';
                if (!hasLiveData) {
                    document.getElementById('sosTitle').textContent = 'Recent reports unavailable';
                    document.getElementById('sosSummary').textContent = 'An unavailable connection does not mean that no reports were received.';
                    renderTable();
                }
            } finally {
                liveFetchInProgress = false;
                document.getElementById('newerPageBtn').disabled = !hasLiveData || historyPage <= 1;
                document.getElementById('olderPageBtn').disabled = !hasLiveData || historyPage >= historyPages;
                document.getElementById('latestPageBtn').disabled = false;
            }
        }

        refreshLiveIncidents();
        setInterval(() => { if (!historyFrozen) refreshLiveIncidents(); }, 3000);
    </script>
</body>
</html>
)ADMINDASHBOARD";

#endif
