"""Reconstruct every admitted lookup from actual compiler-emitted readonly data."""
from pathlib import Path
import struct

def data(path,size):
 image=Path(path).read_bytes();assert struct.unpack_from('<I',image)[0]==0xfeedfacf
 sections=[];symbols=None;at=32
 for _ in range(struct.unpack_from('<I',image,16)[0]):
  kind,length=struct.unpack_from('<II',image,at)
  if kind==0x19:
   for index in range(struct.unpack_from('<I',image,at+64)[0]):
    p=at+72+index*80;name,segment=struct.unpack_from('<16s16s',image,p);address,extent,offset=struct.unpack_from('<QQI',image,p+32)
    sections.append((name.rstrip(b'\0'),segment.rstrip(b'\0'),address,extent,offset))
  elif kind==2:symbols=struct.unpack_from('<IIII',image,at+8)
  at+=length
 assert symbols is not None
 symoff,count,stroff,strsize=symbols;found=[]
 for index in range(count):
  key,kind,section,_,value=struct.unpack_from('<IBBHQ',image,symoff+16*index);assert key<strsize
  end=image.index(b'\0',stroff+key,stroff+strsize)
  if image[stroff+key:end]==b'_mech_compact_cost_codes_0':
   name,segment,address,extent,offset=sections[section-1];assert kind==0xe and (name,segment)==(b'__const',b'__TEXT')
   begin=value-address;assert value%16==0 and 0<=begin<=extent-size
   found.append(image[offset+begin:offset+begin+size])
 result,=found;assert len(result)==size;return result

def verify(original,path,shift,physical_size):
 expected=data(original,65536);actual=data(path,physical_size)
 if shift is None:
  assert actual==expected;return {'values':65536,'storage_bytes':physical_size,'paged':False}
 page_size=1<<shift;directory_bytes=len(expected)//page_size
 assert physical_size>directory_bytes and (physical_size-directory_bytes)%page_size==0
 page_count=(physical_size-directory_bytes)//page_size;assert 0<page_count<=256
 assert all(page<page_count for page in actual[:directory_bytes])
 decoded=bytes(actual[directory_bytes+(actual[word>>shift]<<shift)+(word&(page_size-1))] for word in range(len(expected)))
 assert decoded==expected
 return {'values':65536,'storage_bytes':physical_size,'paged':True,'shift':shift,'directory_bytes':directory_bytes,'unique_pages':page_count,'source_index_and_cost_admission_changed':False}
