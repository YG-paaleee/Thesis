"""Verify direct survey routes and planned-topology exclusion using real headers."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SurveyRouting(unittest.TestCase):
    def test_v6_v1_measured_link(self):
        source = (ROOT / 'src/main.cpp').read_text(encoding='utf-8')
        matrix = re.search(r'uint8_t adjacencyMatrix\[.*?\] = (\{.*?\n\});', source, re.S).group(1)
        code = r'''
#include <cassert>
#include "link_state.h"
uint32_t millis() { return 0; }
int main() {
    const uint8_t planned[NETWORK_NODE_COUNT][NETWORK_NODE_COUNT] = MATRIX;
    for (uint8_t self : {uint8_t(1), uint8_t(6)}) {
        const uint8_t peer = self == 1 ? 6 : 1;
        LinkStateDb db; db.begin(self);
        uint8_t own[6], remote[6], graph[6][6], hop;
        memset(own, 255, sizeof own); memset(remote, 255, sizeof remote);
        own[self-1] = remote[peer-1] = 0;
        own[peer-1] = remote[self-1] = 1;
        assert(db.update(peer, 1, remote, 100));
        db.buildGraph(own, planned, true, 101, 300000, graph);
        assert(!dijkstraNextHop(graph, self, peer, hop));
        db.buildGraph(own, planned, false, 101, 300000, graph);
        assert(dijkstraNextHop(graph, self, peer, hop) && hop == peer);
        own[peer-1] = 255;
        db.buildGraph(own, planned, false, 101, 300000, graph);
        assert(!dijkstraNextHop(graph, self, peer, hop));
    }
}
'''.replace('MATRIX', matrix)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'Arduino.h').write_text('#pragma once\n#include <stdint.h>\n#include <stddef.h>\n#include <initializer_list>\nuint32_t millis();\n')
            (path / 'test.cpp').write_text(code)
            exe = path / 'test.exe'
            subprocess.run([shutil.which('g++'), '-std=c++17', '-static', '-static-libgcc', '-static-libstdc++', '-I', str(path), '-I', str(ROOT / 'include'), str(path / 'test.cpp'), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    unittest.main()
