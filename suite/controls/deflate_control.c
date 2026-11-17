/* Complete-call controls for pinned Roc/libdeflate. Raw bytes go to stdout.
   Lists follow the pinned Roc compiler's list ABI, checked against its source. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef ROC_CONTROL
typedef struct { unsigned char *elements; size_t length, capacity; } RocList;
extern RocList roc_compress(RocList input, RocList output);
void *roc_alloc(size_t bytes, size_t alignment) { assert(alignment<=16); void *p=malloc(bytes?bytes:1);assert(p);return p; }
void roc_dealloc(void *p, size_t alignment) { (void)alignment;free(p); }
void *roc_realloc(void *p,size_t bytes,size_t alignment) {assert(alignment<=16);p=realloc(p,bytes?bytes:1);assert(p);return p;}
void roc_dbg(const unsigned char *p,size_t n) {fwrite(p,1,n,stderr);}
void roc_crashed(const unsigned char *p,size_t n) {roc_dbg(p,n);abort();}
void roc_expect_failed(const unsigned char *p,size_t n) {roc_crashed(p,n);}
static RocList list(const unsigned char *bytes,size_t n,size_t capacity) {
    assert(capacity>=n);if (!capacity) return (RocList){0};
    size_t *p=roc_alloc(capacity+8,8);*p=1;unsigned char *data=(unsigned char *)(p+1);memcpy(data,bytes,n);
    return (RocList){data,n,capacity*2};
}
static size_t *reference(RocList a) {assert(!(a.capacity&1));return (size_t *)a.elements-1;}
static RocList retained(RocList a) {if(a.elements)++*reference(a);return a;}
static void release(RocList a) {if(a.elements && --*reference(a)==0)free(reference(a));}
#else
#include "libdeflate.h"
#endif
static unsigned char *read_file(const char *path,size_t *n) {
    FILE *f=fopen(path,"rb");assert(f);assert(!fseek(f,0,SEEK_END));long size=ftell(f);assert(size>=0);rewind(f);
    *n=(size_t)size;unsigned char *p=malloc(*n?*n:1);assert(p);assert(fread(p,1,*n,f)==*n);assert(!fclose(f));return p;
}
static double now(void) {struct timespec t;assert(!clock_gettime(CLOCK_MONOTONIC,&t));return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv) {
    assert(argc==4);size_t n,pn;unsigned char *input=read_file(argv[1],&n),*prefix=read_file(argv[2],&pn);
    char *end;size_t capacity=strtoull(argv[3],&end,10);assert(!*end && capacity>=pn);
    double started,seconds;unsigned char *result;size_t length;
#ifdef ROC_CONTROL
    RocList source=list(input,n,n),prepared=list(prefix,pn,capacity);
    RocList a=retained(source),b=retained(prepared);
    started=now();RocList returned=roc_compress(a,b);seconds=now()-started;
    assert(source.length==n && (!n || !memcmp(source.elements,input,n)));
    assert(prepared.length==pn && (!pn || !memcmp(prepared.elements,prefix,pn)));
    assert(!source.elements || *reference(source)==1);assert(*reference(prepared)==1 && *reference(returned)==1);
    assert(returned.elements!=prepared.elements && returned.capacity/2==capacity);
    result=returned.elements;length=returned.length;
#else
    unsigned char *prepared=malloc(capacity);assert(prepared);memcpy(prepared,prefix,pn);
    started=now();struct libdeflate_compressor *compressor=libdeflate_alloc_compressor(12);assert(compressor);
    result=malloc(capacity);assert(result);memcpy(result,prefix,pn);
    size_t compressed=libdeflate_deflate_compress(compressor,input,n,result+pn,capacity-pn);assert(compressed);
    libdeflate_free_compressor(compressor);seconds=now()-started;length=pn+compressed;
    assert(result!=prepared && !memcmp(prepared,prefix,pn));free(prepared);
#endif
    assert(length>=pn && (!pn || !memcmp(result,prefix,pn)));
    assert(fwrite(result,1,length,stdout)==length);assert(!fflush(stdout));
    fprintf(stderr,"{\"control_call_seconds\":%.12g,\"input_bytes\":%zu,\"output_bytes\":%zu,\"aliases_preserved\":true,\"level\":12}\n",seconds,n,length);
#ifdef ROC_CONTROL
    release(returned);release(prepared);release(source);
#else
    free(result);
#endif
    free(input);free(prefix);return 0;
}
