"""Host checks of actual firmware submit logic and actual queue/policy headers.

Hardware, radio, cryptography and dashboard storage are controlled test doubles;
the firmware submission function and queue implementations are not reimplemented.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class MessageHandling(unittest.TestCase):
    def test_real_submission_queues_and_failure_policy(self):
        compiler = shutil.which('g++')
        self.assertIsNotNone(compiler, 'A host C++ compiler is required for these firmware logic checks')
        source = (ROOT / 'src' / 'main.cpp').read_text(encoding='utf-8')
        submit = function(source, 'SubmitResult submitOwnMessage(')
        enum = re.search(r'enum SubmitResult[^;]+;', source).group(0)
        code = r'''
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include "min_heap.h"
#include "fifo_queue.h"
#include "packet_codec.h"
#include "delivery_policy.h"
uint32_t fakeNow = 100;
uint32_t millis() { return fakeNow; }
uint8_t NODE_ID = 1;
constexpr uint8_t HUB_NODE_ID = 1, INITIAL_TTL = 15, MAX_AP_CLIENTS = 10;
constexpr uint32_t DTN_RETENTION_MS = 100000;
bool queueResult = true, dashboardResult = true;
int pushes = 0, incidents = 0, seen = 0;
uint16_t nextId = 0;
std::vector<std::string> events;
struct SerialStub { template<class... T> void printf(const char*, T...) {} void println(const char*) {} } Serial;
struct WifiStub { int softAPgetStationNum() { return 0; } } WiFi;
struct CsvEvent { const char* event; uint16_t bytes = 0; const char* detail = nullptr; };
CsvEvent csvEvent(const char* name, const EmergencyMessage&, uint8_t) { return CsvEvent{name}; }
void logCsv(const CsvEvent& e) { events.emplace_back(e.event); }
uint16_t allocateMessageId() { return ++nextId; }
uint64_t epochNowMs() { return 0; }
bool queuePush(const EmergencyMessage&) { ++pushes; return queueResult; }
size_t queueSize() { return 0; }
void seenListAdd(uint8_t, uint16_t) { ++seen; }
bool recordLiveIncident(uint16_t, uint8_t, uint8_t, uint8_t, uint16_t, uint32_t, uint16_t, const char*, const char*) {
    ++incidents; return dashboardResult;
}
namespace AESCrypto {
bool encrypt(const uint8_t*, size_t, uint8_t*, size_t& length, size_t) { length = 16; return true; }
}
'''
        code += '\n' + enum + '\n' + submit
        code += '\n' + function(source, 'void appendPathNode(') + '\n' + function(source, 'void buildIncidentPath(')
        code += r'''
char adminPassword[65] = {};
int adminAccessMux = 0;
#define portENTER_CRITICAL(x) ((void)0)
#define portEXIT_CRITICAL(x) ((void)0)
struct AsyncWebServerRequest {
    int status = 0, challenges = 0, authCalls = 0;
    bool credentialMatches = false;
    void send(int code, const char*, const char*) { status = code; }
    bool authenticate(const char* user, const char* password) {
        ++authCalls; assert(std::string(user) == "admin");
        assert(std::string(password) == std::string(adminPassword));
        return credentialMatches;
    }
    void requestAuthentication(const char*) { ++challenges; }
};
'''
        code += '\n' + function(source, 'bool validAdminPassword(') + '\n' + function(source, 'bool authorizeAdmin(')
        code += r'''
void reset() { pushes = incidents = seen = 0; events.clear(); queueResult = dashboardResult = true; }
template<class Queue> void checkQueue() {
    Queue queue;
    EmergencyMessage evicted{};
    for (uint16_t id = 1; id <= 32; ++id) {
        EmergencyMessage message{}; message.id = id; message.originNode = 2; message.priority = 2;
        assert(queue.push(message, evicted) == Queue::PUSH_OK);
    }
    EmergencyMessage before{}, after{};
    assert(queue.peek(before));
    for (uint16_t id = 1; id <= 32; ++id) assert(queue.noteFailedHop(id, 2) == 1);
    assert(queue.noteFailedHop(1, 2) == 2);
    assert(queue.noteFailedHop(1, 2) == 3);
    assert(queue.noteFailedHop(1, 3) == 255); // same ID, wrong origin
    assert(queue.peek(after));
    assert(before.id == after.id && before.arrivalSeq == after.arrivalSeq && before.enqueuedAtMs == after.enqueuedAtMs);
    assert(after.failedHopAttempts == 3);
    assert(queue.removeById(1, 2));
    assert(queue.noteFailedHop(1, 2) == 255);
    EmergencyMessage message{}; message.id = 1; message.originNode = 2; message.priority = 2;
    assert(queue.push(message, evicted) == Queue::PUSH_OK);
    assert(queue.noteFailedHop(1, 2) == 1); // no stale failure state after removal
}
int main() {
    EmergencyMessage message{};
    reset(); NODE_ID = 1; queueResult = false;
    assert(submitOwnMessage(3, 0, 0, "Here", "Help", "web", message) == SUBMIT_OK);
    assert(incidents == 1 && pushes == 0 && seen == 1);
    assert(events == std::vector<std::string>({"NEW", "DELIVER"}));
    auto first = message.id;
    assert(submitOwnMessage(3, 0, 0, "Here", "Help", "web", message) == SUBMIT_OK);
    assert(message.id != first && pushes == 0 && incidents == 2);
    reset(); dashboardResult = false;
    assert(submitOwnMessage(3, 0, 0, "Here", "Help", "web", message) == SUBMIT_HUB_BUSY);
    assert(events.empty() && pushes == 0 && seen == 0);
    reset(); NODE_ID = 2;
    assert(submitOwnMessage(3, 0, 0, "Here", "Help", "web", message) == SUBMIT_OK);
    assert(pushes == 1 && incidents == 0 && events == std::vector<std::string>({"NEW"}));
    reset(); queueResult = false;
    assert(submitOwnMessage(3, 0, 0, "Here", "Help", "web", message) == SUBMIT_QUEUE_FULL);
    assert(events.empty() && incidents == 0 && seen == 0);
    reset(); NODE_ID = 1;
    assert(submitOwnMessage(3, 0, 0, "Here", "", "web", message) == SUBMIT_BAD_SIZE);
    assert(incidents == 0 && pushes == 0);
    std::string location83(83, 'L'), message117(117, 'M');
    assert(submitOwnMessage(3, 0, 0, location83.c_str(), message117.c_str(), "web", message) == SUBMIT_OK);
    assert(std::string(message.location) == location83 && std::string(message.payload) == message117);
    assert(submitOwnMessage(3, 0, 0, std::string(84, 'L').c_str(), "Help", "web", message) == SUBMIT_BAD_SIZE);
    assert(submitOwnMessage(3, 0, 0, location83.c_str(), std::string(118, 'M').c_str(), "web", message) == SUBMIT_BAD_SIZE);
    std::string unicodeLocation;
    for (int n = 0; n < 41; ++n) unicodeLocation += "\xc3\xb1";
    unicodeLocation += 'L';
    assert(unicodeLocation.size() == 83);
    assert(submitOwnMessage(3, 0, 0, unicodeLocation.c_str(), message117.c_str(), "web", message) == SUBMIT_OK);
    assert(std::string(message.location) == unicodeLocation);
    unicodeLocation += 'L';
    assert(submitOwnMessage(3, 0, 0, unicodeLocation.c_str(), "Help", "web", message) == SUBMIT_BAD_SIZE);
    char path[64]; buildIncidentPath(1, 0, path, sizeof(path)); assert(std::string(path) == "V1");
    buildIncidentPath(2, 0, path, sizeof(path)); assert(std::string(path) == "V2 -> V1");
    assert(noDtnFailureAction(false, 0, 3) == NoDtnAction::DropNoRoute);
    assert(noDtnFailureAction(true, 1, 3) == NoDtnAction::Retry);
    assert(noDtnFailureAction(true, 2, 3) == NoDtnAction::Retry);
    assert(noDtnFailureAction(true, 3, 3) == NoDtnAction::DropLimit);
    assert(noDtnFailureAction(true, 255, 3) == NoDtnAction::AlreadyRemoved);
    checkQueue<FifoQueue>(); checkQueue<PriorityMinHeap>();
    assert(!validAdminPassword("short"));
    assert(!validAdminPassword("password with spaces"));
    assert(validAdminPassword("test-password-123"));
    NODE_ID = 2;
    AsyncWebServerRequest relay; relay.credentialMatches = true;
    assert(!authorizeAdmin(&relay) && relay.status == 404 && relay.authCalls == 0);
    NODE_ID = 1;
    AsyncWebServerRequest unset;
    assert(!authorizeAdmin(&unset) && unset.status == 503 && unset.authCalls == 0);
    strcpy(adminPassword, "test-password-123");
    AsyncWebServerRequest denied;
    assert(!authorizeAdmin(&denied) && denied.challenges == 1);
    AsyncWebServerRequest allowed; allowed.credentialMatches = true;
    assert(authorizeAdmin(&allowed) && allowed.challenges == 0);
    assert(std::string(adminPassword) == "test-password-123");
}
'''
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(Path(__file__).parent.resolve()))
            (root / 'Arduino.h').write_text('#pragma once\n#include <stdint.h>\n#include <stddef.h>\nuint32_t millis();\n', encoding='utf-8')
            (root / 'test.cpp').write_text(code, encoding='utf-8')
            executable = root / 'test.exe'
            result = subprocess.run([compiler, '-std=c++17', '-static', '-static-libgcc', '-static-libstdc++',
                                     '-I', str(root), '-I', str(ROOT / 'include'),
                                     str(root / 'test.cpp'), '-o', str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
