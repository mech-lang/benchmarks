/* Compile against the retained complete SDK; never substitute ABI declarations. */
#include "reb-host.h"
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <gmp.h>
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

_Static_assert(sizeof(void *) == 8 && sizeof(double) == 8, "arm64 scalar layout");
_Static_assert(sizeof(RXIARG) == 16 && _Alignof(RXIARG) == 4, "packed argument layout");
_Static_assert(sizeof(RXIFRM) == 256 && offsetof(RXIARG, index) == 8, "frame layout");
_Static_assert(sizeof(REBREQ) == 116 && sizeof(REBEVT) == 16, "host event/request layout");
_Static_assert(sizeof(RL_LIB) == 52 * sizeof(void *), "complete generated function table");
_Static_assert(offsetof(RL_LIB, expand_series) == 16 * sizeof(void *), "expander slot");
_Static_assert(offsetof(RL_LIB, make_string) == 17 * sizeof(void *), "allocator slot");
_Static_assert(offsetof(RL_LIB, series) == 27 * sizeof(void *), "series accessor slot");
_Static_assert(RXT_BINARY == 40 && RXT_INTEGER == 5 && RXT_DECIMAL == 6, "value tags");

int main(int argc, char **argv) {
    if (argc != 2 || !CHECK_STRUCT_ALIGN) return 2;
    void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 3; }
    const char *symbols[] = {"RX_Init", "RX_Quit", "RX_Call"};
    for (size_t i = 0; i < sizeof(symbols) / sizeof(symbols[0]); ++i) {
        dlerror();
        void *address = dlsym(library, symbols[i]);
        if (!address || dlerror()) return 4;
        Dl_info info;
        if (!dladdr(address, &info) || !info.dli_fname) return 5;
        /* The controller resolves this actual origin against the built dylib. */
        printf("export\t%s\t%s\n", symbols[i], info.dli_fname);
    }
    char pcre_version[128];
    if (pcre2_config(PCRE2_CONFIG_VERSION, pcre_version) < 0) return 6;
    printf("layout\t8\t8\t16\t4\t256\t8\t116\t16\t416\t128\t136\t216\n");
    printf("gmp\t%s\npcre2\t%s\n", gmp_version, pcre_version);
    uint32_t count = _dyld_image_count();
    for (uint32_t i = 0; i < count; ++i) {
        const char *name = _dyld_get_image_name(i);
        if (!name || strchr(name, '\t') || strchr(name, '\n')) return 7;
        printf("image\t%s\n", name);
    }
    if (dlclose(library)) return 8;
    return ferror(stdout) ? 9 : 0;
}
