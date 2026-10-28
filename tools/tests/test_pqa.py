import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('pqa_analyzer', ROOT / 'tools/analyze_run.py')
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)


def capture(items, boot='abc', session='test'):
    rows = []
    for seq, item in enumerate(items, 1):
        event, mid, k, ms = item[:4]
        rows.append(dict(event=event, id=mid, k=k, ms=ms, node=2, origin=6,
                         type=0 if k == 1 else 2, session=session,
                         detail=f'boot={boot};seq={seq}'))
    return pd.DataFrame(rows)


class PqaAnalysis(unittest.TestCase):
    def test_fifo_inversion_not_hidden_by_duplicate_rx(self):
        df = capture([('ENQUEUE', 1, 1, 10), ('TX', 2, 3, 20),
                      ('RX', 1, 1, 25), ('DUP', 1, 1, 26), ('TX', 1, 1, 30),
                      ('TX', 1, 1, 40)])
        result = analyzer.pqa_per_message(df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0].overtaken_by, 1)
        self.assertEqual(result.iloc[0].waited_ms, 20)

    def test_heap_correct_and_same_millisecond_event_order(self):
        df = capture([('TX', 3, 3, 10), ('ENQUEUE', 1, 1, 10),
                      ('TX', 1, 1, 10), ('TX', 2, 2, 10)])
        self.assertEqual(analyzer.pqa_per_message(df).iloc[0].overtaken_by, 0)
        df = capture([('ENQUEUE', 1, 1, 10), ('TX', 2, 2, 10), ('TX', 1, 1, 10)])
        self.assertEqual(analyzer.pqa_per_message(df).iloc[0].overtaken_by, 1)

    def test_rx_or_new_alone_is_not_admission(self):
        for event in ('RX', 'NEW', 'RX_ACCEPT'):
            self.assertTrue(analyzer.pqa_per_message(capture([(event, 1, 1, 1), ('TX', 1, 1, 3)])).empty)

    def test_already_started_lower_priority_tx_logged_late_is_not_violation(self):
        result = analyzer.pqa_per_message(capture([
            ('ENQUEUE', 1, 1, 20), ('TX', 2, 3, 19), ('TX', 1, 1, 30)]))
        self.assertEqual(result.iloc[0].overtaken_by, 0)

    def test_drops_eviction_late_capture_and_unsent_excluded(self):
        for event in ('DROP', 'EVICT'):
            self.assertTrue(analyzer.pqa_per_message(capture([
                ('ENQUEUE', 1, 1, 1), (event, 1, 1, 2), ('TX', 1, 1, 3)])).empty)
        self.assertTrue(analyzer.pqa_per_message(capture([('TX', 1, 1, 3)])).empty)
        result = analyzer.pqa_per_message(capture([('ENQUEUE', 1, 1, 1)]))
        self.assertTrue(result.empty)
        self.assertEqual(result.attrs['audit'][0]['reason'], 'no_first_transmission')

    def test_gap_excludes_interval_but_later_complete_interval_works(self):
        df = capture([('ENQUEUE', 1, 1, 1), ('TX', 9, 3, 2), ('TX', 1, 1, 3),
                      ('ENQUEUE', 2, 1, 4), ('TX', 2, 1, 5)]).drop(index=1)
        result = analyzer.pqa_per_message(df)
        self.assertEqual(list(result.id), [2])
        self.assertEqual(result.attrs['audit'][0]['reason'], 'log_gap')

    def test_boot_session_origin_and_node_separate(self):
        entry = capture([('ENQUEUE', 1, 1, 1)])
        for column, value in (('session', 'other'), ('node', 3), ('origin', 5), ('detail', 'boot=def;seq=2')):
            tx = capture([('TX', 1, 1, 2)])
            tx.loc[0, 'detail'] = 'boot=abc;seq=2'
            tx.loc[0, column] = value
            self.assertTrue(analyzer.pqa_per_message(pd.concat([entry, tx])).empty)

    def test_merged_copies_conflicting_rows_and_legacy(self):
        df = capture([('ENQUEUE', 1, 1, 1), ('TX', 1, 1, 3)])
        self.assertEqual(len(analyzer.pqa_per_message(pd.concat([df, df]))), 1)
        corrupt = df.copy()
        corrupt.loc[1, 'k'] = 3
        self.assertTrue(analyzer.pqa_per_message(pd.concat([df, corrupt])).empty)
        df['detail'] = ''
        self.assertTrue(analyzer.pqa_per_message(df).empty)

    def test_wrap_and_dtn_custody_and_repeated_entry(self):
        df = capture([('ENQUEUE', 1, 1, 0xfffffff0), ('STORE', 1, 1, 0xfffffff1),
                      ('ENQUEUE', 1, 1, 0xfffffff2), ('TX', 2, 3, 1), ('TX', 1, 1, 10)])
        row = analyzer.pqa_per_message(df).iloc[0]
        self.assertEqual(row.waited_ms, 26)
        self.assertEqual(row.overtaken_by, 1)


class FirmwareQueueEvents(unittest.TestCase):
    def test_actual_queue_wrapper_for_fifo_and_heap(self):
        source = (ROOT / 'src/main.cpp').read_text(encoding='utf-8')
        start = source.index('bool queuePush(')
        end = source.index('\nbool queuePeek(', start)
        wrapper = source[start:end]
        preamble = r'''
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include "fifo_queue.h"
uint32_t millis() { return 100; }
using MessageQueue = QUEUE;
MessageQueue priorityQueue;
int priorityQueueMutex = 1;
bool lockOk = true, held = false;
constexpr int pdTRUE = 1;
int pdMS_TO_TICKS(int n) { return n; }
int xSemaphoreTake(int, int) { held = lockOk; return held; }
void xSemaphoreGive(int) { held = false; }
struct { template<class... T> void printf(const char*, T...) {} } Serial;
struct CsvEvent { const char* event; const char* detail = ""; bool hasEventTime = false; uint32_t eventMs = 0; };
CsvEvent csvEvent(const char* event, const EmergencyMessage&, int) { return {event}; }
std::vector<std::string> events;
void logCsv(const CsvEvent& e) {
    if (!strcmp(e.event, "ENQUEUE")) assert(held);
    events.emplace_back(e.event);
}
'''
        checks = r'''
int main() {
    EmergencyMessage m{}; m.id = 1; m.originNode = 6; m.priority = 3;
    lockOk = false; assert(!queuePush(m)); assert(events.back() == "DROP");
    lockOk = true; events.clear();
    for (int i = 0; i < 32; ++i) { m.id = i; assert(queuePush(m)); }
    assert(events.size() == 32);
    for (const auto& event : events) assert(event == "ENQUEUE");
    events.clear(); m.id = 50; assert(!queuePush(m));
    assert(events.size() == 1 && events[0] == "DROP");
    events.clear(); m.priority = 1;
    bool accepted = queuePush(m);
    assert(accepted == EXPECT_EVICTION);
    if (accepted) assert(events.size() == 2 && events[0] == "ENQUEUE" && events[1] == "EVICT");
    else assert(events.size() == 1 && events[0] == "DROP");
}
'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'Arduino.h').write_text('#pragma once\n#include <stdint.h>\n#include <stddef.h>\nuint32_t millis();\n')
            for queue, evicts in (('FifoQueue', 'false'), ('PriorityMinHeap', 'true')):
                cpp = path / 'test.cpp'
                cpp.write_text(preamble.replace('QUEUE', queue) + wrapper + checks.replace('EXPECT_EVICTION', evicts))
                exe = path / 'test.exe'
                subprocess.run([shutil.which('g++'), '-std=c++17', '-static', '-static-libgcc', '-static-libstdc++', '-I', str(path), '-I', str(ROOT / 'include'), str(cpp), '-o', str(exe)], check=True)
                subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    unittest.main()
