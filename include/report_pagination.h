#pragma once
#include <stdint.h>
#include <stddef.h>

inline bool parseHistoryNumber(const char *text, uint32_t &out) {
    if (!text || !*text) return false;
    uint64_t value = 0;
    for (; *text; ++text) {
        if (*text < '0' || *text > '9') return false;
        value = value * 10 + (*text - '0');
        if (value > UINT32_MAX) return false;
    }
    out = (uint32_t)value;
    return true;
}

struct ReportPage {
    uint32_t snapshot = 0;
    size_t retained = 0, pages = 1, offset = 0, length = 0;
};
enum class ReportPageResult { Ok, InvalidPage, ExpiredSnapshot };

// Offset is measured from the current ring's oldest entry. Page 1 is newest.
inline ReportPageResult planReportPage(uint32_t total, size_t capacity, size_t pageSize,
                                      uint32_t page, uint32_t snapshot, ReportPage &out) {
    if (!capacity || !pageSize || !page) return ReportPageResult::InvalidPage;
    out = ReportPage{};
    out.snapshot = snapshot ? snapshot : total;
    if (out.snapshot > total) return ReportPageResult::ExpiredSnapshot;
    out.retained = out.snapshot < capacity ? out.snapshot : capacity;
    out.pages = out.retained ? (out.retained + pageSize - 1) / pageSize : 1;
    if (page > out.pages) return ReportPageResult::InvalidPage;
    const uint32_t oldestNow = total > capacity ? total - capacity + 1 : 1;
    const uint32_t oldestSnapshot = out.snapshot - out.retained + 1;
    if (oldestNow > oldestSnapshot) return ReportPageResult::ExpiredSnapshot;
    const size_t end = out.retained - (page - 1) * pageSize;
    const size_t start = end > pageSize ? end - pageSize : 0;
    out.offset = oldestSnapshot - oldestNow + start;
    out.length = end - start;
    return ReportPageResult::Ok;
}
