// Lean compiler output
// Module: binarytrees
// Imports: public import Init public meta import Init public import Std
#include <lean/lean.h>

#include <stdatomic.h>
#include <stdio.h>
static _Atomic unsigned long long bench_nodes;
static lean_object* bench_node(unsigned t, unsigned o, unsigned s) {
  atomic_fetch_add_explicit(&bench_nodes, 1, memory_order_relaxed);
  return lean_alloc_ctor(t, o, s);
}
__attribute__((destructor)) static void bench_node_report(void) {
  fprintf(stderr, "{\"node_allocations\":%llu}\n", atomic_load(&bench_nodes));
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
lean_object* lean_nat_sub(lean_object*, lean_object*);
lean_object* lean_nat_add(lean_object*, lean_object*);
lean_object* lean_nat_pow(lean_object*, lean_object*);
uint64_t lean_uint64_of_nat(lean_object*);
uint8_t lean_nat_dec_eq(lean_object*, lean_object*);
uint64_t lean_uint64_shift_left(uint64_t, uint64_t);
uint64_t lean_uint64_add(uint64_t, uint64_t);
lean_object* lean_task_spawn(lean_object*, lean_object*);
lean_object* lean_array_push(lean_object*, lean_object*);
lean_object* l_Nat_reprFast(lean_object*);
lean_object* lean_string_append(lean_object*, lean_object*);
lean_object* lean_string_push(lean_object*, uint32_t);
lean_object* lean_get_stdout();
lean_object* lean_mk_empty_array_with_capacity(lean_object*);
size_t lean_array_size(lean_object*);
uint8_t lean_usize_dec_lt(size_t, size_t);
lean_object* lean_array_uget_borrowed(lean_object*, size_t);
lean_object* lean_task_get_own(lean_object*);
size_t lean_usize_add(size_t, size_t);
lean_object* lean_string_utf8_byte_size(lean_object*);
lean_object* l_String_Slice_toNat_x21(lean_object*);
uint8_t lean_nat_dec_le(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorIdx(lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorIdx___boxed(lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorElim___redArg(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorElim(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorElim___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_nil_elim___redArg(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_nil_elim(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_node_elim___redArg(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_node_elim(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_instInhabitedTree_default;
LEAN_EXPORT lean_object* l_instInhabitedTree;
LEAN_EXPORT lean_object* l_makeTree(lean_object*, uint64_t);
LEAN_EXPORT lean_object* l_makeTree___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_checkTree(lean_object*);
LEAN_EXPORT lean_object* l_checkTree___boxed(lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_manyTrees(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_manyTrees___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0___boxed(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(lean_object*);
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0(lean_object*);
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0___boxed(lean_object*, lean_object*);
static const lean_string_object l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 10, .m_capacity = 10, .m_length = 9, .m_data = "\t check: "};
static const lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__0 = (const lean_object*)&l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__0_value;
static const lean_string_object l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__1_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 18, .m_capacity = 18, .m_length = 17, .m_data = "\t trees of depth "};
static const lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__1 = (const lean_object*)&l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__1_value;
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2(lean_object*, size_t, size_t, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
static const lean_string_object l_main___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 23, .m_capacity = 23, .m_length = 22, .m_data = "stretch tree of depth "};
static const lean_object* l_main___closed__0 = (const lean_object*)&l_main___closed__0_value;
static const lean_array_object l_main___closed__1_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_array_object) + sizeof(void*)*0, .m_other = 0, .m_tag = 246}, .m_size = 0, .m_capacity = 0, .m_data = {}};
static const lean_object* l_main___closed__1 = (const lean_object*)&l_main___closed__1_value;
static const lean_string_object l_main___closed__2_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 26, .m_capacity = 26, .m_length = 25, .m_data = "long lived tree of depth "};
static const lean_object* l_main___closed__2 = (const lean_object*)&l_main___closed__2_value;
static const lean_string_object l_main___closed__3_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 2, .m_capacity = 2, .m_length = 1, .m_data = "0"};
static const lean_object* l_main___closed__3 = (const lean_object*)&l_main___closed__3_value;
LEAN_EXPORT lean_object* _lean_main(lean_object*);
LEAN_EXPORT lean_object* l_main___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* l_Tree_ctorIdx(lean_object* v_x_1_){
_start:
{
if (lean_obj_tag(v_x_1_) == 0)
{
lean_object* v___x_2_; 
v___x_2_ = lean_unsigned_to_nat(0u);
return v___x_2_;
}
else
{
lean_object* v___x_3_; 
v___x_3_ = lean_unsigned_to_nat(1u);
return v___x_3_;
}
}
}
LEAN_EXPORT lean_object* l_Tree_ctorIdx___boxed(lean_object* v_x_4_){
_start:
{
lean_object* v_res_5_; 
v_res_5_ = l_Tree_ctorIdx(v_x_4_);
lean_dec(v_x_4_);
return v_res_5_;
}
}
LEAN_EXPORT lean_object* l_Tree_ctorElim___redArg(lean_object* v_t_6_, lean_object* v_k_7_){
_start:
{
if (lean_obj_tag(v_t_6_) == 0)
{
return v_k_7_;
}
else
{
uint64_t v_serial_8_; lean_object* v_left_9_; lean_object* v_right_10_; lean_object* v___x_11_; lean_object* v___x_12_; 
v_serial_8_ = lean_ctor_get_uint64(v_t_6_, sizeof(void*)*2);
v_left_9_ = lean_ctor_get(v_t_6_, 0);
lean_inc(v_left_9_);
v_right_10_ = lean_ctor_get(v_t_6_, 1);
lean_inc(v_right_10_);
lean_dec_ref_known(v_t_6_, 2);
v___x_11_ = lean_box_uint64(v_serial_8_);
v___x_12_ = lean_apply_3(v_k_7_, v___x_11_, v_left_9_, v_right_10_);
return v___x_12_;
}
}
}
LEAN_EXPORT lean_object* l_Tree_ctorElim(lean_object* v_motive_13_, lean_object* v_ctorIdx_14_, lean_object* v_t_15_, lean_object* v_h_16_, lean_object* v_k_17_){
_start:
{
lean_object* v___x_18_; 
v___x_18_ = l_Tree_ctorElim___redArg(v_t_15_, v_k_17_);
return v___x_18_;
}
}
LEAN_EXPORT lean_object* l_Tree_ctorElim___boxed(lean_object* v_motive_19_, lean_object* v_ctorIdx_20_, lean_object* v_t_21_, lean_object* v_h_22_, lean_object* v_k_23_){
_start:
{
lean_object* v_res_24_; 
v_res_24_ = l_Tree_ctorElim(v_motive_19_, v_ctorIdx_20_, v_t_21_, v_h_22_, v_k_23_);
lean_dec(v_ctorIdx_20_);
return v_res_24_;
}
}
LEAN_EXPORT lean_object* l_Tree_nil_elim___redArg(lean_object* v_t_25_, lean_object* v_nil_26_){
_start:
{
lean_object* v___x_27_; 
v___x_27_ = l_Tree_ctorElim___redArg(v_t_25_, v_nil_26_);
return v___x_27_;
}
}
LEAN_EXPORT lean_object* l_Tree_nil_elim(lean_object* v_motive_28_, lean_object* v_t_29_, lean_object* v_h_30_, lean_object* v_nil_31_){
_start:
{
lean_object* v___x_32_; 
v___x_32_ = l_Tree_ctorElim___redArg(v_t_29_, v_nil_31_);
return v___x_32_;
}
}
LEAN_EXPORT lean_object* l_Tree_node_elim___redArg(lean_object* v_t_33_, lean_object* v_node_34_){
_start:
{
lean_object* v___x_35_; 
v___x_35_ = l_Tree_ctorElim___redArg(v_t_33_, v_node_34_);
return v___x_35_;
}
}
LEAN_EXPORT lean_object* l_Tree_node_elim(lean_object* v_motive_36_, lean_object* v_t_37_, lean_object* v_h_38_, lean_object* v_node_39_){
_start:
{
lean_object* v___x_40_; 
v___x_40_ = l_Tree_ctorElim___redArg(v_t_37_, v_node_39_);
return v___x_40_;
}
}
static lean_object* _init_l_instInhabitedTree_default(void){
_start:
{
lean_object* v___x_41_; 
v___x_41_ = lean_box(0);
return v___x_41_;
}
}
static lean_object* _init_l_instInhabitedTree(void){
_start:
{
lean_object* v___x_42_; 
v___x_42_ = lean_box(0);
return v___x_42_;
}
}
LEAN_EXPORT lean_object* l_makeTree(lean_object* v_x_43_, uint64_t v_x_44_){
_start:
{
lean_object* v_zero_45_; uint8_t v_isZero_46_; 
v_zero_45_ = lean_unsigned_to_nat(0u);
v_isZero_46_ = lean_nat_dec_eq(v_x_43_, v_zero_45_);
if (v_isZero_46_ == 1)
{
lean_object* v___x_47_; lean_object* v___x_48_; 
v___x_47_ = lean_box(0);
v___x_48_ = bench_node(1, 2, 8);
lean_ctor_set(v___x_48_, 0, v___x_47_);
lean_ctor_set(v___x_48_, 1, v___x_47_);
lean_ctor_set_uint64(v___x_48_, sizeof(void*)*2, v_x_44_);
return v___x_48_;
}
else
{
lean_object* v_one_49_; lean_object* v_n_50_; uint64_t v___x_51_; uint64_t v___x_52_; lean_object* v___x_53_; uint64_t v___x_54_; lean_object* v___x_55_; lean_object* v___x_56_; 
v_one_49_ = lean_unsigned_to_nat(1u);
v_n_50_ = lean_nat_sub(v_x_43_, v_one_49_);
v___x_51_ = 1ULL;
v___x_52_ = lean_uint64_shift_left(v_x_44_, v___x_51_);
v___x_53_ = l_makeTree(v_n_50_, v___x_52_);
v___x_54_ = lean_uint64_add(v___x_52_, v___x_51_);
v___x_55_ = l_makeTree(v_n_50_, v___x_54_);
lean_dec(v_n_50_);
v___x_56_ = bench_node(1, 2, 8);
lean_ctor_set(v___x_56_, 0, v___x_53_);
lean_ctor_set(v___x_56_, 1, v___x_55_);
lean_ctor_set_uint64(v___x_56_, sizeof(void*)*2, v_x_44_);
return v___x_56_;
}
}
}
LEAN_EXPORT lean_object* l_makeTree___boxed(lean_object* v_x_57_, lean_object* v_x_58_){
_start:
{
uint64_t v_x_64__boxed_59_; lean_object* v_res_60_; 
v_x_64__boxed_59_ = lean_unbox_uint64(v_x_58_);
lean_dec_ref(v_x_58_);
v_res_60_ = l_makeTree(v_x_57_, v_x_64__boxed_59_);
lean_dec(v_x_57_);
return v_res_60_;
}
}
LEAN_EXPORT lean_object* l_checkTree(lean_object* v_x_61_){
_start:
{
if (lean_obj_tag(v_x_61_) == 0)
{
lean_object* v___x_62_; 
v___x_62_ = lean_unsigned_to_nat(0u);
return v___x_62_;
}
else
{
lean_object* v_left_63_; lean_object* v_right_64_; lean_object* v___x_65_; lean_object* v___x_66_; lean_object* v___x_67_; lean_object* v___x_68_; lean_object* v___x_69_; 
v_left_63_ = lean_ctor_get(v_x_61_, 0);
v_right_64_ = lean_ctor_get(v_x_61_, 1);
v___x_65_ = lean_unsigned_to_nat(1u);
v___x_66_ = l_checkTree(v_left_63_);
v___x_67_ = lean_nat_add(v___x_65_, v___x_66_);
lean_dec(v___x_66_);
v___x_68_ = l_checkTree(v_right_64_);
v___x_69_ = lean_nat_add(v___x_67_, v___x_68_);
lean_dec(v___x_68_);
lean_dec(v___x_67_);
return v___x_69_;
}
}
}
LEAN_EXPORT lean_object* l_checkTree___boxed(lean_object* v_x_70_){
_start:
{
lean_object* v_res_71_; 
v_res_71_ = l_checkTree(v_x_70_);
lean_dec(v_x_70_);
return v_res_71_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg(lean_object* v_depth_72_, lean_object* v_range_73_, lean_object* v_b_74_, lean_object* v_i_75_){
_start:
{
lean_object* v_stop_76_; lean_object* v_step_77_; uint8_t v___x_78_; 
v_stop_76_ = lean_ctor_get(v_range_73_, 1);
v_step_77_ = lean_ctor_get(v_range_73_, 2);
v___x_78_ = lean_nat_dec_lt(v_i_75_, v_stop_76_);
if (v___x_78_ == 0)
{
lean_dec(v_i_75_);
return v_b_74_;
}
else
{
uint64_t v___x_79_; lean_object* v___x_80_; lean_object* v___x_81_; lean_object* v___x_82_; lean_object* v___x_83_; 
v___x_79_ = lean_uint64_of_nat(v_i_75_);
v___x_80_ = l_makeTree(v_depth_72_, v___x_79_);
v___x_81_ = l_checkTree(v___x_80_);
lean_dec(v___x_80_);
v___x_82_ = lean_nat_add(v_b_74_, v___x_81_);
lean_dec(v___x_81_);
lean_dec(v_b_74_);
v___x_83_ = lean_nat_add(v_i_75_, v_step_77_);
lean_dec(v_i_75_);
v_b_74_ = v___x_82_;
v_i_75_ = v___x_83_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg___boxed(lean_object* v_depth_85_, lean_object* v_range_86_, lean_object* v_b_87_, lean_object* v_i_88_){
_start:
{
lean_object* v_res_89_; 
v_res_89_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg(v_depth_85_, v_range_86_, v_b_87_, v_i_88_);
lean_dec_ref(v_range_86_);
lean_dec(v_depth_85_);
return v_res_89_;
}
}
LEAN_EXPORT lean_object* l_manyTrees(lean_object* v_depth_90_, lean_object* v_count_91_){
_start:
{
lean_object* v_total_92_; lean_object* v___x_93_; lean_object* v___x_94_; lean_object* v___x_95_; 
v_total_92_ = lean_unsigned_to_nat(0u);
v___x_93_ = lean_unsigned_to_nat(1u);
v___x_94_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_94_, 0, v_total_92_);
lean_ctor_set(v___x_94_, 1, v_count_91_);
lean_ctor_set(v___x_94_, 2, v___x_93_);
v___x_95_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg(v_depth_90_, v___x_94_, v_total_92_, v_total_92_);
lean_dec_ref_known(v___x_94_, 3);
return v___x_95_;
}
}
LEAN_EXPORT lean_object* l_manyTrees___boxed(lean_object* v_depth_96_, lean_object* v_count_97_){
_start:
{
lean_object* v_res_98_; 
v_res_98_ = l_manyTrees(v_depth_96_, v_count_97_);
lean_dec(v_depth_96_);
return v_res_98_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0(lean_object* v_depth_99_, lean_object* v_range_100_, lean_object* v_b_101_, lean_object* v_i_102_, lean_object* v_hs_103_, lean_object* v_hl_104_){
_start:
{
lean_object* v___x_105_; 
v___x_105_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___redArg(v_depth_99_, v_range_100_, v_b_101_, v_i_102_);
return v___x_105_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0___boxed(lean_object* v_depth_106_, lean_object* v_range_107_, lean_object* v_b_108_, lean_object* v_i_109_, lean_object* v_hs_110_, lean_object* v_hl_111_){
_start:
{
lean_object* v_res_112_; 
v_res_112_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00manyTrees_spec__0(v_depth_106_, v_range_107_, v_b_108_, v_i_109_, v_hs_110_, v_hl_111_);
lean_dec_ref(v_range_107_);
lean_dec(v_depth_106_);
return v_res_112_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0(lean_object* v_i_113_, lean_object* v___x_114_, lean_object* v_x_115_){
_start:
{
lean_object* v___x_116_; 
v___x_116_ = l_manyTrees(v_i_113_, v___x_114_);
return v___x_116_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0___boxed(lean_object* v_i_117_, lean_object* v___x_118_, lean_object* v_x_119_){
_start:
{
lean_object* v_res_120_; 
v_res_120_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0(v_i_117_, v___x_118_, v_x_119_);
lean_dec(v_i_117_);
return v_res_120_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(lean_object* v___y_121_, lean_object* v_range_122_, lean_object* v_b_123_, lean_object* v_i_124_){
_start:
{
lean_object* v_stop_126_; lean_object* v_step_127_; uint8_t v___x_128_; 
v_stop_126_ = lean_ctor_get(v_range_122_, 1);
v_step_127_ = lean_ctor_get(v_range_122_, 2);
v___x_128_ = lean_nat_dec_lt(v_i_124_, v_stop_126_);
if (v___x_128_ == 0)
{
lean_object* v___x_129_; 
lean_dec(v_i_124_);
v___x_129_ = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(v___x_129_, 0, v_b_123_);
return v___x_129_;
}
else
{
lean_object* v___x_130_; lean_object* v___x_131_; lean_object* v___x_132_; lean_object* v___x_133_; lean_object* v___x_134_; lean_object* v___f_135_; lean_object* v___x_136_; lean_object* v___x_137_; lean_object* v___x_138_; lean_object* v___x_139_; lean_object* v___x_140_; lean_object* v___x_141_; 
v___x_130_ = lean_unsigned_to_nat(4u);
v___x_131_ = lean_unsigned_to_nat(2u);
v___x_132_ = lean_nat_sub(v___y_121_, v_i_124_);
v___x_133_ = lean_nat_add(v___x_132_, v___x_130_);
lean_dec(v___x_132_);
v___x_134_ = lean_nat_pow(v___x_131_, v___x_133_);
lean_dec(v___x_133_);
lean_inc(v___x_134_);
lean_inc_n(v_i_124_, 2);
v___f_135_ = lean_alloc_closure((void*)(l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___lam__0___boxed), 3, 2);
lean_closure_set(v___f_135_, 0, v_i_124_);
lean_closure_set(v___f_135_, 1, v___x_134_);
v___x_136_ = lean_unsigned_to_nat(0u);
v___x_137_ = lean_task_spawn(v___f_135_, v___x_136_);
v___x_138_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_138_, 0, v_i_124_);
lean_ctor_set(v___x_138_, 1, v___x_137_);
v___x_139_ = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(v___x_139_, 0, v___x_134_);
lean_ctor_set(v___x_139_, 1, v___x_138_);
v___x_140_ = lean_array_push(v_b_123_, v___x_139_);
v___x_141_ = lean_nat_add(v_i_124_, v_step_127_);
lean_dec(v_i_124_);
v_b_123_ = v___x_140_;
v_i_124_ = v___x_141_;
goto _start;
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg___boxed(lean_object* v___y_143_, lean_object* v_range_144_, lean_object* v_b_145_, lean_object* v_i_146_, lean_object* v___y_147_){
_start:
{
lean_object* v_res_148_; 
v_res_148_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v___y_143_, v_range_144_, v_b_145_, v_i_146_);
lean_dec_ref(v_range_144_);
lean_dec(v___y_143_);
return v_res_148_;
}
}
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(lean_object* v_s_149_){
_start:
{
lean_object* v___x_151_; lean_object* v_putStr_152_; lean_object* v___x_153_; 
v___x_151_ = lean_get_stdout();
v_putStr_152_ = lean_ctor_get(v___x_151_, 4);
lean_inc_ref(v_putStr_152_);
lean_dec_ref(v___x_151_);
v___x_153_ = lean_apply_2(v_putStr_152_, v_s_149_, lean_box(0));
return v___x_153_;
}
}
LEAN_EXPORT lean_object* l_IO_print___at___00IO_println___at___00main_spec__0_spec__0___boxed(lean_object* v_s_154_, lean_object* v_a_155_){
_start:
{
lean_object* v_res_156_; 
v_res_156_ = l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(v_s_154_);
return v_res_156_;
}
}
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0(lean_object* v_s_157_){
_start:
{
uint32_t v___x_159_; lean_object* v___x_160_; lean_object* v___x_161_; 
v___x_159_ = 10;
v___x_160_ = lean_string_push(v_s_157_, v___x_159_);
v___x_161_ = l_IO_print___at___00IO_println___at___00main_spec__0_spec__0(v___x_160_);
return v___x_161_;
}
}
LEAN_EXPORT lean_object* l_IO_println___at___00main_spec__0___boxed(lean_object* v_s_162_, lean_object* v_a_163_){
_start:
{
lean_object* v_res_164_; 
v_res_164_ = l_IO_println___at___00main_spec__0(v_s_162_);
return v_res_164_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2(lean_object* v_as_167_, size_t v_sz_168_, size_t v_i_169_, lean_object* v_b_170_){
_start:
{
uint8_t v___x_172_; 
v___x_172_ = lean_usize_dec_lt(v_i_169_, v_sz_168_);
if (v___x_172_ == 0)
{
lean_object* v___x_173_; 
v___x_173_ = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(v___x_173_, 0, v_b_170_);
return v___x_173_;
}
else
{
lean_object* v_a_174_; lean_object* v_snd_175_; lean_object* v_fst_176_; lean_object* v_fst_177_; lean_object* v_snd_178_; lean_object* v___x_179_; lean_object* v___x_180_; lean_object* v___x_181_; lean_object* v___x_182_; lean_object* v___x_183_; lean_object* v___x_184_; lean_object* v___x_185_; lean_object* v___x_186_; lean_object* v___x_187_; lean_object* v___x_188_; lean_object* v___x_189_; lean_object* v___x_190_; 
v_a_174_ = lean_array_uget_borrowed(v_as_167_, v_i_169_);
v_snd_175_ = lean_ctor_get(v_a_174_, 1);
v_fst_176_ = lean_ctor_get(v_a_174_, 0);
v_fst_177_ = lean_ctor_get(v_snd_175_, 0);
v_snd_178_ = lean_ctor_get(v_snd_175_, 1);
v___x_179_ = ((lean_object*)(l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__0));
v___x_180_ = lean_box(0);
lean_inc(v_fst_176_);
v___x_181_ = l_Nat_reprFast(v_fst_176_);
v___x_182_ = ((lean_object*)(l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__1));
v___x_183_ = lean_string_append(v___x_181_, v___x_182_);
lean_inc(v_fst_177_);
v___x_184_ = l_Nat_reprFast(v_fst_177_);
v___x_185_ = lean_string_append(v___x_183_, v___x_184_);
lean_dec_ref(v___x_184_);
v___x_186_ = lean_string_append(v___x_185_, v___x_179_);
lean_inc(v_snd_178_);
v___x_187_ = lean_task_get_own(v_snd_178_);
v___x_188_ = l_Nat_reprFast(v___x_187_);
v___x_189_ = lean_string_append(v___x_186_, v___x_188_);
lean_dec_ref(v___x_188_);
v___x_190_ = l_IO_println___at___00main_spec__0(v___x_189_);
if (lean_obj_tag(v___x_190_) == 0)
{
size_t v___x_191_; size_t v___x_192_; 
lean_dec_ref_known(v___x_190_, 1);
v___x_191_ = ((size_t)1ULL);
v___x_192_ = lean_usize_add(v_i_169_, v___x_191_);
v_i_169_ = v___x_192_;
v_b_170_ = v___x_180_;
goto _start;
}
else
{
return v___x_190_;
}
}
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___boxed(lean_object* v_as_194_, lean_object* v_sz_195_, lean_object* v_i_196_, lean_object* v_b_197_, lean_object* v___y_198_){
_start:
{
size_t v_sz_boxed_199_; size_t v_i_boxed_200_; lean_object* v_res_201_; 
v_sz_boxed_199_ = lean_unbox_usize(v_sz_195_);
lean_dec(v_sz_195_);
v_i_boxed_200_ = lean_unbox_usize(v_i_196_);
lean_dec(v_i_196_);
v_res_201_ = l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2(v_as_194_, v_sz_boxed_199_, v_i_boxed_200_, v_b_197_);
lean_dec_ref(v_as_194_);
return v_res_201_;
}
}
LEAN_EXPORT lean_object* _lean_main(lean_object* v_args_207_){
_start:
{
lean_object* v___y_210_; lean_object* v___x_246_; lean_object* v___y_248_; 
v___x_246_ = lean_unsigned_to_nat(6u);
if (lean_obj_tag(v_args_207_) == 0)
{
lean_object* v___x_254_; 
v___x_254_ = ((lean_object*)(l_main___closed__3));
v___y_248_ = v___x_254_;
goto v___jp_247_;
}
else
{
lean_object* v_head_255_; 
v_head_255_ = lean_ctor_get(v_args_207_, 0);
lean_inc(v_head_255_);
lean_dec_ref_known(v_args_207_, 2);
v___y_248_ = v_head_255_;
goto v___jp_247_;
}
v___jp_209_:
{
lean_object* v___x_211_; lean_object* v_stretch_212_; lean_object* v___x_213_; lean_object* v___x_214_; lean_object* v___x_215_; lean_object* v___x_216_; lean_object* v___x_217_; uint64_t v___x_218_; lean_object* v___x_219_; lean_object* v___x_220_; lean_object* v___x_221_; lean_object* v___x_222_; lean_object* v___x_223_; 
v___x_211_ = lean_unsigned_to_nat(1u);
v_stretch_212_ = lean_nat_add(v___y_210_, v___x_211_);
v___x_213_ = ((lean_object*)(l_main___closed__0));
lean_inc(v_stretch_212_);
v___x_214_ = l_Nat_reprFast(v_stretch_212_);
v___x_215_ = lean_string_append(v___x_213_, v___x_214_);
lean_dec_ref(v___x_214_);
v___x_216_ = ((lean_object*)(l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2___closed__0));
v___x_217_ = lean_string_append(v___x_215_, v___x_216_);
v___x_218_ = 1ULL;
v___x_219_ = l_makeTree(v_stretch_212_, v___x_218_);
v___x_220_ = l_checkTree(v___x_219_);
lean_dec(v___x_219_);
v___x_221_ = l_Nat_reprFast(v___x_220_);
v___x_222_ = lean_string_append(v___x_217_, v___x_221_);
lean_dec_ref(v___x_221_);
v___x_223_ = l_IO_println___at___00main_spec__0(v___x_222_);
if (lean_obj_tag(v___x_223_) == 0)
{
lean_object* v___x_224_; lean_object* v___x_225_; lean_object* v___x_226_; lean_object* v___x_227_; lean_object* v___x_228_; lean_object* v___x_229_; lean_object* v_a_230_; lean_object* v___x_231_; size_t v_sz_232_; size_t v___x_233_; lean_object* v___x_234_; 
lean_dec_ref_known(v___x_223_, 1);
v___x_224_ = l_makeTree(v___y_210_, v___x_218_);
v___x_225_ = ((lean_object*)(l_main___closed__1));
v___x_226_ = lean_unsigned_to_nat(4u);
v___x_227_ = lean_unsigned_to_nat(2u);
v___x_228_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_228_, 0, v___x_226_);
lean_ctor_set(v___x_228_, 1, v_stretch_212_);
lean_ctor_set(v___x_228_, 2, v___x_227_);
v___x_229_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v___y_210_, v___x_228_, v___x_225_, v___x_226_);
lean_dec_ref_known(v___x_228_, 3);
v_a_230_ = lean_ctor_get(v___x_229_, 0);
lean_inc(v_a_230_);
lean_dec_ref(v___x_229_);
v___x_231_ = lean_box(0);
v_sz_232_ = lean_array_size(v_a_230_);
v___x_233_ = ((size_t)0ULL);
v___x_234_ = l___private_Init_Data_Array_Basic_0__Array_forIn_x27Unsafe_loop___at___00main_spec__2(v_a_230_, v_sz_232_, v___x_233_, v___x_231_);
lean_dec(v_a_230_);
if (lean_obj_tag(v___x_234_) == 0)
{
lean_object* v___x_235_; lean_object* v___x_236_; lean_object* v___x_237_; lean_object* v___x_238_; lean_object* v___x_239_; lean_object* v___x_240_; lean_object* v___x_241_; lean_object* v___x_242_; 
lean_dec_ref_known(v___x_234_, 1);
v___x_235_ = ((lean_object*)(l_main___closed__2));
v___x_236_ = l_Nat_reprFast(v___y_210_);
v___x_237_ = lean_string_append(v___x_235_, v___x_236_);
lean_dec_ref(v___x_236_);
v___x_238_ = lean_string_append(v___x_237_, v___x_216_);
v___x_239_ = l_checkTree(v___x_224_);
lean_dec(v___x_224_);
v___x_240_ = l_Nat_reprFast(v___x_239_);
v___x_241_ = lean_string_append(v___x_238_, v___x_240_);
lean_dec_ref(v___x_240_);
v___x_242_ = l_IO_println___at___00main_spec__0(v___x_241_);
if (lean_obj_tag(v___x_242_) == 0)
{
lean_object* v___x_243_; lean_object* v_flush_244_; lean_object* v___x_245_; 
lean_dec_ref_known(v___x_242_, 1);
v___x_243_ = lean_get_stdout();
v_flush_244_ = lean_ctor_get(v___x_243_, 0);
lean_inc_ref(v_flush_244_);
lean_dec_ref(v___x_243_);
v___x_245_ = lean_apply_1(v_flush_244_, lean_box(0));
return v___x_245_;
}
else
{
return v___x_242_;
}
}
else
{
lean_dec(v___x_224_);
lean_dec(v___y_210_);
return v___x_234_;
}
}
else
{
lean_dec(v_stretch_212_);
lean_dec(v___y_210_);
return v___x_223_;
}
}
v___jp_247_:
{
lean_object* v___x_249_; lean_object* v___x_250_; lean_object* v___x_251_; lean_object* v___x_252_; uint8_t v___x_253_; 
v___x_249_ = lean_unsigned_to_nat(0u);
v___x_250_ = lean_string_utf8_byte_size(v___y_248_);
v___x_251_ = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(v___x_251_, 0, v___y_248_);
lean_ctor_set(v___x_251_, 1, v___x_249_);
lean_ctor_set(v___x_251_, 2, v___x_250_);
v___x_252_ = l_String_Slice_toNat_x21(v___x_251_);
lean_dec_ref_known(v___x_251_, 3);
v___x_253_ = lean_nat_dec_le(v___x_246_, v___x_252_);
if (v___x_253_ == 0)
{
lean_dec(v___x_252_);
v___y_210_ = v___x_246_;
goto v___jp_209_;
}
else
{
v___y_210_ = v___x_252_;
goto v___jp_209_;
}
}
}
}
LEAN_EXPORT lean_object* l_main___boxed(lean_object* v_args_256_, lean_object* v_a_257_){
_start:
{
lean_object* v_res_258_; 
v_res_258_ = _lean_main(v_args_256_);
return v_res_258_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(lean_object* v___y_259_, lean_object* v_range_260_, lean_object* v_b_261_, lean_object* v_i_262_, lean_object* v_hs_263_, lean_object* v_hl_264_){
_start:
{
lean_object* v___x_266_; 
v___x_266_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___redArg(v___y_259_, v_range_260_, v_b_261_, v_i_262_);
return v___x_266_;
}
}
LEAN_EXPORT lean_object* l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1___boxed(lean_object* v___y_267_, lean_object* v_range_268_, lean_object* v_b_269_, lean_object* v_i_270_, lean_object* v_hs_271_, lean_object* v_hl_272_, lean_object* v___y_273_){
_start:
{
lean_object* v_res_274_; 
v_res_274_ = l___private_Init_Data_Range_Basic_0__Std_Legacy_Range_forIn_x27_loop___at___00main_spec__1(v___y_267_, v_range_268_, v_b_269_, v_i_270_, v_hs_271_, v_hl_272_);
lean_dec_ref(v_range_268_);
lean_dec(v___y_267_);
return v_res_274_;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Std(uint8_t builtin);
void lean_initialize_runtime_module();
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_binarytrees(uint8_t builtin) {
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
l_instInhabitedTree_default = _init_l_instInhabitedTree_default();
lean_mark_persistent(l_instInhabitedTree_default);
l_instInhabitedTree = _init_l_instInhabitedTree();
lean_mark_persistent(l_instInhabitedTree);
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
  res = initialize_binarytrees(1 /* builtin */);
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
