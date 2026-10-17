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
v___x_48_ = lean_alloc_ctor(1, 2, 8);
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
v___x_56_ = lean_alloc_ctor(1, 2, 8);
lean_ctor_set(v___x_56_, 0, v___x_53_);
lean_ctor_set(v___x_56_, 1, v___x_55_);
lean_ctor_set_uint64(v___x_56_, sizeof(void*)*2, v_x_44_);
return v___x_56_;
}
}
}
