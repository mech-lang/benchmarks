#include <lean/lean.h>
#include <stdio.h>

/* General fixed-point formatting; benchmark algorithms remain in Lean. */
LEAN_EXPORT lean_obj_res lean_bench_fixed(double value, uint32_t digits) {
    char buffer[512];
    if (digits > 30) digits = 30;
    snprintf(buffer, sizeof buffer, "%.*f", (int)digits, value);
    return lean_mk_string(buffer);
}
