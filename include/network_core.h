#ifndef NETWORK_CORE_H
#define NETWORK_CORE_H

#include <Arduino.h>
#include "min_heap.h"

constexpr uint8_t NETWORK_NODE_COUNT = 6;
constexpr size_t DTN_BUFFER_MAX_BYTES = 8192;

class DtnBuffer {
private:
    struct Entry {
        EmergencyMessage message;
        bool occupied;
    };

    static constexpr size_t MAX_ENTRIES =
        (DTN_BUFFER_MAX_BYTES - sizeof(size_t)) / sizeof(Entry);
    Entry entries[MAX_ENTRIES];
    size_t usedEntries;

    static bool deadlineReached(uint32_t now, uint32_t deadline) {
        return (int32_t)(now - deadline) >= 0;
    }

public:
    static constexpr size_t B_MAX_BYTES = DTN_BUFFER_MAX_BYTES;

    DtnBuffer() : usedEntries(0) {
        for (size_t i = 0; i < MAX_ENTRIES; i++) entries[i].occupied = false;
    }

    bool store(const EmergencyMessage &message, uint32_t now) {
        purgeExpired(now);
        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (entries[i].occupied && entries[i].message.id == message.id &&
                entries[i].message.originNode == message.originNode) {
                return true;
            }
        }
        if (usedEntries >= MAX_ENTRIES) return false;

        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (entries[i].occupied) continue;
            entries[i].message = message;
            if (entries[i].message.expiresAtMs == 0) {
                entries[i].message.expiresAtMs = now + 1800000UL;
            }
            entries[i].occupied = true;
            usedEntries++;
            return true;
        }
        return false;
    }

    bool peekDue(uint32_t now, EmergencyMessage &message) {
        purgeExpired(now);
        int selected = -1;
        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (!entries[i].occupied ||
                !deadlineReached(now, entries[i].message.nextRetryAtMs)) continue;
            if (selected < 0 || entries[i].message.priority < entries[selected].message.priority ||
                (entries[i].message.priority == entries[selected].message.priority &&
                 entries[i].message.timestamp_tx < entries[selected].message.timestamp_tx)) {
                selected = (int)i;
            }
        }
        if (selected < 0) return false;
        message = entries[selected].message;
        return true;
    }

    bool defer(uint16_t id, uint8_t originNode, uint32_t nextAttemptAtMs, uint8_t retryExponent) {
        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (!entries[i].occupied || entries[i].message.id != id ||
                entries[i].message.originNode != originNode) continue;
            entries[i].message.nextRetryAtMs = nextAttemptAtMs;
            entries[i].message.retryExponent = retryExponent;
            return true;
        }
        return false;
    }

    bool remove(uint16_t id, uint8_t originNode) {
        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (!entries[i].occupied || entries[i].message.id != id ||
                entries[i].message.originNode != originNode) continue;
            entries[i].occupied = false;
            usedEntries--;
            return true;
        }
        return false;
    }

    size_t purgeExpired(uint32_t now) {
        size_t purged = 0;
        for (size_t i = 0; i < MAX_ENTRIES; i++) {
            if (entries[i].occupied && deadlineReached(now, entries[i].message.expiresAtMs)) {
                entries[i].occupied = false;
                usedEntries--;
                purged++;
            }
        }
        return purged;
    }

    size_t size() const { return usedEntries; }
    size_t usedBytes() const { return usedEntries * sizeof(Entry); }
};

static_assert(sizeof(DtnBuffer) <= DtnBuffer::B_MAX_BYTES,
              "DTN buffer object exceeds its configured SRAM ceiling");

inline bool dijkstraNextHop(const uint8_t graph[NETWORK_NODE_COUNT][NETWORK_NODE_COUNT],
                            uint8_t sourceNode, uint8_t destinationNode, uint8_t &nextHopNode) {
    if (sourceNode < 1 || sourceNode > NETWORK_NODE_COUNT ||
        destinationNode < 1 || destinationNode > NETWORK_NODE_COUNT) return false;
    if (sourceNode == destinationNode) {
        nextHopNode = sourceNode;
        return true;
    }

    constexpr uint16_t INFINITY_COST = 0xFFFF;
    const uint8_t source = sourceNode - 1;
    const uint8_t destination = destinationNode - 1;
    uint16_t distance[NETWORK_NODE_COUNT];
    uint8_t previous[NETWORK_NODE_COUNT];
    bool visited[NETWORK_NODE_COUNT] = {};
    for (uint8_t i = 0; i < NETWORK_NODE_COUNT; i++) {
        distance[i] = INFINITY_COST;
        previous[i] = 0xFF;
    }
    distance[source] = 0;

    for (uint8_t step = 0; step < NETWORK_NODE_COUNT; step++) {
        int current = -1;
        for (uint8_t i = 0; i < NETWORK_NODE_COUNT; i++) {
            if (!visited[i] && distance[i] != INFINITY_COST &&
                (current < 0 || distance[i] < distance[current])) current = i;
        }
        if (current < 0 || current == destination) break;
        visited[current] = true;

        for (uint8_t neighbor = 0; neighbor < NETWORK_NODE_COUNT; neighbor++) {
            const uint8_t edgeCost = graph[current][neighbor];
            if (edgeCost == 0 || visited[neighbor]) continue;
            const uint16_t candidate = distance[current] + edgeCost;
            if (candidate < distance[neighbor]) {
                distance[neighbor] = candidate;
                previous[neighbor] = (uint8_t)current;
            }
        }
    }

    if (distance[destination] == INFINITY_COST) return false;
    uint8_t hop = destination;
    while (previous[hop] != source) {
        if (previous[hop] == 0xFF) return false;
        hop = previous[hop];
    }
    nextHopNode = hop + 1;
    return true;
}

#endif