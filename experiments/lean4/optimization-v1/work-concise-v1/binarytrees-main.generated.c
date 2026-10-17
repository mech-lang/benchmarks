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
