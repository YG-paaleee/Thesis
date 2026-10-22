#ifndef PRIVATE_CONFIG_H
#define PRIVATE_CONFIG_H

#include <stdint.h>

// Local deployment secrets. This file is intentionally excluded from Git.
// Every mesh node must use the same PSK; changing it requires reflashing all nodes.
static const uint8_t PRE_SHARED_KEY[16] = {
    0x8F, 0x71, 0x47, 0x05, 0x12, 0x6A, 0xB1, 0x42,
    0x65, 0xDE, 0xAF, 0xB8, 0x40, 0x31, 0x77, 0xA4
};

#define COMMUNITY_ACCESS_CREDENTIAL "SANMIGUEL2026"
#define ADMIN_DASHBOARD_USERNAME "admin"
#define ADMIN_DASHBOARD_PASSWORD "dDwIg9jTGvC_7UNqAAsR9CtE7X3bRvoS"

#endif
