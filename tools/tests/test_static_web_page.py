"""Regression: HTML must use the installed library's flash response, not String.

Executes the actual installed response factory and flash-buffer reader against
the actual generated pages. Network/Arduino classes are controlled host stubs;
this is not a replacement for ESP32 heap/load and browser checks.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_message_handling import function

ROOT = Path(__file__).resolve().parents[2]


class StaticWebPage(unittest.TestCase):
    def test_flash_response_preserves_both_pages(self):
        library = ROOT / '.pio/libdeps/baseline-n1/ESPAsyncWebServer/src'
        factory = (library / 'WebRequest.cpp').read_text(encoding='utf-8')
        responses = (library / 'WebResponses.cpp').read_text(encoding='utf-8')
        actual = '\n'.join([
            function(factory, 'AsyncWebServerResponse* AsyncWebServerRequest::beginResponse(int code, const char* contentType, const char* content,'),
            function(factory, 'AsyncWebServerResponse* AsyncWebServerRequest::beginResponse(int code, const char* contentType, const uint8_t* content,'),
            function(responses, 'AsyncProgmemResponse::AsyncProgmemResponse('),
            function(responses, 'size_t AsyncProgmemResponse::_fillBuffer('),
        ])
        firmware = (ROOT / 'src/main.cpp').read_text(encoding='utf-8')
        self.assertNotIn('request->send_P(', firmware)
        self.assertIn('sendStaticWebPage(request, CAPTIVE_PORTAL_HTML);', firmware)
        self.assertIn('if (!authorizeAdmin(request)) return;\n        sendStaticWebPage(request, ADMIN_DASHBOARD_HTML);', firmware)
        stub = r'''
#pragma once
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
using AwsTemplateProcessor = void*;
#define memcpy_P memcpy
inline int basicResponses = 0;
struct AsyncWebServerResponse {
    int _code = 0;
    std::string _contentType, cache;
    size_t _contentLength = 0;
    virtual ~AsyncWebServerResponse() = default;
    void addHeader(const char* name, const char* value) { assert(std::string(name) == "Cache-Control"); cache = value; }
};
struct AsyncAbstractResponse : AsyncWebServerResponse {
    explicit AsyncAbstractResponse(AwsTemplateProcessor callback) { assert(!callback); }
};
struct AsyncBasicResponse : AsyncWebServerResponse {
    AsyncBasicResponse(int, const char*, const char*) { ++basicResponses; }
};
struct AsyncProgmemResponse : AsyncAbstractResponse {
    const uint8_t* _content = nullptr;
    size_t _readLength = 0;
    AsyncProgmemResponse(int, const char*, const uint8_t*, size_t, AwsTemplateProcessor = nullptr);
    size_t _fillBuffer(uint8_t*, size_t);
};
struct AsyncWebServerRequest {
    AsyncWebServerResponse* response = nullptr;
    AsyncWebServerResponse* beginResponse(int, const char*, const char*, AwsTemplateProcessor = nullptr);
    AsyncWebServerResponse* beginResponse(int, const char*, const uint8_t*, size_t, AwsTemplateProcessor = nullptr);
    void send(AsyncWebServerResponse* value) { response = value; }
    ~AsyncWebServerRequest() { delete response; }
};
'''
        code = r'''
#include "static_web_page.h"
#include "captive_portal.h"
#include "admin_dashboard.h"
''' + actual + r'''
template<size_t N> void check(const char (&page)[N], size_t chunk) {
    AsyncWebServerRequest request;
    sendStaticWebPage(&request, page);
    auto* response = dynamic_cast<AsyncProgmemResponse*>(request.response);
    assert(response && response->_content == reinterpret_cast<const uint8_t*>(page));
    assert(response->_contentLength == N - 1);
    assert(response->_code == 200 && response->cache == "no-store");
    assert(response->_contentType == "text/html; charset=utf-8");
    std::vector<uint8_t> buffer(chunk);
    std::string body;
    while (auto n = response->_fillBuffer(buffer.data(), buffer.size())) body.append(reinterpret_cast<char*>(buffer.data()), n);
    assert(body == std::string(page, N - 1));
    assert(response->_fillBuffer(buffer.data(), buffer.size()) == 0);
}
int main() {
    for (int visit = 0; visit < 30; ++visit) {
        for (size_t chunk : {1u, 1460u, 4096u}) {
            check(CAPTIVE_PORTAL_HTML, chunk);
            check(ADMIN_DASHBOARD_HTML, chunk);
        }
    }
    assert(basicResponses == 0);
    // Two simultaneous readers must have independent offsets into static data.
    AsyncWebServerRequest first, second;
    sendStaticWebPage(&first, CAPTIVE_PORTAL_HTML);
    sendStaticWebPage(&second, CAPTIVE_PORTAL_HTML);
    auto* a = dynamic_cast<AsyncProgmemResponse*>(first.response);
    auto* b = dynamic_cast<AsyncProgmemResponse*>(second.response);
    uint8_t buffer[100];
    assert(a->_fillBuffer(buffer, 100) == 100 && b->_readLength == 0);
    assert(b->_fillBuffer(buffer, 100) == 100 && a->_readLength == 100);
}
'''
        compiler = shutil.which('g++')
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            (root / 'ESPAsyncWebServer.h').write_text(stub, encoding='utf-8')
            (root / 'pgmspace.h').write_text('#pragma once\n#define PROGMEM\n', encoding='utf-8')
            (root / 'test.cpp').write_text(code, encoding='utf-8')
            executable = root / 'test.exe'
            result = subprocess.run([compiler, '-std=c++17', '-static', '-static-libgcc', '-static-libstdc++',
                                     '-I', str(root), '-I', str(ROOT / 'include'), str(root / 'test.cpp'), '-o', str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
