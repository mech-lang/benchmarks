#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <lean/lean.h>
#include <stdio.h>
#include <stdlib.h>

/* General regex compilation and next-match leaves; all benchmark traversal,
   counts, replacements and output assembly are implemented in Lean. */
static lean_external_class *regex_class;

static void finalize_regex(void *pointer) {
    pcre2_code_free((pcre2_code *)pointer);
}

static void visit_regex(void *pointer, b_lean_obj_arg visitor) {
    (void)pointer;
    (void)visitor;
}

LEAN_EXPORT lean_obj_res lean_bench_regex_compile(b_lean_obj_arg pattern) {
    int error;
    PCRE2_SIZE offset;
    pcre2_code *code = pcre2_compile((PCRE2_SPTR)lean_string_cstr(pattern),
        lean_string_size(pattern) - 1, 0, &error, &offset, NULL);
    if (!code) return lean_box(0);
    if (!regex_class)
        regex_class = lean_register_external_class(finalize_regex, visit_regex);
    lean_object *some = lean_alloc_ctor(1, 1, 0);
    lean_ctor_set(some, 0, lean_alloc_external(regex_class, code));
    return some;
}

LEAN_EXPORT lean_obj_res lean_bench_regex_find(b_lean_obj_arg regex,
        b_lean_obj_arg input, b_lean_obj_arg offset) {
    pcre2_code *code = (pcre2_code *)lean_get_external_data(regex);
    pcre2_match_data *data = pcre2_match_data_create_from_pattern(code, NULL);
    int result = pcre2_match(code, lean_sarray_cptr(input), lean_sarray_size(input),
        lean_usize_of_nat(offset), 0, data, NULL);
    if (result < 0) {
        pcre2_match_data_free(data);
        if (result != PCRE2_ERROR_NOMATCH) {
            fprintf(stderr, "PCRE2 match error: %d\n", result);
            abort();
        }
        return lean_box(0);
    }
    PCRE2_SIZE *range = pcre2_get_ovector_pointer(data);
    lean_object *pair = lean_alloc_ctor(0, 2, 0);
    lean_ctor_set(pair, 0, lean_usize_to_nat(range[0]));
    lean_ctor_set(pair, 1, lean_usize_to_nat(range[1]));
    pcre2_match_data_free(data);
    lean_object *some = lean_alloc_ctor(1, 1, 0);
    lean_ctor_set(some, 0, pair);
    return some;
}
