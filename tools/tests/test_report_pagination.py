"""Exercise the actual firmware page planner independently of ESP32 hardware."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_message_handling import function

ROOT = Path(__file__).resolve().parents[2]


class ReportPagination(unittest.TestCase):
    def test_actual_page_planner(self):
        compiler = shutil.which('g++')
        self.assertIsNotNone(compiler)
        firmware = (ROOT / 'src/main.cpp').read_text(encoding='utf-8')
        incident_struct = 'struct LiveIncident {' + firmware.split('struct LiveIncident {', 1)[1].split('};', 1)[0] + '};'
        ring_fixture = r'''
#include <cstdio>
#include <string>
''' + incident_struct + r'''
constexpr size_t LIVE_INCIDENT_CAPACITY = 200;
LiveIncident liveIncidents[LIVE_INCIDENT_CAPACITY]{};
size_t liveIncidentWriteIndex = 0, liveIncidentCount = 0;
uint32_t liveIncidentArrivalCounter = 0;
int liveIncidentMutex = 1;
constexpr int pdTRUE = 1, NODE_ID = 1;
bool canLock = true;
int pdMS_TO_TICKS(int value) { return value; }
int xSemaphoreTake(int, int) { return canLock; }
void xSemaphoreGive(int) {}
uint32_t millis() { return liveIncidentArrivalCounter * 1000; }
int32_t calculateIncidentLatencyMs(uint32_t, uint16_t) { return -1; }
void buildIncidentPath(uint8_t, uint16_t, char* path, size_t capacity) { snprintf(path, capacity, "V2 -> V1"); }
''' + function(firmware, 'bool recordLiveIncident(')
        code = '#include <stdint.h>\n#include <stddef.h>\n' + ring_fixture + r'''
#include <cassert>
#include <set>
#include "report_pagination.h"
int main() {
    uint32_t parsed = 0;
    assert(parseHistoryNumber("4294967295", parsed) && parsed == UINT32_MAX);
    for (auto bad : {"", "-1", "+1", " 2", "2x", "4294967296"}) assert(!parseHistoryNumber(bad, parsed));
    ReportPage out;
    assert(planReportPage(0, 200, 20, 1, 0, out) == ReportPageResult::Ok && out.length == 0 && out.pages == 1);
    assert(planReportPage(25, 200, 20, 1, 0, out) == ReportPageResult::Ok && out.offset == 5 && out.length == 20);
    assert(planReportPage(25, 200, 20, 2, 25, out) == ReportPageResult::Ok && out.offset == 0 && out.length == 5);
    assert(planReportPage(25, 200, 20, 3, 25, out) == ReportPageResult::InvalidPage);
    assert(planReportPage(25, 200, 20, 0, 0, out) == ReportPageResult::InvalidPage);
    assert(planReportPage(5, 200, 20, 1, 25, out) == ReportPageResult::ExpiredSnapshot);
    // New arrivals below capacity preserve every row of an older snapshot.
    assert(planReportPage(130, 200, 20, 6, 120, out) == ReportPageResult::Ok && out.offset == 0 && out.length == 20);
    // Once the oldest snapshot record has been overwritten, refuse to mix pages.
    assert(planReportPage(201, 200, 20, 2, 200, out) == ReportPageResult::ExpiredSnapshot);
    for (uint32_t total : {25u, 120u, 200u, 205u, 999u}) {
        std::set<uint32_t> arrivals;
        size_t retained = total < 200 ? total : 200;
        size_t pages = (retained + 19) / 20;
        for (size_t page = 1; page <= pages; ++page) {
            assert(planReportPage(total, 200, 20, page, total, out) == ReportPageResult::Ok);
            assert(out.length <= 20 && out.offset + out.length <= retained);
            for (size_t i = out.offset; i < out.offset + out.length; ++i)
                assert(arrivals.insert(total - retained + 1 + i).second);
        }
        assert(arrivals.size() == retained);
        assert(*arrivals.begin() == total - retained + 1 && *arrivals.rbegin() == total);
    }
    // Exercise real firmware insertion and physical ring wrap, not a reimplementation.
    for (uint16_t i = 1; i <= 205; ++i) {
        assert(recordLiveIncident(i, 1, 0, 2, 0, 0, 0, "Here", std::to_string(i).c_str()));
        if (i == 120) {
            assert(liveIncidentCount == 120);
            assert(planReportPage(120, 200, 20, 6, 120, out) == ReportPageResult::Ok);
            assert(liveIncidents[out.offset].messageId == 1);
        }
    }
    assert(liveIncidentCount == 200 && liveIncidentArrivalCounter == 205);
    const size_t oldest = (liveIncidentWriteIndex + 200 - liveIncidentCount) % 200;
    std::set<uint16_t> actualIds;
    for (size_t page = 1; page <= 10; ++page) {
        assert(planReportPage(205, 200, 20, page, 205, out) == ReportPageResult::Ok);
        for (size_t i = out.offset; i < out.offset + out.length; ++i) {
            const auto &row = liveIncidents[(oldest + i) % 200];
            assert(row.arrivalNo == row.messageId);
            assert(std::string(row.message) == std::to_string(row.messageId));
            assert(actualIds.insert(row.messageId).second);
        }
    }
    assert(actualIds.size() == 200 && *actualIds.begin() == 6 && *actualIds.rbegin() == 205);
    canLock = false;
    assert(!recordLiveIncident(206, 1, 0, 2, 0, 0, 0, "Here", "No lock"));
    assert(liveIncidentArrivalCounter == 205);
}
'''
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            source, executable = root / 'pages.cpp', root / 'pages.exe'
            source.write_text(code, encoding='utf-8')
            result = subprocess.run([compiler, '-std=c++17', '-static', '-static-libgcc', '-static-libstdc++',
                                     '-I', str(ROOT / 'include'), str(source), '-o', str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
