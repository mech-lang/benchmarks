/* Diagnostic-only arithmetic call counter. Never inserted into timed subjects. */
#include <gmp.h>
#include <dlfcn.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

static uint64_t divisions, floor_divisions, multiplications, additions;
static int trace_enabled;
static void (*real_divide)(mpz_ptr,mpz_srcptr,mpz_srcptr);
static void (*real_floor)(mpz_ptr,mpz_srcptr,mpz_srcptr);
static void (*real_multiply)(mpz_ptr,mpz_srcptr,unsigned long);
static void (*real_add)(mpz_ptr,mpz_srcptr,mpz_srcptr);
__attribute__((constructor)) static void initialize(void) {
    real_divide=dlsym(RTLD_NEXT,"__gmpz_tdiv_q");
    real_floor=dlsym(RTLD_NEXT,"__gmpz_fdiv_q");
    real_multiply=dlsym(RTLD_NEXT,"__gmpz_mul_ui");
    real_add=dlsym(RTLD_NEXT,"__gmpz_add");
    if(!real_divide || !real_floor || !real_multiply || !real_add) abort();
    const char *s=getenv("MECH_GMP_TRACE_QUOTIENTS"); trace_enabled=s && s[0]=='1';
}
static void quotient(mpz_srcptr n,mpz_srcptr d,mpz_srcptr q) {
    if(!trace_enabled) return;
    size_t ns=mpz_sizeinbase(n,10)+3,ds=mpz_sizeinbase(d,10)+3,qs=mpz_sizeinbase(q,10)+3;
    char *a=malloc(ns),*b=malloc(ds),*c=malloc(qs);
    if(!a || !b || !c) abort();
    mpz_get_str(a,10,n);mpz_get_str(b,10,d);mpz_get_str(c,10,q);
    fprintf(stderr,"Q %s %s %s\n",a,b,c);free(a);free(b);free(c);
}
static void counted_divide(mpz_ptr q,mpz_srcptr n,mpz_srcptr d) {
    ++divisions;real_divide(q,n,d);quotient(n,d,q);
}
static void counted_floor(mpz_ptr q,mpz_srcptr n,mpz_srcptr d) {
    ++floor_divisions;real_floor(q,n,d);quotient(n,d,q);
}
static void counted_multiply(mpz_ptr out,mpz_srcptr in,unsigned long factor) {
    ++multiplications;real_multiply(out,in,factor);
}
static void counted_add(mpz_ptr out,mpz_srcptr a,mpz_srcptr b) {
    ++additions;real_add(out,a,b);
}
__attribute__((destructor)) static void finish(void) {
    fprintf(stderr,"WORK tdiv=%"PRIu64" fdiv=%"PRIu64" mul_ui=%"PRIu64" add=%"PRIu64"\n",divisions,floor_divisions,multiplications,additions);
}
__attribute__((used,section("__DATA,__interpose")))
static const struct {const void *replacement; const void *original;} replacements[]={
    {(const void*)counted_divide,(const void*)__gmpz_tdiv_q},
    {(const void*)counted_floor,(const void*)__gmpz_fdiv_q},
    {(const void*)counted_multiply,(const void*)__gmpz_mul_ui},
    {(const void*)counted_add,(const void*)__gmpz_add}
};
