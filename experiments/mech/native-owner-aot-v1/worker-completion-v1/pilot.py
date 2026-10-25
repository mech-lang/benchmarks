"""Read only this thread's counters; no counter configuration or priority change."""
import ctypes
import json
import time

lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
class Raw(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ('instructions','cycles','user_mach','system_mach')]
class Timebase(ctypes.Structure):
    _fields_ = [('numer',ctypes.c_uint32),('denom',ctypes.c_uint32)]
lib.thread_selfcounts.argtypes=[ctypes.c_uint32,ctypes.c_void_p,ctypes.c_size_t]
lib.thread_selfcounts.restype=ctypes.c_int
lib.clock_gettime_nsec_np.argtypes=[ctypes.c_int]
lib.clock_gettime_nsec_np.restype=ctypes.c_uint64
lib.mach_timebase_info.argtypes=[ctypes.POINTER(Timebase)]
lib.mach_timebase_info.restype=ctypes.c_int
lib.sysctlbyname.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p,ctypes.c_size_t]
lib.sysctlbyname.restype=ctypes.c_int

def sysctl(name, cls):
    value=cls(); size=ctypes.c_size_t(ctypes.sizeof(value))
    assert lib.sysctlbyname(name.encode(),ctypes.byref(value),ctypes.byref(size),None,0)==0,(name,ctypes.get_errno())
    assert size.value==ctypes.sizeof(value)
    return value.value

def string(name):
    value=ctypes.create_string_buffer(128); size=ctypes.c_size_t(len(value))
    assert lib.sysctlbyname(name.encode(),value,ctypes.byref(size),None,0)==0,(name,ctypes.get_errno())
    return value.value.decode()

levels=sysctl('hw.nperflevels',ctypes.c_int)
assert 1<=levels<=8
names=[string(f'hw.perflevel{i}.name') for i in range(levels)]
tb=Timebase(); assert lib.mach_timebase_info(ctypes.byref(tb))==0 and tb.numer and tb.denom

def fields(raw): return {name:getattr(raw,name) for name,_ in Raw._fields_}
def stamp():
    wall=time.monotonic_ns(); flat=Raw(); split=(Raw*levels)()
    assert lib.thread_selfcounts(3,ctypes.byref(flat),ctypes.sizeof(flat))==0,ctypes.get_errno()
    assert lib.thread_selfcounts(4,split,ctypes.sizeof(split))==0,ctypes.get_errno()
    cpu=lib.clock_gettime_nsec_np(16)
    total_ns=(sum(v.user_mach+v.system_mach for v in split)*tb.numer)//tb.denom
    assert abs(total_ns-cpu)<2_000_000,(total_ns,cpu)
    return dict(wall_ns=wall,cpu_ns=cpu,total=fields(flat),levels=list(map(fields,split)))

rows=[stamp()]
acc=1
for batch in range(3):
    for i in range(200000): acc=(acc*1664525+1013904223+i)&0xffffffff
    rows.append(stamp())
for a,b in zip(rows,rows[1:]):
    assert b['cpu_ns']>a['cpu_ns'] and b['wall_ns']>a['wall_ns']
    assert b['total']['instructions']>a['total']['instructions'] and b['total']['cycles']>a['total']['cycles']
    assert b['cpu_ns']-a['cpu_ns']<=b['wall_ns']-a['wall_ns']+2_000_000
print(json.dumps(dict(status='self-counters-available-and-monotone',levels=levels,level_names=names,timebase=dict(numer=tb.numer,denom=tb.denom),snapshots=rows,checksum=acc,settings_changed=False)))
