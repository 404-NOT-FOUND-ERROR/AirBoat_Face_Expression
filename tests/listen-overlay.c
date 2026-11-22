/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include "../integrations/listen-overlay/listen_overlay_rgb565.h"

int main(void)
{
    uint32_t hash = 2166136261U;
    for (unsigned i = 0; i <= 65535U; ++i) {
        const uint16_t value = (uint16_t)i;
        assert(airboat_listen_over_rgb565(value, 0U) == value);
        assert(airboat_listen_over_rgb565(value, 0xffffU) == 0xffffU);
        assert(airboat_listen_over_rgb565(0U, value) == value);
        const uint16_t actual = airboat_listen_over_rgb565(value, (uint16_t)(i ^ 0xa55aU));
        hash = (hash ^ (actual & 255U)) * 16777619U;
        hash = (hash ^ (actual >> 8)) * 16777619U;
    }
    printf("{\"status\":\"passed\",\"backgrounds\":65536,\"fingerprint\":%lu}\n", (unsigned long)hash);
    return 0;
}
