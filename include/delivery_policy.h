#ifndef DELIVERY_POLICY_H
#define DELIVERY_POLICY_H

#include <stdint.h>

enum class NoDtnAction { DropNoRoute, Retry, DropLimit, AlreadyRemoved };

inline NoDtnAction noDtnFailureAction(bool routeExists, uint8_t failedAttempts, uint8_t limit) {
    if (!routeExists) return NoDtnAction::DropNoRoute;
    if (failedAttempts == 255) return NoDtnAction::AlreadyRemoved;
    return failedAttempts >= limit ? NoDtnAction::DropLimit : NoDtnAction::Retry;
}

#endif
