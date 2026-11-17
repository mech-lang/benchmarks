/* Independent byte-string oracle: direct overlapping substring comparisons. */
#include <assert.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef struct {char key[3];uint64_t count;} Count;
static int order(const void *a,const void *b) {
 const Count *x=a,*y=b;
 return x->count==y->count ? strcmp(x->key,y->key) : x->count>y->count?-1:1;
}
int main(void) {
 char *line=NULL;size_t capacity=0,n=0,allocated=0;unsigned char *dna=NULL;int selected=0;ssize_t bytes;
 size_t consumed=0;
 while((bytes=getline(&line,&capacity,stdin))>=0) {
  consumed+=(size_t)bytes;
  if(line[0]=='>'){selected=!strncmp(line,">THREE",6);continue;}
  if(!selected)continue;
  for(ssize_t j=0;j<bytes;j++)if(!isspace((unsigned char)line[j])) {
   unsigned char c=toupper((unsigned char)line[j]);assert(strchr("ACGT",c));
   if(n==allocated){allocated=allocated?allocated*2:65536;dna=realloc(dna,allocated);assert(dna);}dna[n++]=c;
  }
 }
 assert(feof(stdin));free(line);assert(n>=2);
 uint64_t one[256]={0},two[65536]={0};
 for(size_t i=0;i<n;i++){one[dna[i]]++;if(i+1<n)two[dna[i]*256+dna[i+1]]++;}
 for(int width=1;width<=2;width++) {
  Count counts[16];size_t k=0;
  for(size_t a=0;a<4;a++)for(size_t b=0;b<(width==2?4:1);b++) {
   char x="ACGT"[a],y="ACGT"[b];counts[k]=(Count){{x,width==2?y:0,0},width==2?two[(unsigned char)x*256+(unsigned char)y]:one[(unsigned char)x]};k++;
  }
  qsort(counts,k,sizeof(Count),order);
  for(size_t i=0;i<k;i++)if(counts[i].count)printf("%s %.3f\n",counts[i].key,100.0*counts[i].count/(n-width+1));
  putchar('\n');
 }
 const char *queries[]={"GGT","GGTA","GGTATT","GGTATTTTAATT","GGTATTTTAATTTATAGT"};
 for(size_t q=0;q<5;q++){size_t width=strlen(queries[q]);uint64_t count=0;for(size_t i=0;i+width<=n;i++)if(dna[i]=='G'&&!memcmp(dna+i,queries[q],width))count++;printf("%llu\t%s\n",(unsigned long long)count,queries[q]);}
 fprintf(stderr,"{\"input_bytes\":%zu,\"selected_bases\":%zu,\"complete_input_consumption\":true}\n",consumed,n);
 free(dna);return 0;
}
