// Lean compiler output
// Module: fannkuchredux
// Imports: public import Init public meta import Init public import Std
#include <lean/lean.h>

#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
static _Atomic unsigned char bench_seen[362880];
static _Atomic unsigned long long bench_visits, bench_duplicates, bench_invalid;
static void bench_visit(size_t n, lean_object* p) {
  if (n > 9 || lean_sarray_size(p) != n) { atomic_fetch_add(&bench_invalid, 1); return; }
  size_t rank = 0; unsigned mask = 0;
  for (size_t i = 0; i < n; i++) {
    unsigned x = lean_byte_array_uget(p, i);
    if (x >= n || (mask & (1u << x))) { atomic_fetch_add(&bench_invalid, 1); return; }
    mask |= 1u << x;
    unsigned smaller = 0;
    for (size_t j = i + 1; j < n; j++) smaller += lean_byte_array_uget(p, j) < x;
    rank = rank * (n - i) + smaller;
  }
  atomic_fetch_add(&bench_visits, 1);
  if (atomic_exchange(&bench_seen[rank], 1)) atomic_fetch_add(&bench_duplicates, 1);
}
__attribute__((destructor)) static void bench_perm_report(void) {
  unsigned long long distinct = 0;
  for (size_t i = 0; i < 362880; i++) distinct += atomic_load(&bench_seen[i]);
  fprintf(stderr, "{\"visits\":%llu,\"duplicates\":%llu,\"invalid\":%llu,\"distinct\":%llu}\n",
      atomic_load(&bench_visits), atomic_load(&bench_duplicates), atomic_load(&bench_invalid), distinct);
}

#if defined(__clang__)
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wunused-label"
#elif defined(__GNUC__) && !defined(__CLANG__)
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#endif
#ifdef __cplusplus
extern "C" {
#endif
uint8_t lean_nat_dec_lt(lean_object*, lean_object*);
lean_object* lean_array_get_size(lean_object*);
lean_object* lean_nat_sub(lean_object*, lean_object*);
lean_object* lean_array_get_borrowed(lean_object*, lean_object*, lean_object*);
lean_object* lean_nat_mul(lean_object*, lean_object*);
lean_object* lean_array_push(lean_object*, lean_object*);
lean_object* lean_nat_add(lean_object*, lean_object*);
lean_object* l_Array_range(lean_object*);
size_t lean_array_size(lean_object*);
uint8_t lean_usize_dec_lt(size_t, size_t);
lean_object* lean_array_uget(lean_object*, size_t);
lean_object* lean_array_uset(lean_object*, size_t, lean_object*);
uint8_t lean_uint8_of_nat(lean_object*);
size_t lean_usize_add(size_t, size_t);
lean_object* lean_byte_array_mk(lean_object*);
lean_object* lean_mk_array(lean_object*, lean_object*);
lean_object* l_List_range(lean_object*);
lean_object* l_List_reverse___redArg(lean_object*);
lean_object* lean_nat_div(lean_object*, lean_object*);
lean_object* lean_nat_mod(lean_object*, lean_object*);
lean_object* lean_byte_array_set(lean_object*, lean_object*, uint8_t);
size_t lean_usize_of_nat(lean_object*);
uint8_t lean_byte_array_uget(lean_object*, size_t);
lean_object* lean_byte_array_uset(lean_object*, size_t, uint8_t);
uint64_t lean_uint64_of_nat(lean_object*);
uint8_t lean_nat_dec_eq(lean_object*, lean_object*);
uint64_t lean_int64_of_nat(lean_object*);
lean_object* lean_usize_to_nat(size_t);
lean_object* lean_byte_array_copy_slice(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, uint8_t);
uint8_t lean_uint8_dec_eq(uint8_t, uint8_t);
uint8_t lean_uint64_dec_eq(uint64_t, uint64_t);
uint64_t lean_uint64_sub(uint64_t, uint64_t);
uint8_t lean_usize_dec_eq(size_t, size_t);
uint8_t lean_uint8_sub(uint8_t, uint8_t);
uint8_t lean_uint8_dec_lt(uint8_t, uint8_t);
uint8_t lean_uint32_dec_le(uint32_t, uint32_t);
size_t lean_uint8_to_usize(uint8_t);
size_t lean_usize_sub(size_t, size_t);
uint32_t lean_uint32_add(uint32_t, uint32_t);
uint64_t lean_uint32_to_uint64(uint32_t);
uint64_t lean_int64_sub(uint64_t, uint64_t);
uint64_t lean_int64_add(uint64_t, uint64_t);
uint8_t lean_usize_to_uint8(size_t);
lean_object* lean_array_uget_borrowed(lean_object*, size_t);
lean_object* lean_task_get_own(lean_object*);
lean_object* lean_task_spawn(lean_object*, lean_object*);
lean_object* lean_int64_to_int_sint(uint64_t);
lean_object* l_Int_repr(lean_object*);
lean_object* lean_string_append(lean_object*, lean_object*);
lean_object* l_Nat_reprFast(lean_object*);
lean_object* lean_uint32_to_nat(uint32_t);
lean_object* lean_string_push(lean_object*, uint32_t);
lean_object* lean_get_stdout();
lean_object* lean_mk_empty_array_with_capacity(lean_object*);
lean_object* lean_string_utf8_byte_size(lean_object*);
lean_object* l_String_Slice_toNat_x21(lean_object*);
uint8_t lean_nat_dec_le(lean_object*, lean_object*);
lean_object* lean_array_get(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_reversePrefix(lean_object*, size_t, size_t);
LEAN_EXPORT lean_object* l_reversePrefix___boxed(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_rotatePrefix(lean_object*, size_t, size_t, uint8_t);
LEAN_EXPORT lean_object* l_rotatePrefix___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_carrying(size_t, size_t, lean_object*, lean_object*, lean_object*, uint64_t, uint8_t, uint64_t, uint32_t);
LEAN_EXPORT lean_object* l_flipping(size_t, lean_object*, lean_object*, lean_object*, uint64_t, uint8_t, uint64_t, uint32_t, uint32_t);
LEAN_EXPORT lean_object* l_enumerating(size_t, size_t, lean_object*, lean_object*, lean_object*, uint64_t, uint8_t, uint64_t, uint32_t);
LEAN_EXPORT lean_object* l_enumerating___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_carrying___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_flipping___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___redArg(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___redArg___boxed(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0(size_t, size_t, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0___boxed(lean_object*, lean_object*, lean_object*);
static lean_once_cell_t l_chunk___closed__0_once = LEAN_ONCE_CELL_INITIALIZER;
static uint64_t l_chunk___closed__0;
LEAN_EXPORT lean_object* l_chunk(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_chunk___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3(lean_object*, size_t, size_t, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(lean_object*);
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0(lean_object*);
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0___boxed(lean_object*, lean_object*);
static const lean_string_object l_main___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 14, .m_capacity = 14, .m_length = 13, .m_data = "\nPfannkuchen("};
static const lean_object* l_main___closed__0 = (const lean_object*)&l_main___closed__0_value;
static const lean_string_object l_main___closed__1_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 5, .m_capacity = 5, .m_length = 4, .m_data = ") = "};
static const lean_object* l_main___closed__1 = (const lean_object*)&l_main___closed__1_value;
static const lean_array_object l_main___closed__2_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_array_object) + sizeof(void*)*1, .m_other = 0, .m_tag = 246}, .m_size = 1, .m_capacity = 1, .m_data = {((lean_object*)(((size_t)(1) << 1) | 1))}};
static const lean_object* l_main___closed__2 = (const lean_object*)&l_main___closed__2_value;
static const lean_string_object l_main___closed__3_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 44, .m_capacity = 44, .m_length = 43, .m_data = "native permutation counters support n <= 16"};
static const lean_object* l_main___closed__3 = (const lean_object*)&l_main___closed__3_value;
static const lean_ctor_object l_main___closed__4_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 18}, .m_objs = {((lean_object*)&l_main___closed__3_value)}};
static const lean_object* l_main___closed__4 = (const lean_object*)&l_main___closed__4_value;
static const lean_string_object l_main___closed__5_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 2, .m_capacity = 2, .m_length = 1, .m_data = "0"};
static const lean_object* l_main___closed__5 = (const lean_object*)&l_main___closed__5_value;
LEAN_EXPORT lean_object* _lean_main(lean_object*);
LEAN_EXPORT lean_object* l_main___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_reversePrefix(lean_object* v_p_1_, size_t v_first_2_, size_t v_last_3_){
_start:
{
uint8_t v___x_4_; 
v___x_4_ = lean_usize_dec_lt(v_first_2_, v_last_3_);
if (v___x_4_ == 0)
{
return v_p_1_;
}
else
{
uint8_t v_value_5_; uint8_t v___x_6_; lean_object* v_p_7_; lean_object* v_p_8_; size_t v___x_9_; size_t v___x_10_; size_t v___x_11_; 
v_value_5_ = lean_byte_array_uget(v_p_1_, v_first_2_);
v___x_6_ = lean_byte_array_uget(v_p_1_, v_last_3_);
v_p_7_ = lean_byte_array_uset(v_p_1_, v_first_2_, v___x_6_);
v_p_8_ = lean_byte_array_uset(v_p_7_, v_last_3_, v_value_5_);
v___x_9_ = ((size_t)1ULL);
v___x_10_ = lean_usize_add(v_first_2_, v___x_9_);
v___x_11_ = lean_usize_sub(v_last_3_, v___x_9_);
v_p_1_ = v_p_8_;
v_first_2_ = v___x_10_;
v_last_3_ = v___x_11_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l_reversePrefix___boxed(lean_object* v_p_13_, lean_object* v_first_14_, lean_object* v_last_15_){
_start:
{
size_t v_first_boxed_16_; size_t v_last_boxed_17_; lean_object* v_res_18_; 
v_first_boxed_16_ = lean_unbox_usize(v_first_14_);
lean_dec(v_first_14_);
v_last_boxed_17_ = lean_unbox_usize(v_last_15_);
lean_dec(v_last_15_);
v_res_18_ = l_reversePrefix(v_p_13_, v_first_boxed_16_, v_last_boxed_17_);
return v_res_18_;
}
}
LEAN_EXPORT lean_object* l_rotatePrefix(lean_object* v_p_19_, size_t v_i_20_, size_t v_last_21_, uint8_t v_first_22_){
_start:
{
uint8_t v___x_23_; 
v___x_23_ = lean_usize_dec_lt(v_i_20_, v_last_21_);
if (v___x_23_ == 0)
{
lean_object* v___x_24_; 
v___x_24_ = lean_byte_array_uset(v_p_19_, v_last_21_, v_first_22_);
return v___x_24_;
}
else
{
size_t v___x_25_; size_t v___x_26_; uint8_t v___x_27_; lean_object* v___x_28_; 
v___x_25_ = ((size_t)1ULL);
v___x_26_ = lean_usize_add(v_i_20_, v___x_25_);
v___x_27_ = lean_byte_array_uget(v_p_19_, v___x_26_);
v___x_28_ = lean_byte_array_uset(v_p_19_, v_i_20_, v___x_27_);
v_p_19_ = v___x_28_;
v_i_20_ = v___x_26_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l_rotatePrefix___boxed(lean_object* v_p_30_, lean_object* v_i_31_, lean_object* v_last_32_, lean_object* v_first_33_){
_start:
{
size_t v_i_boxed_34_; size_t v_last_boxed_35_; uint8_t v_first_boxed_36_; lean_object* v_res_37_; 
v_i_boxed_34_ = lean_unbox_usize(v_i_31_);
lean_dec(v_i_31_);
v_last_boxed_35_ = lean_unbox_usize(v_last_32_);
lean_dec(v_last_32_);
v_first_boxed_36_ = lean_unbox(v_first_33_);
v_res_37_ = l_rotatePrefix(v_p_30_, v_i_boxed_34_, v_last_boxed_35_, v_first_boxed_36_);
return v_res_37_;
}
}
LEAN_EXPORT lean_object* l_carrying(size_t v_n_38_, size_t v_rank_39_, lean_object* v_p_40_, lean_object* v_counts_41_, lean_object* v_scratch_42_, uint64_t v_remaining_43_, uint8_t v_positive_44_, uint64_t v_checksum_45_, uint32_t v_maximum_46_){
_start:
{
uint8_t v___x_47_; 
v___x_47_ = lean_usize_dec_eq(v_rank_39_, v_n_38_);
if (v___x_47_ == 0)
{
size_t v___x_48_; uint8_t v___x_49_; lean_object* v_p_50_; uint8_t v___x_51_; uint8_t v___x_52_; uint8_t v_count_53_; lean_object* v_counts_54_; uint8_t v___x_55_; uint8_t v___x_56_; 
v___x_48_ = ((size_t)0ULL);
v___x_49_ = lean_byte_array_uget(v_p_40_, v___x_48_);
v_p_50_ = l_rotatePrefix(v_p_40_, v___x_48_, v_rank_39_, v___x_49_);
v___x_51_ = lean_byte_array_uget(v_counts_41_, v_rank_39_);
v___x_52_ = 1;
v_count_53_ = lean_uint8_sub(v___x_51_, v___x_52_);
v_counts_54_ = lean_byte_array_uset(v_counts_41_, v_rank_39_, v_count_53_);
v___x_55_ = 0;
v___x_56_ = lean_uint8_dec_lt(v___x_55_, v_count_53_);
if (v___x_56_ == 0)
{
size_t v___x_57_; size_t v___x_58_; 
v___x_57_ = ((size_t)1ULL);
v___x_58_ = lean_usize_add(v_rank_39_, v___x_57_);
v_rank_39_ = v___x_58_;
v_p_40_ = v_p_50_;
v_counts_41_ = v_counts_54_;
goto _start;
}
else
{
lean_object* v___x_60_; 
v___x_60_ = l_enumerating(v_n_38_, v_rank_39_, v_p_50_, v_counts_54_, v_scratch_42_, v_remaining_43_, v_positive_44_, v_checksum_45_, v_maximum_46_);
return v___x_60_;
}
}
else
{
lean_object* v___x_61_; lean_object* v___x_62_; lean_object* v___x_63_; 
lean_dec_ref(v_scratch_42_);
lean_dec_ref(v_counts_41_);
lean_dec_ref(v_p_40_);
v___x_61_ = lean_box_uint64(v_checksum_45_);
v___x_62_ = lean_box_uint32(v_maximum_46_);
v___x_63_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_63_, 0, v___x_61_);
lean_ctor_set(v___x_63_, 1, v___x_62_);
return v___x_63_;
}
}
}
LEAN_EXPORT lean_object* l_flipping(size_t v_n_64_, lean_object* v_p_65_, lean_object* v_counts_66_, lean_object* v_work_67_, uint64_t v_remaining_68_, uint8_t v_positive_69_, uint64_t v_checksum_70_, uint32_t v_maximum_71_, uint32_t v_flips_72_){
_start:
{
size_t v___x_73_; uint8_t v_first_74_; uint8_t v___x_75_; uint8_t v___x_76_; uint64_t v___y_78_; uint32_t v___y_79_; uint64_t v___y_90_; 
v___x_73_ = ((size_t)0ULL);
v_first_74_ = lean_byte_array_uget(v_work_67_, v___x_73_);
v___x_75_ = 0;
v___x_76_ = lean_uint8_dec_eq(v_first_74_, v___x_75_);
if (v___x_76_ == 0)
{
size_t v___x_92_; lean_object* v___x_93_; uint32_t v___x_94_; uint32_t v___x_95_; 
v___x_92_ = lean_uint8_to_usize(v_first_74_);
v___x_93_ = l_reversePrefix(v_work_67_, v___x_73_, v___x_92_);
v___x_94_ = 1;
v___x_95_ = lean_uint32_add(v_flips_72_, v___x_94_);
v_work_67_ = v___x_93_;
v_flips_72_ = v___x_95_;
goto _start;
}
else
{
uint64_t v_value_97_; 
v_value_97_ = lean_uint32_to_uint64(v_flips_72_);
if (v_positive_69_ == 0)
{
uint64_t v___x_98_; 
v___x_98_ = lean_int64_sub(v_checksum_70_, v_value_97_);
v___y_90_ = v___x_98_;
goto v___jp_89_;
}
else
{
uint64_t v___x_99_; 
v___x_99_ = lean_int64_add(v_checksum_70_, v_value_97_);
v___y_90_ = v___x_99_;
goto v___jp_89_;
}
}
v___jp_77_:
{
uint64_t v___x_80_; uint8_t v___x_81_; 
v___x_80_ = 1ULL;
v___x_81_ = lean_uint64_dec_eq(v_remaining_68_, v___x_80_);
if (v___x_81_ == 0)
{
size_t v___x_82_; uint64_t v___x_83_; 
v___x_82_ = ((size_t)1ULL);
v___x_83_ = lean_uint64_sub(v_remaining_68_, v___x_80_);
if (v_positive_69_ == 0)
{
lean_object* v___x_84_; 
v___x_84_ = l_carrying(v_n_64_, v___x_82_, v_p_65_, v_counts_66_, v_work_67_, v___x_83_, v___x_76_, v___y_78_, v___y_79_);
return v___x_84_;
}
else
{
lean_object* v___x_85_; 
v___x_85_ = l_carrying(v_n_64_, v___x_82_, v_p_65_, v_counts_66_, v_work_67_, v___x_83_, v___x_81_, v___y_78_, v___y_79_);
return v___x_85_;
}
}
else
{
lean_object* v___x_86_; lean_object* v___x_87_; lean_object* v___x_88_; 
lean_dec_ref(v_work_67_);
lean_dec_ref(v_counts_66_);
lean_dec_ref(v_p_65_);
v___x_86_ = lean_box_uint64(v___y_78_);
v___x_87_ = lean_box_uint32(v___y_79_);
v___x_88_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_88_, 0, v___x_86_);
lean_ctor_set(v___x_88_, 1, v___x_87_);
return v___x_88_;
}
}
v___jp_89_:
{
uint8_t v___x_91_; 
v___x_91_ = lean_uint32_dec_le(v_maximum_71_, v_flips_72_);
if (v___x_91_ == 0)
{
v___y_78_ = v___y_90_;
v___y_79_ = v_maximum_71_;
goto v___jp_77_;
}
else
{
v___y_78_ = v___y_90_;
v___y_79_ = v_flips_72_;
goto v___jp_77_;
}
}
}
}
LEAN_EXPORT lean_object* l_enumerating(size_t v_n_100_, size_t v_rank_101_, lean_object* v_p_102_, lean_object* v_counts_103_, lean_object* v_scratch_104_, uint64_t v_remaining_105_, uint8_t v_positive_106_, uint64_t v_checksum_107_, uint32_t v_maximum_108_){
_start:
{
size_t v___x_109_; uint8_t v___x_110_; 
v___x_109_ = ((size_t)1ULL);
v___x_110_ = lean_usize_dec_lt(v___x_109_, v_rank_101_);
if (v___x_110_ == 0)
{
lean_object* v___x_111_; lean_object* v___x_112_; uint8_t v___x_113_; lean_object* v___x_114_; uint32_t v___x_115_; lean_object* v___x_116_; 
v___x_111_ = lean_unsigned_to_nat(0u);
v___x_112_ = lean_usize_to_nat(v_n_100_);
v___x_113_ = 1;
v___x_114_ = lean_byte_array_copy_slice(v_p_102_, v___x_111_, v_scratch_104_, v___x_111_, v___x_112_, v___x_113_);
v___x_115_ = 0;
bench_visit(v_n_100_, v_p_102_);
v___x_116_ = l_flipping(v_n_100_, v_p_102_, v_counts_103_, v___x_114_, v_remaining_105_, v_positive_106_, v_checksum_107_, v_maximum_108_, v___x_115_);
return v___x_116_;
}
else
{
size_t v___x_117_; uint8_t v___x_118_; lean_object* v___x_119_; 
v___x_117_ = lean_usize_sub(v_rank_101_, v___x_109_);
v___x_118_ = lean_usize_to_uint8(v_rank_101_);
v___x_119_ = lean_byte_array_uset(v_counts_103_, v___x_117_, v___x_118_);
v_rank_101_ = v___x_117_;
v_counts_103_ = v___x_119_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l_enumerating___boxed(lean_object* v_n_121_, lean_object* v_rank_122_, lean_object* v_p_123_, lean_object* v_counts_124_, lean_object* v_scratch_125_, lean_object* v_remaining_126_, lean_object* v_positive_127_, lean_object* v_checksum_128_, lean_object* v_maximum_129_){
_start:
{
size_t v_n_boxed_130_; size_t v_rank_boxed_131_; uint64_t v_remaining_boxed_132_; uint8_t v_positive_boxed_133_; uint64_t v_checksum_boxed_134_; uint32_t v_maximum_boxed_135_; lean_object* v_res_136_; 
v_n_boxed_130_ = lean_unbox_usize(v_n_121_);
lean_dec(v_n_121_);
v_rank_boxed_131_ = lean_unbox_usize(v_rank_122_);
lean_dec(v_rank_122_);
v_remaining_boxed_132_ = lean_unbox_uint64(v_remaining_126_);
lean_dec_ref(v_remaining_126_);
v_positive_boxed_133_ = lean_unbox(v_positive_127_);
v_checksum_boxed_134_ = lean_unbox_uint64(v_checksum_128_);
lean_dec_ref(v_checksum_128_);
v_maximum_boxed_135_ = lean_unbox_uint32(v_maximum_129_);
lean_dec(v_maximum_129_);
v_res_136_ = l_enumerating(v_n_boxed_130_, v_rank_boxed_131_, v_p_123_, v_counts_124_, v_scratch_125_, v_remaining_boxed_132_, v_positive_boxed_133_, v_checksum_boxed_134_, v_maximum_boxed_135_);
return v_res_136_;
}
}
LEAN_EXPORT lean_object* l_carrying___boxed(lean_object* v_n_137_, lean_object* v_rank_138_, lean_object* v_p_139_, lean_object* v_counts_140_, lean_object* v_scratch_141_, lean_object* v_remaining_142_, lean_object* v_positive_143_, lean_object* v_checksum_144_, lean_object* v_maximum_145_){
_start:
{
size_t v_n_boxed_146_; size_t v_rank_boxed_147_; uint64_t v_remaining_boxed_148_; uint8_t v_positive_boxed_149_; uint64_t v_checksum_boxed_150_; uint32_t v_maximum_boxed_151_; lean_object* v_res_152_; 
v_n_boxed_146_ = lean_unbox_usize(v_n_137_);
lean_dec(v_n_137_);
v_rank_boxed_147_ = lean_unbox_usize(v_rank_138_);
lean_dec(v_rank_138_);
v_remaining_boxed_148_ = lean_unbox_uint64(v_remaining_142_);
lean_dec_ref(v_remaining_142_);
v_positive_boxed_149_ = lean_unbox(v_positive_143_);
v_checksum_boxed_150_ = lean_unbox_uint64(v_checksum_144_);
lean_dec_ref(v_checksum_144_);
v_maximum_boxed_151_ = lean_unbox_uint32(v_maximum_145_);
lean_dec(v_maximum_145_);
v_res_152_ = l_carrying(v_n_boxed_146_, v_rank_boxed_147_, v_p_139_, v_counts_140_, v_scratch_141_, v_remaining_boxed_148_, v_positive_boxed_149_, v_checksum_boxed_150_, v_maximum_boxed_151_);
return v_res_152_;
}
}
LEAN_EXPORT lean_object* l_flipping___boxed(lean_object* v_n_153_, lean_object* v_p_154_, lean_object* v_counts_155_, lean_object* v_work_156_, lean_object* v_remaining_157_, lean_object* v_positive_158_, lean_object* v_checksum_159_, lean_object* v_maximum_160_, lean_object* v_flips_161_){
_start:
{
size_t v_n_boxed_162_; uint64_t v_remaining_boxed_163_; uint8_t v_positive_boxed_164_; uint64_t v_checksum_boxed_165_; uint32_t v_maximum_boxed_166_; uint32_t v_flips_boxed_167_; lean_object* v_res_168_; 
v_n_boxed_162_ = lean_unbox_usize(v_n_153_);
lean_dec(v_n_153_);
v_remaining_boxed_163_ = lean_unbox_uint64(v_remaining_157_);
lean_dec_ref(v_remaining_157_);
v_positive_boxed_164_ = lean_unbox(v_positive_158_);
v_checksum_boxed_165_ = lean_unbox_uint64(v_checksum_159_);
lean_dec_ref(v_checksum_159_);
v_maximum_boxed_166_ = lean_unbox_uint32(v_maximum_160_);
lean_dec(v_maximum_160_);
v_flips_boxed_167_ = lean_unbox_uint32(v_flips_161_);
lean_dec(v_flips_161_);
v_res_168_ = l_flipping(v_n_boxed_162_, v_p_154_, v_counts_155_, v_work_156_, v_remaining_boxed_163_, v_positive_boxed_164_, v_checksum_boxed_165_, v_maximum_boxed_166_, v_flips_boxed_167_);
return v_res_168_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg(lean_object* v___x_169_, lean_object* v_range_170_, lean_object* v_b_171_, lean_object* v_i_172_){
_start:
{
lean_object* v_stop_173_; lean_object* v_step_174_; uint8_t v___x_175_; 
v_stop_173_ = lean_ctor_get(v_range_170_, 1);
v_step_174_ = lean_ctor_get(v_range_170_, 2);
v___x_175_ = lean_nat_dec_lt(v_i_172_, v_stop_173_);
if (v___x_175_ == 0)
{
lean_dec(v_i_172_);
return v_b_171_;
}
else
{
size_t v___x_176_; size_t v___x_177_; uint8_t v___x_178_; lean_object* v___x_179_; lean_object* v___x_180_; 
v___x_176_ = ((size_t)0ULL);
v___x_177_ = lean_usize_of_nat(v___x_169_);
v___x_178_ = lean_byte_array_uget(v_b_171_, v___x_176_);
v___x_179_ = l_rotatePrefix(v_b_171_, v___x_176_, v___x_177_, v___x_178_);
v___x_180_ = lean_nat_add(v_i_172_, v_step_174_);
lean_dec(v_i_172_);
v_b_171_ = v___x_179_;
v_i_172_ = v___x_180_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg___boxed(lean_object* v___x_182_, lean_object* v_range_183_, lean_object* v_b_184_, lean_object* v_i_185_){
_start:
{
lean_object* v_res_186_; 
v_res_186_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg(v___x_182_, v_range_183_, v_b_184_, v_i_185_);
lean_dec_ref(v_range_183_);
lean_dec(v___x_182_);
return v_res_186_;
}
}
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___redArg(lean_object* v_factorials_187_, lean_object* v_as_x27_188_, lean_object* v_b_189_){
_start:
{
if (lean_obj_tag(v_as_x27_188_) == 0)
{
return v_b_189_;
}
else
{
lean_object* v_snd_190_; lean_object* v_head_191_; lean_object* v_tail_192_; lean_object* v_fst_193_; lean_object* v___x_195_; uint8_t v_isShared_196_; uint8_t v_isSharedCheck_222_; 
v_snd_190_ = lean_ctor_get(v_b_189_, 1);
lean_inc(v_snd_190_);
v_head_191_ = lean_ctor_get(v_as_x27_188_, 0);
v_tail_192_ = lean_ctor_get(v_as_x27_188_, 1);
v_fst_193_ = lean_ctor_get(v_b_189_, 0);
v_isSharedCheck_222_ = !lean_is_exclusive(v_b_189_);
if (v_isSharedCheck_222_ == 0)
{
lean_object* v_unused_223_; 
v_unused_223_ = lean_ctor_get(v_b_189_, 1);
lean_dec(v_unused_223_);
v___x_195_ = v_b_189_;
v_isShared_196_ = v_isSharedCheck_222_;
goto v_resetjp_194_;
}
else
{
lean_inc(v_fst_193_);
lean_dec(v_b_189_);
v___x_195_ = lean_box(0);
v_isShared_196_ = v_isSharedCheck_222_;
goto v_resetjp_194_;
}
v_resetjp_194_:
{
lean_object* v_fst_197_; lean_object* v_snd_198_; lean_object* v___x_200_; uint8_t v_isShared_201_; uint8_t v_isSharedCheck_221_; 
v_fst_197_ = lean_ctor_get(v_snd_190_, 0);
v_snd_198_ = lean_ctor_get(v_snd_190_, 1);
v_isSharedCheck_221_ = !lean_is_exclusive(v_snd_190_);
if (v_isSharedCheck_221_ == 0)
{
v___x_200_ = v_snd_190_;
v_isShared_201_ = v_isSharedCheck_221_;
goto v_resetjp_199_;
}
else
{
lean_inc(v_snd_198_);
lean_inc(v_fst_197_);
lean_dec(v_snd_190_);
v___x_200_ = lean_box(0);
v_isShared_201_ = v_isSharedCheck_221_;
goto v_resetjp_199_;
}
v_resetjp_199_:
{
lean_object* v___x_202_; lean_object* v___x_203_; lean_object* v___x_204_; lean_object* v___x_205_; lean_object* v___x_206_; lean_object* v___x_207_; lean_object* v___x_208_; lean_object* v___x_209_; uint8_t v___x_210_; lean_object* v___x_211_; lean_object* v___x_212_; lean_object* v___x_213_; lean_object* v___x_215_; 
v___x_202_ = lean_unsigned_to_nat(1u);
v___x_203_ = lean_unsigned_to_nat(0u);
v___x_204_ = lean_nat_add(v_head_191_, v___x_202_);
v___x_205_ = lean_array_get_borrowed(v___x_203_, v_factorials_187_, v___x_204_);
v___x_206_ = lean_nat_div(v_snd_198_, v___x_205_);
v___x_207_ = lean_nat_mod(v_snd_198_, v___x_205_);
lean_dec(v_snd_198_);
v___x_208_ = lean_nat_add(v___x_204_, v___x_202_);
v___x_209_ = lean_nat_sub(v___x_208_, v___x_206_);
lean_dec(v___x_208_);
v___x_210_ = lean_uint8_of_nat(v___x_209_);
lean_dec(v___x_209_);
v___x_211_ = lean_byte_array_set(v_fst_197_, v___x_204_, v___x_210_);
v___x_212_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_212_, 0, v___x_203_);
lean_ctor_set(v___x_212_, 1, v___x_206_);
lean_ctor_set(v___x_212_, 2, v___x_202_);
v___x_213_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg(v___x_204_, v___x_212_, v_fst_193_, v___x_203_);
lean_dec_ref_known(v___x_212_, 3);
lean_dec(v___x_204_);
if (v_isShared_201_ == 0)
{
lean_ctor_set(v___x_200_, 1, v___x_207_);
lean_ctor_set(v___x_200_, 0, v___x_211_);
v___x_215_ = v___x_200_;
goto v_reusejp_214_;
}
else
{
lean_object* v_reuseFailAlloc_220_; 
v_reuseFailAlloc_220_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v_reuseFailAlloc_220_, 0, v___x_211_);
lean_ctor_set(v_reuseFailAlloc_220_, 1, v___x_207_);
v___x_215_ = v_reuseFailAlloc_220_;
goto v_reusejp_214_;
}
v_reusejp_214_:
{
lean_object* v___x_217_; 
if (v_isShared_196_ == 0)
{
lean_ctor_set(v___x_195_, 1, v___x_215_);
lean_ctor_set(v___x_195_, 0, v___x_213_);
v___x_217_ = v___x_195_;
goto v_reusejp_216_;
}
else
{
lean_object* v_reuseFailAlloc_219_; 
v_reuseFailAlloc_219_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v_reuseFailAlloc_219_, 0, v___x_213_);
lean_ctor_set(v_reuseFailAlloc_219_, 1, v___x_215_);
v___x_217_ = v_reuseFailAlloc_219_;
goto v_reusejp_216_;
}
v_reusejp_216_:
{
v_as_x27_188_ = v_tail_192_;
v_b_189_ = v___x_217_;
goto _start;
}
}
}
}
}
}
}
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___redArg___boxed(lean_object* v_factorials_224_, lean_object* v_as_x27_225_, lean_object* v_b_226_){
_start:
{
lean_object* v_res_227_; 
v_res_227_ = l_List_forIn_x27_loop___at___00chunk_spec__2___redArg(v_factorials_224_, v_as_x27_225_, v_b_226_);
lean_dec(v_as_x27_225_);
lean_dec_ref(v_factorials_224_);
return v_res_227_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0(size_t v_sz_228_, size_t v_i_229_, lean_object* v_bs_230_){
_start:
{
uint8_t v___x_231_; 
v___x_231_ = lean_usize_dec_lt(v_i_229_, v_sz_228_);
if (v___x_231_ == 0)
{
return v_bs_230_;
}
else
{
lean_object* v_v_232_; lean_object* v___x_233_; lean_object* v_bs_x27_234_; uint8_t v___x_235_; size_t v___x_236_; size_t v___x_237_; lean_object* v___x_238_; lean_object* v___x_239_; 
v_v_232_ = lean_array_uget(v_bs_230_, v_i_229_);
v___x_233_ = lean_unsigned_to_nat(0u);
v_bs_x27_234_ = lean_array_uset(v_bs_230_, v_i_229_, v___x_233_);
v___x_235_ = lean_uint8_of_nat(v_v_232_);
lean_dec(v_v_232_);
v___x_236_ = ((size_t)1ULL);
v___x_237_ = lean_usize_add(v_i_229_, v___x_236_);
v___x_238_ = lean_box(v___x_235_);
v___x_239_ = lean_array_uset(v_bs_x27_234_, v_i_229_, v___x_238_);
v_i_229_ = v___x_237_;
v_bs_230_ = v___x_239_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0___boxed(lean_object* v_sz_241_, lean_object* v_i_242_, lean_object* v_bs_243_){
_start:
{
size_t v_sz_boxed_244_; size_t v_i_boxed_245_; lean_object* v_res_246_; 
v_sz_boxed_244_ = lean_unbox_usize(v_sz_241_);
lean_dec(v_sz_241_);
v_i_boxed_245_ = lean_unbox_usize(v_i_242_);
lean_dec(v_i_242_);
v_res_246_ = l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0(v_sz_boxed_244_, v_i_boxed_245_, v_bs_243_);
return v_res_246_;
}
}
static uint64_t _init_l_chunk___closed__0(void){
_start:
{
lean_object* v___x_247_; uint64_t v___x_248_; 
v___x_247_ = lean_unsigned_to_nat(0u);
v___x_248_ = lean_int64_of_nat(v___x_247_);
return v___x_248_;
}
}
LEAN_EXPORT lean_object* l_chunk(lean_object* v_n_249_, lean_object* v_factorials_250_, lean_object* v_start_251_, lean_object* v_count_252_){
_start:
{
lean_object* v___x_253_; size_t v_sz_254_; size_t v___x_255_; lean_object* v___x_256_; lean_object* v_p_257_; uint8_t v___x_258_; lean_object* v___x_259_; lean_object* v___x_260_; lean_object* v_counts_261_; lean_object* v___x_262_; lean_object* v___x_263_; lean_object* v___x_264_; lean_object* v___x_265_; lean_object* v___x_266_; lean_object* v___x_267_; lean_object* v___x_268_; lean_object* v_snd_269_; lean_object* v_fst_270_; lean_object* v_fst_271_; lean_object* v___x_272_; size_t v___x_273_; size_t v___x_274_; uint64_t v___x_275_; lean_object* v___x_276_; lean_object* v___x_277_; uint8_t v___x_278_; uint64_t v___x_279_; uint32_t v___x_280_; lean_object* v___x_281_; 
lean_inc_n(v_n_249_, 2);
v___x_253_ = l_Array_range(v_n_249_);
v_sz_254_ = lean_array_size(v___x_253_);
v___x_255_ = ((size_t)0ULL);
v___x_256_ = l___private_Init_Data_Array_Basic_0__Array_mapMUnsafe_map___at___00chunk_spec__0(v_sz_254_, v___x_255_, v___x_253_);
v_p_257_ = lean_byte_array_mk(v___x_256_);
v___x_258_ = 0;
v___x_259_ = lean_box(v___x_258_);
v___x_260_ = lean_mk_array(v_n_249_, v___x_259_);
v_counts_261_ = lean_byte_array_mk(v___x_260_);
v___x_262_ = lean_unsigned_to_nat(1u);
v___x_263_ = lean_nat_sub(v_n_249_, v___x_262_);
v___x_264_ = l_List_range(v___x_263_);
v___x_265_ = l_List_reverse___redArg(v___x_264_);
lean_inc(v_start_251_);
lean_inc_ref(v_counts_261_);
v___x_266_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_266_, 0, v_counts_261_);
lean_ctor_set(v___x_266_, 1, v_start_251_);
v___x_267_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_267_, 0, v_p_257_);
lean_ctor_set(v___x_267_, 1, v___x_266_);
v___x_268_ = l_List_forIn_x27_loop___at___00chunk_spec__2___redArg(v_factorials_250_, v___x_265_, v___x_267_);
lean_dec(v___x_265_);
v_snd_269_ = lean_ctor_get(v___x_268_, 1);
lean_inc(v_snd_269_);
v_fst_270_ = lean_ctor_get(v___x_268_, 0);
lean_inc(v_fst_270_);
lean_dec_ref(v___x_268_);
v_fst_271_ = lean_ctor_get(v_snd_269_, 0);
lean_inc(v_fst_271_);
lean_dec(v_snd_269_);
v___x_272_ = lean_unsigned_to_nat(0u);
v___x_273_ = lean_usize_of_nat(v_n_249_);
lean_dec(v_n_249_);
v___x_274_ = ((size_t)1ULL);
v___x_275_ = lean_uint64_of_nat(v_count_252_);
v___x_276_ = lean_unsigned_to_nat(2u);
v___x_277_ = lean_nat_mod(v_start_251_, v___x_276_);
lean_dec(v_start_251_);
v___x_278_ = lean_nat_dec_eq(v___x_277_, v___x_272_);
lean_dec(v___x_277_);
v___x_279_ = lean_uint64_once(&l_chunk___closed__0, &l_chunk___closed__0_once, _init_l_chunk___closed__0);
v___x_280_ = 0;
v___x_281_ = l_enumerating(v___x_273_, v___x_274_, v_fst_270_, v_fst_271_, v_counts_261_, v___x_275_, v___x_278_, v___x_279_, v___x_280_);
return v___x_281_;
}
}
LEAN_EXPORT lean_object* l_chunk___boxed(lean_object* v_n_282_, lean_object* v_factorials_283_, lean_object* v_start_284_, lean_object* v_count_285_){
_start:
{
lean_object* v_res_286_; 
v_res_286_ = l_chunk(v_n_282_, v_factorials_283_, v_start_284_, v_count_285_);
lean_dec(v_count_285_);
lean_dec_ref(v_factorials_283_);
return v_res_286_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1(lean_object* v___x_287_, lean_object* v_range_288_, lean_object* v_b_289_, lean_object* v_i_290_, lean_object* v_hs_291_, lean_object* v_hl_292_){
_start:
{
lean_object* v___x_293_; 
v___x_293_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___redArg(v___x_287_, v_range_288_, v_b_289_, v_i_290_);
return v___x_293_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1___boxed(lean_object* v___x_294_, lean_object* v_range_295_, lean_object* v_b_296_, lean_object* v_i_297_, lean_object* v_hs_298_, lean_object* v_hl_299_){
_start:
{
lean_object* v_res_300_; 
v_res_300_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00chunk_spec__1(v___x_294_, v_range_295_, v_b_296_, v_i_297_, v_hs_298_, v_hl_299_);
lean_dec_ref(v_range_295_);
lean_dec(v___x_294_);
return v_res_300_;
}
}
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2(lean_object* v_factorials_301_, lean_object* v_as_302_, lean_object* v_as_x27_303_, lean_object* v_b_304_, lean_object* v_a_305_){
_start:
{
lean_object* v___x_306_; 
v___x_306_ = l_List_forIn_x27_loop___at___00chunk_spec__2___redArg(v_factorials_301_, v_as_x27_303_, v_b_304_);
return v___x_306_;
}
}
LEAN_EXPORT lean_object* l_List_forIn_x27_loop___at___00chunk_spec__2___boxed(lean_object* v_factorials_307_, lean_object* v_as_308_, lean_object* v_as_x27_309_, lean_object* v_b_310_, lean_object* v_a_311_){
_start:
{
lean_object* v_res_312_; 
v_res_312_ = l_List_forIn_x27_loop___at___00chunk_spec__2(v_factorials_307_, v_as_308_, v_as_x27_309_, v_b_310_, v_a_311_);
lean_dec(v_as_x27_309_);
lean_dec(v_as_308_);
lean_dec_ref(v_factorials_307_);
return v_res_312_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0(lean_object* v___x_313_, lean_object* v___x_314_, lean_object* v_n_315_, lean_object* v_a_316_, lean_object* v_x_317_){
_start:
{
lean_object* v___x_318_; lean_object* v___x_319_; 
v___x_318_ = lean_nat_sub(v___x_313_, v___x_314_);
v___x_319_ = l_chunk(v_n_315_, v_a_316_, v___x_314_, v___x_318_);
lean_dec(v___x_318_);
return v___x_319_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0___boxed(lean_object* v___x_320_, lean_object* v___x_321_, lean_object* v_n_322_, lean_object* v_a_323_, lean_object* v_x_324_){
_start:
{
lean_object* v_res_325_; 
v_res_325_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0(v___x_320_, v___x_321_, v_n_322_, v_a_323_, v_x_324_);
lean_dec_ref(v_a_323_);
lean_dec(v___x_320_);
return v_res_325_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg(lean_object* v___x_326_, lean_object* v___y_327_, lean_object* v_n_328_, lean_object* v_a_329_, lean_object* v_range_330_, lean_object* v_b_331_, lean_object* v_i_332_){
_start:
{
lean_object* v_stop_334_; lean_object* v_step_335_; uint8_t v___x_336_; 
v_stop_334_ = lean_ctor_get(v_range_330_, 1);
v_step_335_ = lean_ctor_get(v_range_330_, 2);
v___x_336_ = lean_nat_dec_lt(v_i_332_, v_stop_334_);
if (v___x_336_ == 0)
{
lean_object* v___x_337_; 
lean_dec(v_i_332_);
lean_dec_ref(v_a_329_);
lean_dec(v_n_328_);
v___x_337_ = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(v___x_337_, 0, v_b_331_);
return v___x_337_;
}
else
{
lean_object* v___x_338_; lean_object* v___x_339_; lean_object* v___x_340_; lean_object* v___x_341_; lean_object* v___x_342_; lean_object* v___x_343_; lean_object* v___f_344_; lean_object* v___x_345_; lean_object* v___x_346_; lean_object* v___x_347_; lean_object* v___x_348_; 
v___x_338_ = lean_unsigned_to_nat(1u);
v___x_339_ = lean_nat_mul(v___x_326_, v_i_332_);
v___x_340_ = lean_nat_div(v___x_339_, v___y_327_);
lean_dec(v___x_339_);
v___x_341_ = lean_nat_add(v_i_332_, v___x_338_);
v___x_342_ = lean_nat_mul(v___x_326_, v___x_341_);
lean_dec(v___x_341_);
v___x_343_ = lean_nat_div(v___x_342_, v___y_327_);
lean_dec(v___x_342_);
lean_inc_ref(v_a_329_);
lean_inc(v_n_328_);
v___f_344_ = lean_alloc_closure((void*)(l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___lam__0___boxed), 5, 4);
lean_closure_set(v___f_344_, 0, v___x_343_);
lean_closure_set(v___f_344_, 1, v___x_340_);
lean_closure_set(v___f_344_, 2, v_n_328_);
lean_closure_set(v___f_344_, 3, v_a_329_);
v___x_345_ = lean_unsigned_to_nat(0u);
v___x_346_ = lean_task_spawn(v___f_344_, v___x_345_);
v___x_347_ = lean_array_push(v_b_331_, v___x_346_);
v___x_348_ = lean_nat_add(v_i_332_, v_step_335_);
lean_dec(v_i_332_);
v_b_331_ = v___x_347_;
v_i_332_ = v___x_348_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg___boxed(lean_object* v___x_350_, lean_object* v___y_351_, lean_object* v_n_352_, lean_object* v_a_353_, lean_object* v_range_354_, lean_object* v_b_355_, lean_object* v_i_356_, lean_object* v___y_357_){
_start:
{
lean_object* v_res_358_; 
v_res_358_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg(v___x_350_, v___y_351_, v_n_352_, v_a_353_, v_range_354_, v_b_355_, v_i_356_);
lean_dec_ref(v_range_354_);
lean_dec(v___y_351_);
lean_dec(v___x_350_);
return v_res_358_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3(lean_object* v_as_359_, size_t v_sz_360_, size_t v_i_361_, lean_object* v_b_362_){
_start:
{
uint8_t v___x_364_; 
v___x_364_ = lean_usize_dec_lt(v_i_361_, v_sz_360_);
if (v___x_364_ == 0)
{
lean_object* v___x_365_; 
v___x_365_ = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(v___x_365_, 0, v_b_362_);
return v___x_365_;
}
else
{
lean_object* v_a_366_; lean_object* v___x_367_; lean_object* v_fst_368_; lean_object* v_snd_369_; lean_object* v_fst_370_; lean_object* v_snd_371_; lean_object* v___x_373_; uint8_t v_isShared_374_; uint8_t v_isSharedCheck_393_; 
v_a_366_ = lean_array_uget_borrowed(v_as_359_, v_i_361_);
lean_inc(v_a_366_);
v___x_367_ = lean_task_get_own(v_a_366_);
v_fst_368_ = lean_ctor_get(v___x_367_, 0);
lean_inc(v_fst_368_);
v_snd_369_ = lean_ctor_get(v___x_367_, 1);
lean_inc(v_snd_369_);
lean_dec(v___x_367_);
v_fst_370_ = lean_ctor_get(v_b_362_, 0);
v_snd_371_ = lean_ctor_get(v_b_362_, 1);
v_isSharedCheck_393_ = !lean_is_exclusive(v_b_362_);
if (v_isSharedCheck_393_ == 0)
{
v___x_373_ = v_b_362_;
v_isShared_374_ = v_isSharedCheck_393_;
goto v_resetjp_372_;
}
else
{
lean_inc(v_snd_371_);
lean_inc(v_fst_370_);
lean_dec(v_b_362_);
v___x_373_ = lean_box(0);
v_isShared_374_ = v_isSharedCheck_393_;
goto v_resetjp_372_;
}
v_resetjp_372_:
{
uint64_t v___x_375_; uint64_t v___x_376_; uint64_t v___x_377_; uint32_t v___y_379_; uint32_t v___x_388_; uint32_t v___x_389_; uint8_t v___x_390_; 
v___x_375_ = lean_unbox_uint64(v_fst_370_);
lean_dec(v_fst_370_);
v___x_376_ = lean_unbox_uint64(v_fst_368_);
lean_dec(v_fst_368_);
v___x_377_ = lean_int64_add(v___x_375_, v___x_376_);
v___x_388_ = lean_unbox_uint32(v_snd_371_);
v___x_389_ = lean_unbox_uint32(v_snd_369_);
v___x_390_ = lean_uint32_dec_le(v___x_388_, v___x_389_);
if (v___x_390_ == 0)
{
uint32_t v___x_391_; 
lean_dec(v_snd_369_);
v___x_391_ = lean_unbox_uint32(v_snd_371_);
lean_dec(v_snd_371_);
v___y_379_ = v___x_391_;
goto v___jp_378_;
}
else
{
uint32_t v___x_392_; 
lean_dec(v_snd_371_);
v___x_392_ = lean_unbox_uint32(v_snd_369_);
lean_dec(v_snd_369_);
v___y_379_ = v___x_392_;
goto v___jp_378_;
}
v___jp_378_:
{
lean_object* v___x_380_; lean_object* v___x_381_; lean_object* v___x_383_; 
v___x_380_ = lean_box_uint64(v___x_377_);
v___x_381_ = lean_box_uint32(v___y_379_);
if (v_isShared_374_ == 0)
{
lean_ctor_set(v___x_373_, 1, v___x_381_);
lean_ctor_set(v___x_373_, 0, v___x_380_);
v___x_383_ = v___x_373_;
goto v_reusejp_382_;
}
else
{
lean_object* v_reuseFailAlloc_387_; 
v_reuseFailAlloc_387_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v_reuseFailAlloc_387_, 0, v___x_380_);
lean_ctor_set(v_reuseFailAlloc_387_, 1, v___x_381_);
v___x_383_ = v_reuseFailAlloc_387_;
goto v_reusejp_382_;
}
v_reusejp_382_:
{
size_t v___x_384_; size_t v___x_385_; 
v___x_384_ = ((size_t)1ULL);
v___x_385_ = lean_usize_add(v_i_361_, v___x_384_);
v_i_361_ = v___x_385_;
v_b_362_ = v___x_383_;
goto _start;
}
}
}
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3___boxed(lean_object* v_as_394_, lean_object* v_sz_395_, lean_object* v_i_396_, lean_object* v_b_397_, lean_object* v___y_398_){
_start:
{
size_t v_sz_boxed_399_; size_t v_i_boxed_400_; lean_object* v_res_401_; 
v_sz_boxed_399_ = lean_unbox_usize(v_sz_395_);
lean_dec(v_sz_395_);
v_i_boxed_400_ = lean_unbox_usize(v_i_396_);
lean_dec(v_i_396_);
v_res_401_ = l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3(v_as_394_, v_sz_boxed_399_, v_i_boxed_400_, v_b_397_);
lean_dec_ref(v_as_394_);
return v_res_401_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(lean_object* v_range_402_, lean_object* v_b_403_, lean_object* v_i_404_){
_start:
{
lean_object* v_stop_406_; lean_object* v_step_407_; uint8_t v___x_408_; 
v_stop_406_ = lean_ctor_get(v_range_402_, 1);
v_step_407_ = lean_ctor_get(v_range_402_, 2);
v___x_408_ = lean_nat_dec_lt(v_i_404_, v_stop_406_);
if (v___x_408_ == 0)
{
lean_object* v___x_409_; 
lean_dec(v_i_404_);
v___x_409_ = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(v___x_409_, 0, v_b_403_);
return v___x_409_;
}
else
{
lean_object* v___x_410_; lean_object* v___x_411_; lean_object* v___x_412_; lean_object* v___x_413_; lean_object* v___x_414_; lean_object* v___x_415_; lean_object* v___x_416_; lean_object* v___x_417_; 
v___x_410_ = lean_unsigned_to_nat(0u);
v___x_411_ = lean_array_get_size(v_b_403_);
v___x_412_ = lean_unsigned_to_nat(1u);
v___x_413_ = lean_nat_sub(v___x_411_, v___x_412_);
v___x_414_ = lean_array_get_borrowed(v___x_410_, v_b_403_, v___x_413_);
lean_dec(v___x_413_);
v___x_415_ = lean_nat_mul(v___x_414_, v_i_404_);
v___x_416_ = lean_array_push(v_b_403_, v___x_415_);
v___x_417_ = lean_nat_add(v_i_404_, v_step_407_);
lean_dec(v_i_404_);
v_b_403_ = v___x_416_;
v_i_404_ = v___x_417_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___boxed(lean_object* v_range_419_, lean_object* v_b_420_, lean_object* v_i_421_, lean_object* v___y_422_){
_start:
{
lean_object* v_res_423_; 
v_res_423_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v_range_419_, v_b_420_, v_i_421_);
lean_dec_ref(v_range_419_);
return v_res_423_;
}
}
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(lean_object* v_s_424_){
_start:
{
lean_object* v___x_426_; lean_object* v_putStr_427_; lean_object* v___x_428_; 
v___x_426_ = lean_get_stdout();
v_putStr_427_ = lean_ctor_get(v___x_426_, 4);
lean_inc_ref(v_putStr_427_);
lean_dec_ref(v___x_426_);
v___x_428_ = lean_apply_2(v_putStr_427_, v_s_424_, lean_box(0));
return v___x_428_;
}
}
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0___boxed(lean_object* v_s_429_, lean_object* v_a_430_){
_start:
{
lean_object* v_res_431_; 
v_res_431_ = l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(v_s_429_);
return v_res_431_;
}
}
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0(lean_object* v_s_432_){
_start:
{
uint32_t v___x_434_; lean_object* v___x_435_; lean_object* v___x_436_; 
v___x_434_ = 10;
v___x_435_ = lean_string_push(v_s_432_, v___x_434_);
v___x_436_ = l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(v___x_435_);
return v___x_436_;
}
}
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0___boxed(lean_object* v_s_437_, lean_object* v_a_438_){
_start:
{
lean_object* v_res_439_; 
v_res_439_ = l_IO_println___at___00main_spec__0(v_s_437_);
return v_res_439_;
}
}
LEAN_EXPORT lean_object* _lean_main(lean_object* v_args_449_){
_start:
{
lean_object* v___y_452_; uint64_t v_checksum_453_; uint32_t v_maximum_454_; lean_object* v___y_471_; lean_object* v___y_472_; uint64_t v___y_473_; lean_object* v___y_474_; lean_object* v___y_475_; lean_object* v___y_476_; uint32_t v___y_477_; lean_object* v___y_478_; lean_object* v___x_510_; lean_object* v___y_512_; 
v___x_510_ = lean_unsigned_to_nat(0u);
if (lean_obj_tag(v_args_449_) == 0)
{
lean_object* v___x_541_; 
v___x_541_ = ((lean_object*)(l_main___closed__5));
v___y_512_ = v___x_541_;
goto v___jp_511_;
}
else
{
lean_object* v_head_542_; 
v_head_542_ = lean_ctor_get(v_args_449_, 0);
lean_inc(v_head_542_);
lean_dec_ref_known(v_args_449_, 2);
v___y_512_ = v_head_542_;
goto v___jp_511_;
}
v___jp_451_:
{
lean_object* v___x_455_; lean_object* v___x_456_; lean_object* v___x_457_; lean_object* v___x_458_; lean_object* v___x_459_; lean_object* v___x_460_; lean_object* v___x_461_; lean_object* v___x_462_; lean_object* v___x_463_; lean_object* v___x_464_; lean_object* v___x_465_; lean_object* v___x_466_; 
v___x_455_ = lean_int64_to_int_sint(v_checksum_453_);
v___x_456_ = l_Int_repr(v___x_455_);
lean_dec(v___x_455_);
v___x_457_ = ((lean_object*)(l_main___closed__0));
v___x_458_ = lean_string_append(v___x_456_, v___x_457_);
v___x_459_ = l_Nat_reprFast(v___y_452_);
v___x_460_ = lean_string_append(v___x_458_, v___x_459_);
lean_dec_ref(v___x_459_);
v___x_461_ = ((lean_object*)(l_main___closed__1));
v___x_462_ = lean_string_append(v___x_460_, v___x_461_);
v___x_463_ = lean_uint32_to_nat(v_maximum_454_);
v___x_464_ = l_Nat_reprFast(v___x_463_);
v___x_465_ = lean_string_append(v___x_462_, v___x_464_);
lean_dec_ref(v___x_464_);
v___x_466_ = l_IO_println___at___00main_spec__0(v___x_465_);
if (lean_obj_tag(v___x_466_) == 0)
{
lean_object* v___x_467_; lean_object* v_flush_468_; lean_object* v___x_469_; 
lean_dec_ref_known(v___x_466_, 1);
v___x_467_ = lean_get_stdout();
v_flush_468_ = lean_ctor_get(v___x_467_, 0);
lean_inc_ref(v_flush_468_);
lean_dec_ref(v___x_467_);
v___x_469_ = lean_apply_1(v_flush_468_, lean_box(0));
return v___x_469_;
}
else
{
return v___x_466_;
}
}
v___jp_470_:
{
lean_object* v___x_479_; lean_object* v___x_480_; lean_object* v___x_481_; 
v___x_479_ = lean_mk_empty_array_with_capacity(v___y_475_);
lean_inc(v___y_478_);
lean_inc(v___y_475_);
v___x_480_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_480_, 0, v___y_475_);
lean_ctor_set(v___x_480_, 1, v___y_478_);
lean_ctor_set(v___x_480_, 2, v___y_472_);
lean_inc(v___y_476_);
v___x_481_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg(v___y_474_, v___y_478_, v___y_476_, v___y_471_, v___x_480_, v___x_479_, v___y_475_);
lean_dec_ref_known(v___x_480_, 3);
lean_dec(v___y_478_);
lean_dec(v___y_474_);
if (lean_obj_tag(v___x_481_) == 0)
{
lean_object* v_a_482_; lean_object* v___x_483_; lean_object* v___x_484_; lean_object* v___x_485_; size_t v_sz_486_; size_t v___x_487_; lean_object* v___x_488_; 
v_a_482_ = lean_ctor_get(v___x_481_, 0);
lean_inc(v_a_482_);
lean_dec_ref_known(v___x_481_, 1);
v___x_483_ = lean_box_uint64(v___y_473_);
v___x_484_ = lean_box_uint32(v___y_477_);
v___x_485_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_485_, 0, v___x_483_);
lean_ctor_set(v___x_485_, 1, v___x_484_);
v_sz_486_ = lean_array_size(v_a_482_);
v___x_487_ = ((size_t)0ULL);
v___x_488_ = l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__3(v_a_482_, v_sz_486_, v___x_487_, v___x_485_);
lean_dec(v_a_482_);
if (lean_obj_tag(v___x_488_) == 0)
{
lean_object* v_a_489_; lean_object* v_fst_490_; lean_object* v_snd_491_; uint64_t v___x_492_; uint32_t v___x_493_; 
v_a_489_ = lean_ctor_get(v___x_488_, 0);
lean_inc(v_a_489_);
lean_dec_ref_known(v___x_488_, 1);
v_fst_490_ = lean_ctor_get(v_a_489_, 0);
lean_inc(v_fst_490_);
v_snd_491_ = lean_ctor_get(v_a_489_, 1);
lean_inc(v_snd_491_);
lean_dec(v_a_489_);
v___x_492_ = lean_unbox_uint64(v_fst_490_);
lean_dec(v_fst_490_);
v___x_493_ = lean_unbox_uint32(v_snd_491_);
lean_dec(v_snd_491_);
v___y_452_ = v___y_476_;
v_checksum_453_ = v___x_492_;
v_maximum_454_ = v___x_493_;
goto v___jp_451_;
}
else
{
lean_object* v_a_494_; lean_object* v___x_496_; uint8_t v_isShared_497_; uint8_t v_isSharedCheck_501_; 
lean_dec(v___y_476_);
v_a_494_ = lean_ctor_get(v___x_488_, 0);
v_isSharedCheck_501_ = !lean_is_exclusive(v___x_488_);
if (v_isSharedCheck_501_ == 0)
{
v___x_496_ = v___x_488_;
v_isShared_497_ = v_isSharedCheck_501_;
goto v_resetjp_495_;
}
else
{
lean_inc(v_a_494_);
lean_dec(v___x_488_);
v___x_496_ = lean_box(0);
v_isShared_497_ = v_isSharedCheck_501_;
goto v_resetjp_495_;
}
v_resetjp_495_:
{
lean_object* v___x_499_; 
if (v_isShared_497_ == 0)
{
v___x_499_ = v___x_496_;
goto v_reusejp_498_;
}
else
{
lean_object* v_reuseFailAlloc_500_; 
v_reuseFailAlloc_500_ = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(v_reuseFailAlloc_500_, 0, v_a_494_);
v___x_499_ = v_reuseFailAlloc_500_;
goto v_reusejp_498_;
}
v_reusejp_498_:
{
return v___x_499_;
}
}
}
}
else
{
lean_object* v_a_502_; lean_object* v___x_504_; uint8_t v_isShared_505_; uint8_t v_isSharedCheck_509_; 
lean_dec(v___y_476_);
v_a_502_ = lean_ctor_get(v___x_481_, 0);
v_isSharedCheck_509_ = !lean_is_exclusive(v___x_481_);
if (v_isSharedCheck_509_ == 0)
{
v___x_504_ = v___x_481_;
v_isShared_505_ = v_isSharedCheck_509_;
goto v_resetjp_503_;
}
else
{
lean_inc(v_a_502_);
lean_dec(v___x_481_);
v___x_504_ = lean_box(0);
v_isShared_505_ = v_isSharedCheck_509_;
goto v_resetjp_503_;
}
v_resetjp_503_:
{
lean_object* v___x_507_; 
if (v_isShared_505_ == 0)
{
v___x_507_ = v___x_504_;
goto v_reusejp_506_;
}
else
{
lean_object* v_reuseFailAlloc_508_; 
v_reuseFailAlloc_508_ = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(v_reuseFailAlloc_508_, 0, v_a_502_);
v___x_507_ = v_reuseFailAlloc_508_;
goto v_reusejp_506_;
}
v_reusejp_506_:
{
return v___x_507_;
}
}
}
}
v___jp_511_:
{
lean_object* v___x_513_; lean_object* v___x_514_; lean_object* v_n_515_; lean_object* v___x_516_; uint8_t v___x_517_; 
v___x_513_ = lean_string_utf8_byte_size(v___y_512_);
v___x_514_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_514_, 0, v___y_512_);
lean_ctor_set(v___x_514_, 1, v___x_510_);
lean_ctor_set(v___x_514_, 2, v___x_513_);
v_n_515_ = l_String_Slice_toNat_x21(v___x_514_);
lean_dec_ref_known(v___x_514_, 3);
v___x_516_ = lean_unsigned_to_nat(16u);
v___x_517_ = lean_nat_dec_lt(v___x_516_, v_n_515_);
if (v___x_517_ == 0)
{
uint64_t v_checksum_518_; uint32_t v_maximum_519_; lean_object* v___x_520_; uint8_t v___x_521_; 
v_checksum_518_ = lean_uint64_once(&l_chunk___closed__0, &l_chunk___closed__0_once, _init_l_chunk___closed__0);
v_maximum_519_ = 0;
v___x_520_ = lean_unsigned_to_nat(2u);
v___x_521_ = lean_nat_dec_le(v___x_520_, v_n_515_);
if (v___x_521_ == 0)
{
v___y_452_ = v_n_515_;
v_checksum_453_ = v_checksum_518_;
v_maximum_454_ = v_maximum_519_;
goto v___jp_451_;
}
else
{
lean_object* v___x_522_; lean_object* v_factorials_523_; lean_object* v___x_524_; lean_object* v___x_525_; lean_object* v___x_526_; 
v___x_522_ = lean_unsigned_to_nat(1u);
v_factorials_523_ = ((lean_object*)(l_main___closed__2));
v___x_524_ = lean_nat_add(v_n_515_, v___x_522_);
v___x_525_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_525_, 0, v___x_522_);
lean_ctor_set(v___x_525_, 1, v___x_524_);
lean_ctor_set(v___x_525_, 2, v___x_522_);
v___x_526_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v___x_525_, v_factorials_523_, v___x_522_);
lean_dec_ref_known(v___x_525_, 3);
if (lean_obj_tag(v___x_526_) == 0)
{
lean_object* v_a_527_; lean_object* v___x_528_; lean_object* v___x_529_; uint8_t v___x_530_; 
v_a_527_ = lean_ctor_get(v___x_526_, 0);
lean_inc(v_a_527_);
lean_dec_ref_known(v___x_526_, 1);
v___x_528_ = lean_array_get(v___x_510_, v_a_527_, v_n_515_);
v___x_529_ = lean_unsigned_to_nat(8u);
v___x_530_ = lean_nat_dec_le(v___x_529_, v___x_528_);
if (v___x_530_ == 0)
{
lean_inc(v___x_528_);
v___y_471_ = v_a_527_;
v___y_472_ = v___x_522_;
v___y_473_ = v_checksum_518_;
v___y_474_ = v___x_528_;
v___y_475_ = v___x_510_;
v___y_476_ = v_n_515_;
v___y_477_ = v_maximum_519_;
v___y_478_ = v___x_528_;
goto v___jp_470_;
}
else
{
v___y_471_ = v_a_527_;
v___y_472_ = v___x_522_;
v___y_473_ = v_checksum_518_;
v___y_474_ = v___x_528_;
v___y_475_ = v___x_510_;
v___y_476_ = v_n_515_;
v___y_477_ = v_maximum_519_;
v___y_478_ = v___x_529_;
goto v___jp_470_;
}
}
else
{
lean_object* v_a_531_; lean_object* v___x_533_; uint8_t v_isShared_534_; uint8_t v_isSharedCheck_538_; 
lean_dec(v_n_515_);
v_a_531_ = lean_ctor_get(v___x_526_, 0);
v_isSharedCheck_538_ = !lean_is_exclusive(v___x_526_);
if (v_isSharedCheck_538_ == 0)
{
v___x_533_ = v___x_526_;
v_isShared_534_ = v_isSharedCheck_538_;
goto v_resetjp_532_;
}
else
{
lean_inc(v_a_531_);
lean_dec(v___x_526_);
v___x_533_ = lean_box(0);
v_isShared_534_ = v_isSharedCheck_538_;
goto v_resetjp_532_;
}
v_resetjp_532_:
{
lean_object* v___x_536_; 
if (v_isShared_534_ == 0)
{
v___x_536_ = v___x_533_;
goto v_reusejp_535_;
}
else
{
lean_object* v_reuseFailAlloc_537_; 
v_reuseFailAlloc_537_ = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(v_reuseFailAlloc_537_, 0, v_a_531_);
v___x_536_ = v_reuseFailAlloc_537_;
goto v_reusejp_535_;
}
v_reusejp_535_:
{
return v___x_536_;
}
}
}
}
}
else
{
lean_object* v___x_539_; lean_object* v___x_540_; 
lean_dec(v_n_515_);
v___x_539_ = ((lean_object*)(l_main___closed__4));
v___x_540_ = lean_alloc_ctor(1, 1, 0);
lean_ctor_set(v___x_540_, 0, v___x_539_);
return v___x_540_;
}
}
}
}
LEAN_EXPORT lean_object* l_main___boxed(lean_object* v_args_543_, lean_object* v_a_544_){
_start:
{
lean_object* v_res_545_; 
v_res_545_ = _lean_main(v_args_543_);
return v_res_545_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(lean_object* v_range_546_, lean_object* v_b_547_, lean_object* v_i_548_, lean_object* v_hs_549_, lean_object* v_hl_550_){
_start:
{
lean_object* v___x_552_; 
v___x_552_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v_range_546_, v_b_547_, v_i_548_);
return v___x_552_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___boxed(lean_object* v_range_553_, lean_object* v_b_554_, lean_object* v_i_555_, lean_object* v_hs_556_, lean_object* v_hl_557_, lean_object* v___y_558_){
_start:
{
lean_object* v_res_559_; 
v_res_559_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(v_range_553_, v_b_554_, v_i_555_, v_hs_556_, v_hl_557_);
lean_dec_ref(v_range_553_);
return v_res_559_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2(lean_object* v___x_560_, lean_object* v___y_561_, lean_object* v_n_562_, lean_object* v_a_563_, lean_object* v_range_564_, lean_object* v_b_565_, lean_object* v_i_566_, lean_object* v_hs_567_, lean_object* v_hl_568_){
_start:
{
lean_object* v___x_570_; 
v___x_570_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___redArg(v___x_560_, v___y_561_, v_n_562_, v_a_563_, v_range_564_, v_b_565_, v_i_566_);
return v___x_570_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2___boxed(lean_object* v___x_571_, lean_object* v___y_572_, lean_object* v_n_573_, lean_object* v_a_574_, lean_object* v_range_575_, lean_object* v_b_576_, lean_object* v_i_577_, lean_object* v_hs_578_, lean_object* v_hl_579_, lean_object* v___y_580_){
_start:
{
lean_object* v_res_581_; 
v_res_581_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__2(v___x_571_, v___y_572_, v_n_573_, v_a_574_, v_range_575_, v_b_576_, v_i_577_, v_hs_578_, v_hl_579_);
lean_dec_ref(v_range_575_);
lean_dec(v___y_572_);
lean_dec(v___x_571_);
return v_res_581_;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Std(uint8_t builtin);
void lean_initialize_runtime_module();
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_fannkuchredux(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
lean_initialize_runtime_module();
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_Std(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
return lean_io_result_mk_ok(lean_box(0));
}
char ** lean_setup_args(int argc, char ** argv);
#if defined(WIN32) || defined(_WIN32)
#include <windows.h>
#endif
lean_object* run_main(int argc, char ** argv) {
    lean_object* in = lean_box(0);
    int i = argc;
    while (i > 1) {
      lean_object* n;
      i--;
      n = lean_alloc_ctor(1,2,0); lean_ctor_set(n, 0, lean_mk_string(argv[i])); lean_ctor_set(n, 1, in);
      in = n;
    }
    return _lean_main(in);
}
int main(int argc, char ** argv) {
#if defined(WIN32) || defined(_WIN32)
  SetErrorMode(SEM_FAILCRITICALERRORS);
  SetConsoleOutputCP(CP_UTF8);
#endif
  lean_object* res;
  argv = lean_setup_args(argc, argv);
  res = initialize_fannkuchredux(1 /* builtin */);
  lean_io_mark_end_initialization();
  if (lean_io_result_is_ok(res)) {
    lean_dec_ref(res);
    lean_init_task_manager();
    res = lean_run_main(&run_main, argc, argv);
  }
  lean_finalize_task_manager();
  if (lean_io_result_is_ok(res)) {
    int ret = 0;
    lean_dec_ref(res);
    return ret;
  } else {
    lean_io_result_show_error(res);
    lean_dec_ref(res);
    return 1;
  }
}
#ifdef __cplusplus
}
#endif
