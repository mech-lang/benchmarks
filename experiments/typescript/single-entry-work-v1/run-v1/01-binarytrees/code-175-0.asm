[marking 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> for optimization to MAGLEV, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> (target MAGLEV), mode: ConcurrencyMode::kSynchronous]
0x1ae954e418a9: [Code]
 - map: 0x1d42df7817e9 <Map[88](CODE_TYPE)>
 - kind: MAGLEV
 - deoptimization_data_or_interpreter_data: 0x1ae954e41739 <ProtectedFixedArray[18]>
 - position_table: 0x1bc26a780011 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - parameter_count: 2
 - instruction_stream: 0x0001266c18c1 <InstructionStream MAGLEV>
 - instruction_start: 0x1266c18e0
 - is_turbofanned: 0
 - stack_slots: 6
 - marked_for_deoptimization: 0
 - embedded_objects_cleared: 0
 - can_have_weak_objects: 0
 - instruction_size: 272
 - metadata_size: 32
 - inlined_bytecode_size: 0
 - osr_offset: -1
 - handler_table_offset: 32
 - unwinding_info_offset: 32
 - code_comments_offset: 32
 - instruction_stream.relocation_info: 0x1ae954e41861 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - instruction_stream.body_size: 304

--- Disassembly: ---
kind = MAGLEV
name = isPosixPathSeparator
compiler = maglev
address = 0x1ae954e418a9

Instructions (size = 272)
0x1266c18e0     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c18e4     4  910003fd       mov fp, sp
0x1266c18e8     8  a9bf6fe1       stp x1, cp, [sp, #-16]!
0x1266c18ec     c  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c18f0    10  d106c3f0       sub x16, sp, #0x1b0 (432)
0x1266c18f4    14  f8520351       ldur x17, [x26, #-224]
0x1266c18f8    18  eb11021f       cmp x16, x17
0x1266c18fc    1c  54000343       b.lo #+0x68 (addr 0x1266c1964)
0x1266c1900    20  f9400fa0       ldr x0, [fp, #24]
0x1266c1904    24  37000720       tbnz w0, #0, #+0xe4 (addr 0x1266c19e8)
0x1266c1908    28  d360fc00       lsr x0, x0, #32
0x1266c190c    2c  7100bc1f       cmp w0, #0x2f (47)
0x1266c1910    30  54000060       b.eq #+0xc (addr 0x1266c191c)
0x1266c1914    34  f940e341       ldr x1, [x26, #448]
0x1266c1918    38  14000002       b #+0x8 (addr 0x1266c1920)
0x1266c191c    3c  f940df41       ldr x1, [x26, #440]
0x1266c1920    40  580004c0       ldr x0, pc+152 (addr 0x00000001266c19b8)    ;; object: 0x273efcb865b1 <FeedbackCell[one closure]>
0x1266c1924    44  b8413002       ldur w2, [x0, #19]
0x1266c1928    48  71001c42       subs w2, w2, #0x7 (7)
0x1266c192c    4c  b8013002       stur w2, [x0, #19]
0x1266c1930    50  5400024b       b.lt #+0x48 (addr 0x1266c1978)
0x1266c1934    54  aa0103e0       mov x0, x1
0x1266c1938    58  f85e83a9       ldur x9, [fp, #-24]
0x1266c193c    5c  d280004a       movz x10, #0x2
0x1266c1940    60  eb09015f       cmp x10, x9
0x1266c1944    64  5400004a       b.ge #+0x8 (addr 0x1266c194c)
0x1266c1948    68  aa0903ea       mov x10, x9
0x1266c194c    6c  910003bf       mov sp, fp
0x1266c1950    70  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c1954    74  91000550       add x16, x10, #0x1 (1)
0x1266c1958    78  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c195c    7c  8b306fff       add sp, sp, x16, lsl #3
0x1266c1960    80  d65f03c0       ret
0x1266c1964    84  d2c03600       movz x0, #0x1b000000000
0x1266c1968    88  58000310       ldr x16, pc+96 (addr 0x00000001266c19c8)
0x1266c196c    8c  d63f0200       blr x16
0x1266c1970    90  17ffffe4       b #-0x70 (addr 0x1266c1900)
0x1266c1974    94  d4200000       brk #0x0
0x1266c1978    98  a9bf07ff       stp xzr, x1, [sp, #-16]!
0x1266c197c    9c  f85f03a2       ldur x2, [fp, #-16]
0x1266c1980    a0  a9bf7fe2       stp x2, xzr, [sp, #-16]!
0x1266c1984    a4  580001fb       ldr cp, pc+60 (addr 0x00000001266c19c0)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c1988    a8  d2800020       movz x0, #0x1
0x1266c198c    ac  d29d9b01       movz x1, #0xecd8
0x1266c1990    b0  f2a06081       movk x1, #0x304, lsl #16
0x1266c1994    b4  f2c00021       movk x1, #0x1, lsl #32
0x1266c1998    b8  580001d0       ldr x16, pc+56 (addr 0x00000001266c19d0)
0x1266c199c    bc  d63f0200       blr x16
0x1266c19a0    c0  a8c107ff       ldp xzr, x1, [sp], #16
0x1266c19a4    c4  17ffffe4       b #-0x70 (addr 0x1266c1934)
0x1266c19a8    c8  d4200000       brk #0x0
0x1266c19ac    cc  5800015f       constant pool begin (num_const = 10)    ;; constant pool
0x1266c19b0    d0  d63f03e0       constant
0x1266c19b4    d4  d503201f       constant
0x1266c19b8    d8  fcb865b1       constant
0x1266c19bc    dc  0000273e       constant
0x1266c19c0    e0  24400109       constant
0x1266c19c4    e4  00002347       constant
0x1266c19c8    e8  03609ba0       constant
0x1266c19cc    ec  00000001       constant
0x1266c19d0    f0  036a61e0       constant
0x1266c19d4    f4  00000001       constant
0x1266c19d8    f8  f8558350       ldur x16, [x26, #-168]
0x1266c19dc    fc  d61f0200       br x16
0x1266c19e0   100  f8560350       ldur x16, [x26, #-160]
0x1266c19e4   104  d61f0200       br x16
0x1266c19e8   108  97fffffc       bl #-0x10 (addr 0x1266c19d8)    ;; debug: deopt position, script offset '87d'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x1266c19ec   10c  97fffffd       bl #-0xc (addr 0x1266c19e0)    ;; debug: deopt position, script offset '866'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 1

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 2)
 index  bytecode-offset    pc
     0                4   108 
     1               -1   10c 

Safepoints (stack slots = 6, entries = 2, byte size = 30, tagged slots = 0)
0x1266c1970     90  num extra spill slots: 0  deopt      1 trampoline:    10c
0x1266c19a0     c0  num extra spill slots: 2  registers: 1

RelocInfo (size = 54)
0x1266c1920  full embedded object  (0x273efcb865b1 <FeedbackCell[one closure]>)
0x1266c1984  full embedded object  (0x234724400109 <NativeContext[302]>)
0x1266c19ac  constant pool (size 44)
0x1266c19e8  deopt script offset  (2173)
0x1266c19e8  deopt inlining id  (-1)
0x1266c19e8  deopt reason  (not a Smi)
0x1266c19e8  deopt index
0x1266c19ec  deopt script offset  (2150)
0x1266c19ec  deopt inlining id  (-1)
0x1266c19ec  deopt reason  ((unknown))
0x1266c19ec  deopt index

[completed compiling 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> (target MAGLEV) - took 0.000, 0.250, 0.291 ms]
[marking 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> for optimization to TURBOFAN_JS, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> (target TURBOFAN_JS), mode: ConcurrencyMode::kConcurrent]
--- Raw source ---
(code) {
  return code === CHAR_FORWARD_SLASH;
}


--- Optimized code ---
optimization_id = 1
source_position = 2150
kind = TURBOFAN_JS
name = isPosixPathSeparator
compiler = turbofan
address = 0x1ae954e41b41

Instructions (size = 208)
0x1266c1a40     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c1a44     4  910003fd       mov fp, sp
0x1266c1a48     8  a9be03ff       stp xzr, x0, [sp, #-32]!
0x1266c1a4c     c  a9016fe1       stp x1, cp, [sp, #16]
0x1266c1a50    10  f8520342       ldur x2, [x26, #-224]
0x1266c1a54    14  f90003fb       str cp, [sp]
0x1266c1a58    18  eb2263ff       cmp sp, x2
0x1266c1a5c    1c  54000289       b.ls #+0x50 (addr 0x1266c1aac)
0x1266c1a60    20  f9401fe2       ldr x2, [sp, #56]
0x1266c1a64    24  f240005f       tst x2, #0x1
0x1266c1a68    28  54000501       b.ne #+0xa0 (addr 0x1266c1b08)
0x1266c1a6c    2c  d2c005e3       movz x3, #0x2f00000000
0x1266c1a70    30  eb03005f       cmp x2, x3
0x1266c1a74    34  54000180       b.eq #+0x30 (addr 0x1266c1aa4)
0x1266c1a78    38  f940e340       ldr x0, [x26, #448]
0x1266c1a7c    3c  f85e83a3       ldur x3, [fp, #-24]
0x1266c1a80    40  910003bf       mov sp, fp
0x1266c1a84    44  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c1a88    48  f100087f       cmp x3, #0x2 (2)
0x1266c1a8c    4c  5400004a       b.ge #+0x8 (addr 0x1266c1a94)
0x1266c1a90    50  d2800043       movz x3, #0x2
0x1266c1a94    54  91000470       add x16, x3, #0x1 (1)
0x1266c1a98    58  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c1a9c    5c  8b306fff       add sp, sp, x16, lsl #3
0x1266c1aa0    60  d65f03c0       ret
0x1266c1aa4    64  f940df40       ldr x0, [x26, #440]
0x1266c1aa8    68  17fffff5       b #-0x2c (addr 0x1266c1a7c)
0x1266c1aac    6c  d2c00402       movz x2, #0x2000000000
0x1266c1ab0    70  d10043ff       sub sp, sp, #0x10 (16)
0x1266c1ab4    74  f90007ff       str xzr, [sp, #8]
0x1266c1ab8    78  f90003e2       str x2, [sp]
0x1266c1abc    7c  d29d4f01       movz x1, #0xea78
0x1266c1ac0    80  f2a06081       movk x1, #0x304, lsl #16
0x1266c1ac4    84  f2c00021       movk x1, #0x1, lsl #32
0x1266c1ac8    88  d2800020       movz x0, #0x1
0x1266c1acc    8c  580000fb       ldr cp, pc+28 (addr 0x00000001266c1ae8)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c1ad0    90  58000110       ldr x16, pc+32 (addr 0x00000001266c1af0)
0x1266c1ad4    94  d63f0200       blr x16
0x1266c1ad8    98  17ffffe2       b #-0x78 (addr 0x1266c1a60)
0x1266c1adc    9c  d503201f       nop
0x1266c1ae0    a0  580000bf       constant pool begin (num_const = 5)    ;; constant pool
0x1266c1ae4    a4  d63f03e0       constant
0x1266c1ae8    a8  24400109       constant
0x1266c1aec    ac  00002347       constant
0x1266c1af0    b0  036a61e0       constant
0x1266c1af4    b4  00000001       constant
0x1266c1af8    b8  f8558350       ldur x16, [x26, #-168]
0x1266c1afc    bc  d61f0200       br x16
0x1266c1b00    c0  f8560350       ldur x16, [x26, #-160]
0x1266c1b04    c4  d61f0200       br x16
0x1266c1b08    c8  97fffffc       bl #-0x10 (addr 0x1266c1af8)    ;; debug: deopt position, script offset '87d'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x1266c1b0c    cc  97fffffd       bl #-0xc (addr 0x1266c1b00)    ;; debug: deopt position, script offset '866'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 1

Source positions:
 pc offset  position
        10      2150
        20      2173
        2c      2196
        6c      2150

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 2)
 index  bytecode-offset    pc
     0                4    NA 
     1               -1    98 

Safepoints (stack slots = 6, entries = 1, byte size = 16)
0x1266c1ad8     98  slots (sp->fp): 100000  deopt      1 trampoline:     cc

RelocInfo (size = 33)
0x1266c1acc  full embedded object  (0x234724400109 <NativeContext[12e]>)
0x1266c1ae0  constant pool (size 18)
0x1266c1b08  deopt script offset  (87d)
0x1266c1b08  deopt inlining id  (ffffffffffffffff)
0x1266c1b08  deopt reason  (not a Smi)
0x1266c1b08  deopt index
0x1266c1b0c  deopt script offset  (866)
0x1266c1b0c  deopt inlining id  (ffffffffffffffff)
0x1266c1b0c  deopt reason  ((unknown))
0x1266c1b0c  deopt index

--- End code ---
[completed compiling 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> (target TURBOFAN_JS) - took 0.042, 0.458, 0.167 ms]
[completed optimizing 0x273efcb86571 <JSFunction isPosixPathSeparator (sfi = 0x7e6c6e12c71)> (target TURBOFAN_JS)]
[marking 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> for optimization to MAGLEV, ConcurrencyMode::kConcurrent, reason: hot and stable]
[marking 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> for optimization to MAGLEV, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> (target MAGLEV), mode: ConcurrencyMode::kSynchronous]
0x1ae954e423e1: [Code]
 - map: 0x1d42df7817e9 <Map[88](CODE_TYPE)>
 - kind: MAGLEV
 - deoptimization_data_or_interpreter_data: 0x1ae954e421f1 <ProtectedFixedArray[24]>
 - position_table: 0x1bc26a780011 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - parameter_count: 3
 - instruction_stream: 0x0001266c1b21 <InstructionStream MAGLEV>
 - instruction_start: 0x1266c1b40
 - is_turbofanned: 0
 - stack_slots: 6
 - marked_for_deoptimization: 0
 - embedded_objects_cleared: 0
 - can_have_weak_objects: 0
 - instruction_size: 520
 - metadata_size: 28
 - inlined_bytecode_size: 0
 - osr_offset: -1
 - handler_table_offset: 28
 - unwinding_info_offset: 28
 - code_comments_offset: 28
 - instruction_stream.relocation_info: 0x1ae954e42369 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - instruction_stream.body_size: 548

--- Disassembly: ---
kind = MAGLEV
name = TreeNode
compiler = maglev
address = 0x1ae954e423e1

Instructions (size = 520)
0x1266c1b40     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c1b44     4  910003fd       mov fp, sp
0x1266c1b48     8  a9bf6fe1       stp x1, cp, [sp, #-16]!
0x1266c1b4c     c  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c1b50    10  d106c3f0       sub x16, sp, #0x1b0 (432)
0x1266c1b54    14  f8520351       ldur x17, [x26, #-224]
0x1266c1b58    18  eb11021f       cmp x16, x17
0x1266c1b5c    1c  54000603       b.lo #+0xc0 (addr 0x1266c1c1c)
0x1266c1b60    20  f9400ba1       ldr x1, [fp, #16]
0x1266c1b64    24  36000ea1       tbz w1, #0, #+0x1d4 (addr 0x1266c1d38)
0x1266c1b68    28  f85ff030       ldur x16, [x1, #-1]
0x1266c1b6c    2c  58000bf1       ldr x17, pc+380 (addr 0x00000001266c1ce8)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1266c1b70    30  eb11021f       cmp x16, x17
0x1266c1b74    34  54000e21       b.ne #+0x1c4 (addr 0x1266c1d38)
0x1266c1b78    38  f9400fa0       ldr x0, [fp, #24]
0x1266c1b7c    3c  36000e00       tbz w0, #0, #+0x1c0 (addr 0x1266c1d3c)
0x1266c1b80    40  f8017020       stur x0, [x1, #23]
0x1266c1b84    44  36000080       tbz w0, #0, #+0x10 (addr 0x1266c1b94)
0x1266c1b88    48  926eb431       and x17, x1, #0xfffffffffffc0000
0x1266c1b8c    4c  f9400231       ldr x17, [x17]
0x1266c1b90    50  37100511       tbnz w17, #2, #+0xa0 (addr 0x1266c1c30)
0x1266c1b94    54  58000ae2       ldr x2, pc+348 (addr 0x00000001266c1cf0)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1266c1b98    58  f81ff022       stur x2, [x1, #-1]
0x1266c1b9c    5c  926eb431       and x17, x1, #0xfffffffffffc0000
0x1266c1ba0    60  f9400231       ldr x17, [x17]
0x1266c1ba4    64  37100571       tbnz w17, #2, #+0xac (addr 0x1266c1c50)
0x1266c1ba8    68  f94013a2       ldr x2, [fp, #32]
0x1266c1bac    6c  36000ca2       tbz w2, #0, #+0x194 (addr 0x1266c1d40)
0x1266c1bb0    70  f801f022       stur x2, [x1, #31]
0x1266c1bb4    74  36000082       tbz w2, #0, #+0x10 (addr 0x1266c1bc4)
0x1266c1bb8    78  926eb431       and x17, x1, #0xfffffffffffc0000
0x1266c1bbc    7c  f9400231       ldr x17, [x17]
0x1266c1bc0    80  37100591       tbnz w17, #2, #+0xb0 (addr 0x1266c1c70)
0x1266c1bc4    84  580009a0       ldr x0, pc+308 (addr 0x00000001266c1cf8)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c1bc8    88  f81ff020       stur x0, [x1, #-1]
0x1266c1bcc    8c  926eb431       and x17, x1, #0xfffffffffffc0000
0x1266c1bd0    90  f9400231       ldr x17, [x17]
0x1266c1bd4    94  371005f1       tbnz w17, #2, #+0xbc (addr 0x1266c1c90)
0x1266c1bd8    98  58000940       ldr x0, pc+296 (addr 0x00000001266c1d00)    ;; object: 0x1dadb5f42c19 <FeedbackCell[one closure]>
0x1266c1bdc    9c  b8413001       ldur w1, [x0, #19]
0x1266c1be0    a0  71003421       subs w1, w1, #0xd (13)
0x1266c1be4    a4  b8013001       stur w1, [x0, #19]
0x1266c1be8    a8  5400064b       b.lt #+0xc8 (addr 0x1266c1cb0)
0x1266c1bec    ac  f940d340       ldr x0, [x26, #416]
0x1266c1bf0    b0  f85e83a9       ldur x9, [fp, #-24]
0x1266c1bf4    b4  d280006a       movz x10, #0x3
0x1266c1bf8    b8  eb09015f       cmp x10, x9
0x1266c1bfc    bc  5400004a       b.ge #+0x8 (addr 0x1266c1c04)
0x1266c1c00    c0  aa0903ea       mov x10, x9
0x1266c1c04    c4  910003bf       mov sp, fp
0x1266c1c08    c8  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c1c0c    cc  91000550       add x16, x10, #0x1 (1)
0x1266c1c10    d0  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c1c14    d4  8b306fff       add sp, sp, x16, lsl #3
0x1266c1c18    d8  d65f03c0       ret
0x1266c1c1c    dc  d2c03600       movz x0, #0x1b000000000
0x1266c1c20    e0  580007d0       ldr x16, pc+248 (addr 0x00000001266c1d18)
0x1266c1c24    e4  d63f0200       blr x16
0x1266c1c28    e8  17ffffce       b #-0xc8 (addr 0x1266c1b60)
0x1266c1c2c    ec  d4200000       brk #0x0
0x1266c1c30    f0  926eb411       and x17, x0, #0xfffffffffffc0000
0x1266c1c34    f4  f9400231       ldr x17, [x17]
0x1266c1c38    f8  360ffaf1       tbz w17, #1, #-0xa4 (addr 0x1266c1b94)
0x1266c1c3c    fc  91005c25       add x5, x1, #0x17 (23)
0x1266c1c40   100  58000690       ldr x16, pc+208 (addr 0x00000001266c1d10)
0x1266c1c44   104  d63f0200       blr x16
0x1266c1c48   108  17ffffd3       b #-0xb4 (addr 0x1266c1b94)
0x1266c1c4c   10c  d4200000       brk #0x0
0x1266c1c50   110  926eb451       and x17, x2, #0xfffffffffffc0000
0x1266c1c54   114  f9400231       ldr x17, [x17]
0x1266c1c58   118  360ffa91       tbz w17, #1, #-0xb0 (addr 0x1266c1ba8)
0x1266c1c5c   11c  d1000425       sub x5, x1, #0x1 (1)
0x1266c1c60   120  58000590       ldr x16, pc+176 (addr 0x00000001266c1d10)
0x1266c1c64   124  d63f0200       blr x16
0x1266c1c68   128  17ffffd0       b #-0xc0 (addr 0x1266c1ba8)
0x1266c1c6c   12c  d4200000       brk #0x0
0x1266c1c70   130  926eb451       and x17, x2, #0xfffffffffffc0000
0x1266c1c74   134  f9400231       ldr x17, [x17]
0x1266c1c78   138  360ffa71       tbz w17, #1, #-0xb4 (addr 0x1266c1bc4)
0x1266c1c7c   13c  91007c25       add x5, x1, #0x1f (31)
0x1266c1c80   140  58000490       ldr x16, pc+144 (addr 0x00000001266c1d10)
0x1266c1c84   144  d63f0200       blr x16
0x1266c1c88   148  17ffffcf       b #-0xc4 (addr 0x1266c1bc4)
0x1266c1c8c   14c  d4200000       brk #0x0
0x1266c1c90   150  926eb411       and x17, x0, #0xfffffffffffc0000
0x1266c1c94   154  f9400231       ldr x17, [x17]
0x1266c1c98   158  360ffa11       tbz w17, #1, #-0xc0 (addr 0x1266c1bd8)
0x1266c1c9c   15c  d1000425       sub x5, x1, #0x1 (1)
0x1266c1ca0   160  58000390       ldr x16, pc+112 (addr 0x00000001266c1d10)
0x1266c1ca4   164  d63f0200       blr x16
0x1266c1ca8   168  17ffffcc       b #-0xd0 (addr 0x1266c1bd8)
0x1266c1cac   16c  d4200000       brk #0x0
0x1266c1cb0   170  f85f03a1       ldur x1, [fp, #-16]
0x1266c1cb4   174  a9bf7fe1       stp x1, xzr, [sp, #-16]!
0x1266c1cb8   178  5800029b       ldr cp, pc+80 (addr 0x00000001266c1d08)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c1cbc   17c  d2800020       movz x0, #0x1
0x1266c1cc0   180  d29d9b01       movz x1, #0xecd8
0x1266c1cc4   184  f2a06081       movk x1, #0x304, lsl #16
0x1266c1cc8   188  f2c00021       movk x1, #0x1, lsl #32
0x1266c1ccc   18c  580002b0       ldr x16, pc+84 (addr 0x00000001266c1d20)
0x1266c1cd0   190  d63f0200       blr x16
0x1266c1cd4   194  17ffffc6       b #-0xe8 (addr 0x1266c1bec)
0x1266c1cd8   198  d4200000       brk #0x0
0x1266c1cdc   19c  5800025f       constant pool begin (num_const = 18)    ;; constant pool
0x1266c1ce0   1a0  d63f03e0       constant
0x1266c1ce4   1a4  d503201f       constant
0x1266c1ce8   1a8  b5f49181       constant
0x1266c1cec   1ac  00001dad       constant
0x1266c1cf0   1b0  b5f49201       constant
0x1266c1cf4   1b4  00001dad       constant
0x1266c1cf8   1b8  b5f49259       constant
0x1266c1cfc   1bc  00001dad       constant
0x1266c1d00   1c0  b5f42c19       constant
0x1266c1d04   1c4  00001dad       constant
0x1266c1d08   1c8  24400109       constant
0x1266c1d0c   1cc  00002347       constant
0x1266c1d10   1d0  035fce40       constant
0x1266c1d14   1d4  00000001       constant
0x1266c1d18   1d8  03609ba0       constant
0x1266c1d1c   1dc  00000001       constant
0x1266c1d20   1e0  036a61e0       constant
0x1266c1d24   1e4  00000001       constant
0x1266c1d28   1e8  f8558350       ldur x16, [x26, #-168]
0x1266c1d2c   1ec  d61f0200       br x16
0x1266c1d30   1f0  f8560350       ldur x16, [x26, #-160]
0x1266c1d34   1f4  d61f0200       br x16
0x1266c1d38   1f8  97fffffc       bl #-0x10 (addr 0x1266c1d28)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 0
0x1266c1d3c   1fc  97fffffb       bl #-0x14 (addr 0x1266c1d28)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 1
0x1266c1d40   200  97fffffa       bl #-0x18 (addr 0x1266c1d28)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 2
0x1266c1d44   204  97fffffb       bl #-0x14 (addr 0x1266c1d30)    ;; debug: deopt position, script offset '4c0'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 3

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 4)
 index  bytecode-offset    pc
     0                2   1f8 
     1                2   1fc 
     2                8   200 
     3               -1   204 

Safepoints (stack slots = 6, entries = 2, byte size = 28, tagged slots = 0)
0x1266c1c28     e8  num extra spill slots: 0  deopt      3 trampoline:    204
0x1266c1cd4    194  num extra spill slots: 0

RelocInfo (size = 99)
0x1266c1b6c  full embedded object  (0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>)
0x1266c1b94  full embedded object  (0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>)
0x1266c1bc4  full embedded object  (0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>)
0x1266c1bd8  full embedded object  (0x1dadb5f42c19 <FeedbackCell[one closure]>)
0x1266c1cb8  full embedded object  (0x234724400109 <NativeContext[302]>)
0x1266c1cdc  constant pool (size 76)
0x1266c1d38  deopt script offset  (1250)
0x1266c1d38  deopt inlining id  (-1)
0x1266c1d38  deopt reason  (wrong map)
0x1266c1d38  deopt index
0x1266c1d3c  deopt script offset  (1250)
0x1266c1d3c  deopt inlining id  (-1)
0x1266c1d3c  deopt reason  (Smi)
0x1266c1d3c  deopt index
0x1266c1d40  deopt script offset  (1277)
0x1266c1d40  deopt inlining id  (-1)
0x1266c1d40  deopt reason  (Smi)
0x1266c1d40  deopt index
0x1266c1d44  deopt script offset  (1216)
0x1266c1d44  deopt inlining id  (-1)
0x1266c1d44  deopt reason  ((unknown))
0x1266c1d44  deopt index

[completed compiling 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> (target MAGLEV) - took 0.000, 0.208, 0.375 ms]
[compiling method 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> (target MAGLEV), mode: ConcurrencyMode::kSynchronous]
0x1ae954e426f1: [Code]
 - map: 0x1d42df7817e9 <Map[88](CODE_TYPE)>
 - kind: MAGLEV
 - deoptimization_data_or_interpreter_data: 0x1ae954e42439 <ProtectedFixedArray[33]>
 - position_table: 0x1bc26a780011 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - parameter_count: 2
 - instruction_stream: 0x0001266c1d81 <InstructionStream MAGLEV>
 - instruction_start: 0x1266c1da0
 - is_turbofanned: 0
 - stack_slots: 8
 - marked_for_deoptimization: 0
 - embedded_objects_cleared: 0
 - can_have_weak_objects: 0
 - instruction_size: 932
 - metadata_size: 80
 - inlined_bytecode_size: 0
 - osr_offset: -1
 - handler_table_offset: 80
 - unwinding_info_offset: 80
 - code_comments_offset: 80
 - instruction_stream.relocation_info: 0x1ae954e42631 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - instruction_stream.body_size: 1012

--- Disassembly: ---
kind = MAGLEV
name = bottomUpTree
compiler = maglev
address = 0x1ae954e426f1

Instructions (size = 932)
0x1266c1da0     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c1da4     4  910003fd       mov fp, sp
0x1266c1da8     8  a9bf6fe1       stp x1, cp, [sp, #-16]!
0x1266c1dac     c  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c1db0    10  a9bf7fff       stp xzr, xzr, [sp, #-16]!
0x1266c1db4    14  d106c3f0       sub x16, sp, #0x1b0 (432)
0x1266c1db8    18  f8520351       ldur x17, [x26, #-224]
0x1266c1dbc    1c  eb11021f       cmp x16, x17
0x1266c1dc0    20  54001123       b.lo #+0x224 (addr 0x1266c1fe4)
0x1266c1dc4    24  f9400fa0       ldr x0, [fp, #24]
0x1266c1dc8    28  37001b00       tbnz w0, #0, #+0x360 (addr 0x1266c2128)
0x1266c1dcc    2c  d360fc00       lsr x0, x0, #32
0x1266c1dd0    30  52800001       movz w1, #0x0
0x1266c1dd4    34  6b01001f       cmp w0, w1
0x1266c1dd8    38  5400092d       b.le #+0x124 (addr 0x1266c1efc)
0x1266c1ddc    3c  71000401       subs w1, w0, #0x1 (1)
0x1266c1de0    40  54001a66       b.vs #+0x34c (addr 0x1266c212c)
0x1266c1de4    44  d3607c20       lsl x0, x1, #32
0x1266c1de8    48  f81e03a0       stur x0, [fp, #-32]
0x1266c1dec    4c  580016a1       ldr x1, pc+724 (addr 0x00000001266c20c0)    ;; object: 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1266c1df0    50  580016db       ldr cp, pc+728 (addr 0x00000001266c20c8)    ;; object: 0x3224a5e677f1 <FunctionContext[7]>
0x1266c1df4    54  f940d343       ldr x3, [x26, #416]
0x1266c1df8    58  a9bf03e3       stp x3, x0, [sp, #-16]!
0x1266c1dfc    5c  52800040       movz w0, #0x2
0x1266c1e00    60  18001784       ldr w4, pc+752 (addr 0x00000001266c20f0)    ;; js dispatch handle:0x2c4700 Builtin::InterpreterEntryTrampoline
0x1266c1e04    64  d2a1cd55       movz x21, #0xe6a0000
0x1266c1e08    68  f2c00035       movk x21, #0x1, lsl #32
0x1266c1e0c    6c  d2988e10       movz x16, #0xc470
0x1266c1e10    70  f2a00050       movk x16, #0x2, lsl #16
0x1266c1e14    74  f8706aa2       ldr x2, [x21, x16]
0x1266c1e18    78  d63f0040       blr x2
0x1266c1e1c    7c  f81d83a0       stur x0, [fp, #-40]
0x1266c1e20    80  58001501       ldr x1, pc+672 (addr 0x00000001266c20c0)    ;; object: 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1266c1e24    84  5800153b       ldr cp, pc+676 (addr 0x00000001266c20c8)    ;; object: 0x3224a5e677f1 <FunctionContext[7]>
0x1266c1e28    88  f940d343       ldr x3, [x26, #416]
0x1266c1e2c    8c  f85e03b0       ldur x16, [fp, #-32]
0x1266c1e30    90  a9bf43e3       stp x3, x16, [sp, #-16]!
0x1266c1e34    94  52800040       movz w0, #0x2
0x1266c1e38    98  180015c4       ldr w4, pc+696 (addr 0x00000001266c20f0)
0x1266c1e3c    9c  d2a1cd55       movz x21, #0xe6a0000
0x1266c1e40    a0  f2c00035       movk x21, #0x1, lsl #32
0x1266c1e44    a4  d2988e10       movz x16, #0xc470
0x1266c1e48    a8  f2a00050       movk x16, #0x2, lsl #16
0x1266c1e4c    ac  f8706aa2       ldr x2, [x21, x16]
0x1266c1e50    b0  d63f0040       blr x2
0x1266c1e54    b4  f85d0341       ldur x1, [x26, #-48]
0x1266c1e58    b8  9100a021       add x1, x1, #0x28 (40)
0x1266c1e5c    bc  f85d8350       ldur x16, [x26, #-40]
0x1266c1e60    c0  eb10003f       cmp x1, x16
0x1266c1e64    c4  54000e42       b.hs #+0x1c8 (addr 0x1266c202c)
0x1266c1e68    c8  f81d0341       stur x1, [x26, #-48]
0x1266c1e6c    cc  d1009c21       sub x1, x1, #0x27 (39)
0x1266c1e70    d0  f81d03a1       stur x1, [fp, #-48]
0x1266c1e74    d4  580012e2       ldr x2, pc+604 (addr 0x00000001266c20d0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1266c1e78    d8  f81ff022       stur x2, [x1, #-1]
0x1266c1e7c    dc  f9413742       ldr x2, [x26, #616]
0x1266c1e80    e0  f8007022       stur x2, [x1, #7]
0x1266c1e84    e4  f800f022       stur x2, [x1, #15]
0x1266c1e88    e8  f940c743       ldr x3, [x26, #392]
0x1266c1e8c    ec  f8017023       stur x3, [x1, #23]
0x1266c1e90    f0  f801f023       stur x3, [x1, #31]
0x1266c1e94    f4  aa0103e4       mov x4, x1
0x1266c1e98    f8  58001201       ldr x1, pc+576 (addr 0x00000001266c20d8)    ;; object: 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x1266c1e9c    fc  5800117b       ldr cp, pc+556 (addr 0x00000001266c20c8)    ;; object: 0x3224a5e677f1 <FunctionContext[7]>
0x1266c1ea0   100  aa0103e3       mov x3, x1
0x1266c1ea4   104  a9bf7fe0       stp x0, xzr, [sp, #-16]!
0x1266c1ea8   108  f85d83b0       ldur x16, [fp, #-40]
0x1266c1eac   10c  a9bf43e4       stp x4, x16, [sp, #-16]!
0x1266c1eb0   110  52800060       movz w0, #0x3
0x1266c1eb4   114  18001224       ldr w4, pc+580 (addr 0x00000001266c20f8)    ;; js dispatch handle:0x2c4800 MAGLEV
0x1266c1eb8   118  d2a1cd55       movz x21, #0xe6a0000
0x1266c1ebc   11c  f2c00035       movk x21, #0x1, lsl #32
0x1266c1ec0   120  d2989010       movz x16, #0xc480
0x1266c1ec4   124  f2a00050       movk x16, #0x2, lsl #16
0x1266c1ec8   128  f8706aa2       ldr x2, [x21, x16]
0x1266c1ecc   12c  d63f0040       blr x2
0x1266c1ed0   130  f85d03a1       ldur x1, [fp, #-48]
0x1266c1ed4   134  f940d350       ldr x16, [x26, #416]
0x1266c1ed8   138  eb10001f       cmp x0, x16
0x1266c1edc   13c  540000c0       b.eq #+0x18 (addr 0x1266c1ef4)
0x1266c1ee0   140  360000a0       tbz w0, #0, #+0x14 (addr 0x1266c1ef4)
0x1266c1ee4   144  f85ff010       ldur x16, [x0, #-1]
0x1266c1ee8   148  7840b210       ldurh w16, [x16, #11]
0x1266c1eec   14c  f104a61f       cmp x16, #0x129 (297)
0x1266c1ef0   150  54000042       b.hs #+0x8 (addr 0x1266c1ef8)
0x1266c1ef4   154  aa0103e0       mov x0, x1
0x1266c1ef8   158  1400002b       b #+0xac (addr 0x1266c1fa4)
0x1266c1efc   15c  f85d0341       ldur x1, [x26, #-48]
0x1266c1f00   160  9100a021       add x1, x1, #0x28 (40)
0x1266c1f04   164  f85d8350       ldur x16, [x26, #-40]
0x1266c1f08   168  eb10003f       cmp x1, x16
0x1266c1f0c   16c  54000a02       b.hs #+0x140 (addr 0x1266c204c)
0x1266c1f10   170  f81d0341       stur x1, [x26, #-48]
0x1266c1f14   174  d1009c21       sub x1, x1, #0x27 (39)
0x1266c1f18   178  f81d03a1       stur x1, [fp, #-48]
0x1266c1f1c   17c  58000da0       ldr x0, pc+436 (addr 0x00000001266c20d0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1266c1f20   180  f81ff020       stur x0, [x1, #-1]
0x1266c1f24   184  f9413740       ldr x0, [x26, #616]
0x1266c1f28   188  f8007020       stur x0, [x1, #7]
0x1266c1f2c   18c  f800f020       stur x0, [x1, #15]
0x1266c1f30   190  f940c740       ldr x0, [x26, #392]
0x1266c1f34   194  f8017020       stur x0, [x1, #23]
0x1266c1f38   198  f801f020       stur x0, [x1, #31]
0x1266c1f3c   19c  aa0103e0       mov x0, x1
0x1266c1f40   1a0  58000cc1       ldr x1, pc+408 (addr 0x00000001266c20d8)    ;; object: 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x1266c1f44   1a4  58000c3b       ldr cp, pc+388 (addr 0x00000001266c20c8)    ;; object: 0x3224a5e677f1 <FunctionContext[7]>
0x1266c1f48   1a8  aa0103e3       mov x3, x1
0x1266c1f4c   1ac  f940db50       ldr x16, [x26, #432]
0x1266c1f50   1b0  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x1266c1f54   1b4  f940db50       ldr x16, [x26, #432]
0x1266c1f58   1b8  a9bf43e0       stp x0, x16, [sp, #-16]!
0x1266c1f5c   1bc  52800060       movz w0, #0x3
0x1266c1f60   1c0  18000cc4       ldr w4, pc+408 (addr 0x00000001266c20f8)
0x1266c1f64   1c4  d2a1cd55       movz x21, #0xe6a0000
0x1266c1f68   1c8  f2c00035       movk x21, #0x1, lsl #32
0x1266c1f6c   1cc  d2989010       movz x16, #0xc480
0x1266c1f70   1d0  f2a00050       movk x16, #0x2, lsl #16
0x1266c1f74   1d4  f8706aa2       ldr x2, [x21, x16]
0x1266c1f78   1d8  d63f0040       blr x2
0x1266c1f7c   1dc  f85d03a1       ldur x1, [fp, #-48]
0x1266c1f80   1e0  f940d350       ldr x16, [x26, #416]
0x1266c1f84   1e4  eb10001f       cmp x0, x16
0x1266c1f88   1e8  540000c0       b.eq #+0x18 (addr 0x1266c1fa0)
0x1266c1f8c   1ec  360000a0       tbz w0, #0, #+0x14 (addr 0x1266c1fa0)
0x1266c1f90   1f0  f85ff010       ldur x16, [x0, #-1]
0x1266c1f94   1f4  7840b210       ldurh w16, [x16, #11]
0x1266c1f98   1f8  f104a61f       cmp x16, #0x129 (297)
0x1266c1f9c   1fc  54000042       b.hs #+0x8 (addr 0x1266c1fa4)
0x1266c1fa0   200  aa0103e0       mov x0, x1
0x1266c1fa4   204  580009e1       ldr x1, pc+316 (addr 0x00000001266c20e0)    ;; object: 0x1dadb5f42c01 <FeedbackCell[one closure]>
0x1266c1fa8   208  b8413022       ldur w2, [x1, #19]
0x1266c1fac   20c  71010042       subs w2, w2, #0x40 (64)
0x1266c1fb0   210  b8013022       stur w2, [x1, #19]
0x1266c1fb4   214  5400058b       b.lt #+0xb0 (addr 0x1266c2064)
0x1266c1fb8   218  f85e83a9       ldur x9, [fp, #-24]
0x1266c1fbc   21c  d280004a       movz x10, #0x2
0x1266c1fc0   220  eb09015f       cmp x10, x9
0x1266c1fc4   224  5400004a       b.ge #+0x8 (addr 0x1266c1fcc)
0x1266c1fc8   228  aa0903ea       mov x10, x9
0x1266c1fcc   22c  910003bf       mov sp, fp
0x1266c1fd0   230  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c1fd4   234  91000550       add x16, x10, #0x1 (1)
0x1266c1fd8   238  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c1fdc   23c  8b306fff       add sp, sp, x16, lsl #3
0x1266c1fe0   240  d65f03c0       ret
0x1266c1fe4   244  d2c03600       movz x0, #0x1b000000000
0x1266c1fe8   248  580008d0       ldr x16, pc+280 (addr 0x00000001266c2100)
0x1266c1fec   24c  d63f0200       blr x16
0x1266c1ff0   250  17ffff75       b #-0x22c (addr 0x1266c1dc4)
0x1266c1ff4   254  d4200000       brk #0x0
0x1266c1ff8   258  1e62003e       scvtf d30, w1
0x1266c1ffc   25c  f85d0340       ldur x0, [x26, #-48]
0x1266c2000   260  91004000       add x0, x0, #0x10 (16)
0x1266c2004   264  f85d8350       ldur x16, [x26, #-40]
0x1266c2008   268  eb10001f       cmp x0, x16
0x1266c200c   26c  54000462       b.hs #+0x8c (addr 0x1266c2098)
0x1266c2010   270  f81d0340       stur x0, [x26, #-48]
0x1266c2014   274  d1003c00       sub x0, x0, #0xf (15)
0x1266c2018   278  f9412750       ldr x16, [x26, #584]
0x1266c201c   27c  f81ff010       stur x16, [x0, #-1]
0x1266c2020   280  fc00701e       stur d30, [x0, #7]
0x1266c2024   284  17ffff71       b #-0x23c (addr 0x1266c1de8)
0x1266c2028   288  d4200000       brk #0x0
0x1266c202c   28c  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c2030   290  52800501       movz w1, #0x28
0x1266c2034   294  580006b0       ldr x16, pc+212 (addr 0x00000001266c2108)
0x1266c2038   298  d63f0200       blr x16
0x1266c203c   29c  aa0003e1       mov x1, x0
0x1266c2040   2a0  a8c103ff       ldp xzr, x0, [sp], #16
0x1266c2044   2a4  17ffff8b       b #-0x1d4 (addr 0x1266c1e70)
0x1266c2048   2a8  d4200000       brk #0x0
0x1266c204c   2ac  52800501       movz w1, #0x28
0x1266c2050   2b0  580005d0       ldr x16, pc+184 (addr 0x00000001266c2108)
0x1266c2054   2b4  d63f0200       blr x16
0x1266c2058   2b8  aa0003e1       mov x1, x0
0x1266c205c   2bc  17ffffaf       b #-0x144 (addr 0x1266c1f18)
0x1266c2060   2c0  d4200000       brk #0x0
0x1266c2064   2c4  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c2068   2c8  f85f03a2       ldur x2, [fp, #-16]
0x1266c206c   2cc  a9bf7fe2       stp x2, xzr, [sp, #-16]!
0x1266c2070   2d0  580003db       ldr cp, pc+120 (addr 0x00000001266c20e8)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c2074   2d4  d2800020       movz x0, #0x1
0x1266c2078   2d8  d29d9b01       movz x1, #0xecd8
0x1266c207c   2dc  f2a06081       movk x1, #0x304, lsl #16
0x1266c2080   2e0  f2c00021       movk x1, #0x1, lsl #32
0x1266c2084   2e4  58000470       ldr x16, pc+140 (addr 0x00000001266c2110)
0x1266c2088   2e8  d63f0200       blr x16
0x1266c208c   2ec  a8c103ff       ldp xzr, x0, [sp], #16
0x1266c2090   2f0  17ffffca       b #-0xd8 (addr 0x1266c1fb8)
0x1266c2094   2f4  d4200000       brk #0x0
0x1266c2098   2f8  6dbf7bef       stp d15, d30, [sp, #-16]!
0x1266c209c   2fc  52800201       movz w1, #0x10
0x1266c20a0   300  58000350       ldr x16, pc+104 (addr 0x00000001266c2108)
0x1266c20a4   304  d63f0200       blr x16
0x1266c20a8   308  6cc17bef       ldp d15, d30, [sp], #16
0x1266c20ac   30c  17ffffdb       b #-0x94 (addr 0x1266c2018)
0x1266c20b0   310  d4200000       brk #0x0
0x1266c20b4   314  5800031f       constant pool begin (num_const = 24)    ;; constant pool
0x1266c20b8   318  d63f03e0       constant
0x1266c20bc   31c  d503201f       constant
0x1266c20c0   320  a5e678f9       constant
0x1266c20c4   324  00003224       constant
0x1266c20c8   328  a5e677f1       constant
0x1266c20cc   32c  00003224       constant
0x1266c20d0   330  b5f49181       constant
0x1266c20d4   334  00001dad       constant
0x1266c20d8   338  a5e686f1       constant
0x1266c20dc   33c  00003224       constant
0x1266c20e0   340  b5f42c01       constant
0x1266c20e4   344  00001dad       constant
0x1266c20e8   348  24400109       constant
0x1266c20ec   34c  00002347       constant
0x1266c20f0   350  002c4700       constant
0x1266c20f4   354  00000000       constant
0x1266c20f8   358  002c4800       constant
0x1266c20fc   35c  00000000       constant
0x1266c2100   360  03609ba0       constant
0x1266c2104   364  00000001       constant
0x1266c2108   368  0360ace0       constant
0x1266c210c   36c  00000001       constant
0x1266c2110   370  036a61e0       constant
0x1266c2114   374  00000001       constant
0x1266c2118   378  f8558350       ldur x16, [x26, #-168]
0x1266c211c   37c  d61f0200       br x16
0x1266c2120   380  f8560350       ldur x16, [x26, #-160]
0x1266c2124   384  d61f0200       br x16
0x1266c2128   388  97fffffc       bl #-0x10 (addr 0x1266c2118)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x1266c212c   38c  97fffffb       bl #-0x14 (addr 0x1266c2118)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 1
0x1266c2130   390  97fffffc       bl #-0x10 (addr 0x1266c2120)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2
0x1266c2134   394  97fffffb       bl #-0x14 (addr 0x1266c2120)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 3
0x1266c2138   398  97fffffa       bl #-0x18 (addr 0x1266c2120)    ;; debug: deopt position, script offset '5f3'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 4
0x1266c213c   39c  97fffff9       bl #-0x1c (addr 0x1266c2120)    ;; debug: deopt position, script offset '63c'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 5
0x1266c2140   3a0  97fffff8       bl #-0x20 (addr 0x1266c2120)    ;; debug: deopt position, script offset '5ca'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 6

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 7)
 index  bytecode-offset    pc
     0                1   388 
     1                1   38c 
     2               20   390 
     3               34   394 
     4               -1   398 
     5               -1   39c 
     6               -1   3a0 

Safepoints (stack slots = 8, entries = 9, byte size = 79, tagged slots = 3)
0x1266c1e1c     7c  num extra spill slots: 0  deopt      2 trampoline:    390
0x1266c1e54     b4  num extra spill slots: 0  deopt      3 trampoline:    394
0x1266c1ed0    130  num extra spill slots: 0  deopt      4 trampoline:    398
0x1266c1f7c    1dc  num extra spill slots: 0  deopt      5 trampoline:    39c
0x1266c1ff0    250  num extra spill slots: 0  deopt      6 trampoline:    3a0
0x1266c203c    29c  num extra spill slots: 2  registers: 1
0x1266c2058    2b8  num extra spill slots: 0
0x1266c208c    2ec  num extra spill slots: 2  registers: 1
0x1266c20a8    308  num extra spill slots: 2

RelocInfo (size = 175)
0x1266c1dec  full embedded object  (0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>)
0x1266c1df0  full embedded object  (0x3224a5e677f1 <FunctionContext[7]>)
0x1266c1e00  js dispatch handle (BUILTIN InterpreterEntryTrampoline)  (2901760)
0x1266c1e74  full embedded object  (0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>)
0x1266c1e98  full embedded object  (0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>)
0x1266c1eb4  js dispatch handle (MAGLEV)  (2902016)
0x1266c1fa4  full embedded object  (0x1dadb5f42c01 <FeedbackCell[one closure]>)
0x1266c2070  full embedded object  (0x234724400109 <NativeContext[302]>)
0x1266c20b4  constant pool (size 100)
0x1266c2128  deopt script offset  (1509)
0x1266c2128  deopt inlining id  (-1)
0x1266c2128  deopt reason  (not a Smi)
0x1266c2128  deopt index
0x1266c212c  deopt script offset  (1509)
0x1266c212c  deopt inlining id  (-1)
0x1266c212c  deopt reason  (overflow)
0x1266c212c  deopt index
0x1266c2130  deopt script offset  (1536)
0x1266c2130  deopt inlining id  (-1)
0x1266c2130  deopt reason  ((unknown))
0x1266c2130  deopt index
0x1266c2134  deopt script offset  (1561)
0x1266c2134  deopt inlining id  (-1)
0x1266c2134  deopt reason  ((unknown))
0x1266c2134  deopt index
0x1266c2138  deopt script offset  (1523)
0x1266c2138  deopt inlining id  (-1)
0x1266c2138  deopt reason  ((unknown))
0x1266c2138  deopt index
0x1266c213c  deopt script offset  (1596)
0x1266c213c  deopt inlining id  (-1)
0x1266c213c  deopt reason  ((unknown))
0x1266c213c  deopt index
0x1266c2140  deopt script offset  (1482)
0x1266c2140  deopt inlining id  (-1)
0x1266c2140  deopt reason  ((unknown))
0x1266c2140  deopt index

[completed compiling 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> (target MAGLEV) - took 0.000, 0.416, 0.584 ms]
[marking 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> for optimization to TURBOFAN_JS, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x3224a5e678f9 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> (target TURBOFAN_JS), mode: ConcurrencyMode::kConcurrent]
[marking 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> for optimization to TURBOFAN_JS, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x3224a5e686f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> (target TURBOFAN_JS), mode: ConcurrencyMode::kConcurrent]
--- Raw source ---
(left, right) {
        this.left = left;
        this.right = right;
    }


--- Optimized code ---
optimization_id = 5
source_position = 1216
kind = TURBOFAN_JS
name = TreeNode
compiler = turbofan
address = 0x1ae954e42981

Instructions (size = 508)
0x1266c21c0     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c21c4     4  910003fd       mov fp, sp
0x1266c21c8     8  a9be03ff       stp xzr, x0, [sp, #-32]!
0x1266c21cc     c  a9016fe1       stp x1, cp, [sp, #16]
0x1266c21d0    10  f8520342       ldur x2, [x26, #-224]
0x1266c21d4    14  f90003fb       str cp, [sp]
0x1266c21d8    18  eb2263ff       cmp sp, x2
0x1266c21dc    1c  54000569       b.ls #+0xac (addr 0x1266c2288)
0x1266c21e0    20  f9401be2       ldr x2, [sp, #48]
0x1266c21e4    24  f240005f       tst x2, #0x1
0x1266c21e8    28  54000e00       b.eq #+0x1c0 (addr 0x1266c23a8)
0x1266c21ec    2c  f85ff043       ldur x3, [x2, #-1]
0x1266c21f0    30  58000bc4       ldr x4, pc+376 (addr 0x00000001266c2368)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1266c21f4    34  eb04007f       cmp x3, x4
0x1266c21f8    38  54000da1       b.ne #+0x1b4 (addr 0x1266c23ac)
0x1266c21fc    3c  f9401fe3       ldr x3, [sp, #56]
0x1266c2200    40  f240007f       tst x3, #0x1
0x1266c2204    44  54000d60       b.eq #+0x1ac (addr 0x1266c23b0)
0x1266c2208    48  58000b44       ldr x4, pc+360 (addr 0x00000001266c2370)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1266c220c    4c  f81ff044       stur x4, [x2, #-1]
0x1266c2210    50  926eb450       and x16, x2, #0xfffffffffffc0000
0x1266c2214    54  f9400210       ldr x16, [x16]
0x1266c2218    58  371008d0       tbnz w16, #2, #+0x118 (addr 0x1266c2330)
0x1266c221c    5c  f8017043       stur x3, [x2, #23]
0x1266c2220    60  926eb450       and x16, x2, #0xfffffffffffc0000
0x1266c2224    64  f9400210       ldr x16, [x16]
0x1266c2228    68  37100710       tbnz w16, #2, #+0xe0 (addr 0x1266c2308)
0x1266c222c    6c  f94023e4       ldr x4, [sp, #64]
0x1266c2230    70  f240009f       tst x4, #0x1
0x1266c2234    74  54000c00       b.eq #+0x180 (addr 0x1266c23b4)
0x1266c2238    78  58000a03       ldr x3, pc+320 (addr 0x00000001266c2378)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c223c    7c  f81ff043       stur x3, [x2, #-1]
0x1266c2240    80  926eb450       and x16, x2, #0xfffffffffffc0000
0x1266c2244    84  f9400210       ldr x16, [x16]
0x1266c2248    88  371004d0       tbnz w16, #2, #+0x98 (addr 0x1266c22e0)
0x1266c224c    8c  f801f044       stur x4, [x2, #31]
0x1266c2250    90  926eb450       and x16, x2, #0xfffffffffffc0000
0x1266c2254    94  f9400210       ldr x16, [x16]
0x1266c2258    98  37100310       tbnz w16, #2, #+0x60 (addr 0x1266c22b8)
0x1266c225c    9c  f940d340       ldr x0, [x26, #416]
0x1266c2260    a0  f85e83a3       ldur x3, [fp, #-24]
0x1266c2264    a4  910003bf       mov sp, fp
0x1266c2268    a8  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c226c    ac  f1000c7f       cmp x3, #0x3 (3)
0x1266c2270    b0  5400004a       b.ge #+0x8 (addr 0x1266c2278)
0x1266c2274    b4  d2800063       movz x3, #0x3
0x1266c2278    b8  91000470       add x16, x3, #0x1 (1)
0x1266c227c    bc  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c2280    c0  8b306fff       add sp, sp, x16, lsl #3
0x1266c2284    c4  d65f03c0       ret
0x1266c2288    c8  d2c00502       movz x2, #0x2800000000
0x1266c228c    cc  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2290    d0  f90007ff       str xzr, [sp, #8]
0x1266c2294    d4  f90003e2       str x2, [sp]
0x1266c2298    d8  d29d4f01       movz x1, #0xea78
0x1266c229c    dc  f2a06081       movk x1, #0x304, lsl #16
0x1266c22a0    e0  f2c00021       movk x1, #0x1, lsl #32
0x1266c22a4    e4  d2800020       movz x0, #0x1
0x1266c22a8    e8  580006db       ldr cp, pc+216 (addr 0x00000001266c2380)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c22ac    ec  58000730       ldr x16, pc+228 (addr 0x00000001266c2390)
0x1266c22b0    f0  d63f0200       blr x16
0x1266c22b4    f4  17ffffcb       b #-0xd4 (addr 0x1266c21e0)
0x1266c22b8    f8  926eb490       and x16, x4, #0xfffffffffffc0000
0x1266c22bc    fc  f9400210       ldr x16, [x16]
0x1266c22c0   100  360ffcf0       tbz w16, #1, #-0x64 (addr 0x1266c225c)
0x1266c22c4   104  a9bf17e1       stp x1, x5, [sp, #-16]!
0x1266c22c8   108  91007c45       add x5, x2, #0x1f (31)
0x1266c22cc   10c  aa0203e1       mov x1, x2
0x1266c22d0   110  580005d0       ldr x16, pc+184 (addr 0x00000001266c2388)
0x1266c22d4   114  d63f0200       blr x16
0x1266c22d8   118  a8c117e1       ldp x1, x5, [sp], #16
0x1266c22dc   11c  17ffffe0       b #-0x80 (addr 0x1266c225c)
0x1266c22e0   120  926eb470       and x16, x3, #0xfffffffffffc0000
0x1266c22e4   124  f9400210       ldr x16, [x16]
0x1266c22e8   128  360ffb30       tbz w16, #1, #-0x9c (addr 0x1266c224c)
0x1266c22ec   12c  a9bf17e1       stp x1, x5, [sp, #-16]!
0x1266c22f0   130  d1000445       sub x5, x2, #0x1 (1)
0x1266c22f4   134  aa0203e1       mov x1, x2
0x1266c22f8   138  58000490       ldr x16, pc+144 (addr 0x00000001266c2388)
0x1266c22fc   13c  d63f0200       blr x16
0x1266c2300   140  a8c117e1       ldp x1, x5, [sp], #16
0x1266c2304   144  17ffffd2       b #-0xb8 (addr 0x1266c224c)
0x1266c2308   148  926eb470       and x16, x3, #0xfffffffffffc0000
0x1266c230c   14c  f9400210       ldr x16, [x16]
0x1266c2310   150  360ff8f0       tbz w16, #1, #-0xe4 (addr 0x1266c222c)
0x1266c2314   154  a9bf17e1       stp x1, x5, [sp, #-16]!
0x1266c2318   158  91005c45       add x5, x2, #0x17 (23)
0x1266c231c   15c  aa0203e1       mov x1, x2
0x1266c2320   160  58000350       ldr x16, pc+104 (addr 0x00000001266c2388)
0x1266c2324   164  d63f0200       blr x16
0x1266c2328   168  a8c117e1       ldp x1, x5, [sp], #16
0x1266c232c   16c  17ffffc0       b #-0x100 (addr 0x1266c222c)
0x1266c2330   170  926eb490       and x16, x4, #0xfffffffffffc0000
0x1266c2334   174  f9400210       ldr x16, [x16]
0x1266c2338   178  360ff730       tbz w16, #1, #-0x11c (addr 0x1266c221c)
0x1266c233c   17c  a9bf17e1       stp x1, x5, [sp, #-16]!
0x1266c2340   180  d1000445       sub x5, x2, #0x1 (1)
0x1266c2344   184  aa0203e1       mov x1, x2
0x1266c2348   188  58000210       ldr x16, pc+64 (addr 0x00000001266c2388)
0x1266c234c   18c  d63f0200       blr x16
0x1266c2350   190  a8c117e1       ldp x1, x5, [sp], #16
0x1266c2354   194  17ffffb2       b #-0x138 (addr 0x1266c221c)
0x1266c2358   198  d503201f       nop
0x1266c235c   19c  580001df       constant pool begin (num_const = 14)    ;; constant pool
0x1266c2360   1a0  d63f03e0       constant
0x1266c2364   1a4  d503201f       constant
0x1266c2368   1a8  b5f49181       constant
0x1266c236c   1ac  00001dad       constant
0x1266c2370   1b0  b5f49201       constant
0x1266c2374   1b4  00001dad       constant
0x1266c2378   1b8  b5f49259       constant
0x1266c237c   1bc  00001dad       constant
0x1266c2380   1c0  24400109       constant
0x1266c2384   1c4  00002347       constant
0x1266c2388   1c8  035fc640       constant
0x1266c238c   1cc  00000001       constant
0x1266c2390   1d0  036a61e0       constant
0x1266c2394   1d4  00000001       constant
0x1266c2398   1d8  f8558350       ldur x16, [x26, #-168]
0x1266c239c   1dc  d61f0200       br x16
0x1266c23a0   1e0  f8560350       ldur x16, [x26, #-160]
0x1266c23a4   1e4  d61f0200       br x16
0x1266c23a8   1e8  97fffffc       bl #-0x10 (addr 0x1266c2398)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 0
0x1266c23ac   1ec  97fffffb       bl #-0x14 (addr 0x1266c2398)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 1
0x1266c23b0   1f0  97fffffa       bl #-0x18 (addr 0x1266c2398)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 2
0x1266c23b4   1f4  97fffff9       bl #-0x1c (addr 0x1266c2398)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 3
0x1266c23b8   1f8  97fffffa       bl #-0x18 (addr 0x1266c23a0)    ;; debug: deopt position, script offset '4c0'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 4

Source positions:
 pc offset  position
        10      1216
        20      1250
        6c      1277
        9c      1290
        c8      1216

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 5)
 index  bytecode-offset    pc
     0                2    NA 
     1                2    NA 
     2                2    NA 
     3                8    NA 
     4               -1    f4 

Safepoints (stack slots = 6, entries = 1, byte size = 18)
0x1266c22b4     f4  slots (sp->fp): 100000  deopt      4 trampoline:    1f8

RelocInfo (size = 79)
0x1266c21f0  full embedded object  (0x1dadb5f49181 <Map[28](HOLEY_ELEMENTS)>)
0x1266c2208  full embedded object  (0x1dadb5f49201 <Map[28](HOLEY_ELEMENTS)>)
0x1266c2238  full embedded object  (0x1dadb5f49259 <Map[28](HOLEY_ELEMENTS)>)
0x1266c22a8  full embedded object  (0x234724400109 <NativeContext[12e]>)
0x1266c235c  constant pool (size 3c)
0x1266c23a8  deopt script offset  (4e2)
0x1266c23a8  deopt inlining id  (ffffffffffffffff)
0x1266c23a8  deopt reason  (Smi)
0x1266c23a8  deopt index
0x1266c23ac  deopt script offset  (4e2)
0x1266c23ac  deopt inlining id  (ffffffffffffffff)
0x1266c23ac  deopt reason  (wrong map)
0x1266c23ac  deopt index
0x1266c23b0  deopt script offset  (4e2)
0x1266c23b0  deopt inlining id  (ffffffffffffffff)
0x1266c23b0  deopt reason  (Smi)
0x1266c23b0  deopt index
0x1266c23b4  deopt script offset  (4fd)
0x1266c23b4  deopt inlining id  (ffffffffffffffff)
0x1266c23b4  deopt reason  (Smi)
0x1266c23b4  deopt index
0x1266c23b8  deopt script offset  (4c0)
0x1266c23b8  deopt inlining id  (ffffffffffffffff)
0x1266c23b8  deopt reason  ((unknown))
0x1266c23b8  deopt index

--- End code ---
[completed compiling 0x2ff96b6426f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> (target TURBOFAN_JS) - took 0.000, 0.667, 0.417 ms]
[completed optimizing 0x2ff96b6426f1 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)> (target TURBOFAN_JS)]
--- Raw source ---
(depth) {
    return depth > 0
        ? new TreeNode(bottomUpTree(depth - 1), bottomUpTree(depth - 1))
        : new TreeNode(null, null);
}


--- Optimized code ---
optimization_id = 4
source_position = 1482
kind = TURBOFAN_JS
name = bottomUpTree
compiler = turbofan
address = 0x1ae954e42d59

Instructions (size = 652)
0x1266c2400     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c2404     4  910003fd       mov fp, sp
0x1266c2408     8  a9be03ff       stp xzr, x0, [sp, #-32]!
0x1266c240c     c  a9016fe1       stp x1, cp, [sp, #16]
0x1266c2410    10  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2414    14  f8520342       ldur x2, [x26, #-224]
0x1266c2418    18  f9000bfb       str cp, [sp, #16]
0x1266c241c    1c  eb2263ff       cmp sp, x2
0x1266c2420    20  54000ce9       b.ls #+0x19c (addr 0x1266c25bc)
0x1266c2424    24  f94027e2       ldr x2, [sp, #72]
0x1266c2428    28  f240005f       tst x2, #0x1
0x1266c242c    2c  54001221       b.ne #+0x244 (addr 0x1266c2670)
0x1266c2430    30  f100005f       cmp x2, #0x0 (0)
0x1266c2434    34  5400038c       b.gt #+0x70 (addr 0x1266c24a4)
0x1266c2438    38  f85d0342       ldur x2, [x26, #-48]
0x1266c243c    3c  f85d8344       ldur x4, [x26, #-40]
0x1266c2440    40  9100a045       add x5, x2, #0x28 (40)
0x1266c2444    44  eb0400bf       cmp x5, x4
0x1266c2448    48  54000d22       b.hs #+0x1a4 (addr 0x1266c25ec)
0x1266c244c    4c  9100a044       add x4, x2, #0x28 (40)
0x1266c2450    50  f81d0344       stur x4, [x26, #-48]
0x1266c2454    54  91000442       add x2, x2, #0x1 (1)
0x1266c2458    58  f9413744       ldr x4, [x26, #616]
0x1266c245c    5c  f8007044       stur x4, [x2, #7]
0x1266c2460    60  f800f044       stur x4, [x2, #15]
0x1266c2464    64  f940db44       ldr x4, [x26, #432]
0x1266c2468    68  f8017044       stur x4, [x2, #23]
0x1266c246c    6c  58000de5       ldr x5, pc+444 (addr 0x00000001266c2628)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c2470    70  f81ff045       stur x5, [x2, #-1]
0x1266c2474    74  f801f044       stur x4, [x2, #31]
0x1266c2478    78  aa0203e0       mov x0, x2
0x1266c247c    7c  f85e83a3       ldur x3, [fp, #-24]
0x1266c2480    80  910003bf       mov sp, fp
0x1266c2484    84  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c2488    88  f100087f       cmp x3, #0x2 (2)
0x1266c248c    8c  5400004a       b.ge #+0x8 (addr 0x1266c2494)
0x1266c2490    90  d2800043       movz x3, #0x2
0x1266c2494    94  91000470       add x16, x3, #0x1 (1)
0x1266c2498    98  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c249c    9c  8b306fff       add sp, sp, x16, lsl #3
0x1266c24a0    a0  d65f03c0       ret
0x1266c24a4    a4  9360fc44       asr x4, x2, #32
0x1266c24a8    a8  71000484       subs w4, w4, #0x1 (1)
0x1266c24ac    ac  54000e46       b.vs #+0x1c8 (addr 0x1266c2674)
0x1266c24b0    b0  58000c01       ldr x1, pc+384 (addr 0x00000001266c2630)    ;; object: 0x2ff96b6425a1 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1266c24b4    b4  f842703b       ldur cp, [x1, #39]
0x1266c24b8    b8  d3607c84       lsl x4, x4, #32
0x1266c24bc    bc  d10043ff       sub sp, sp, #0x10 (16)
0x1266c24c0    c0  f940d343       ldr x3, [x26, #416]
0x1266c24c4    c4  a90013e3       stp x3, x4, [sp]
0x1266c24c8    c8  f9000fe4       str x4, [sp, #24]
0x1266c24cc    cc  d2800040       movz x0, #0x2
0x1266c24d0    d0  b8417024       ldur w4, [x1, #23]
0x1266c24d4    d4  d2a1cd55       movz x21, #0xe6a0000
0x1266c24d8    d8  f2c00035       movk x21, #0x1, lsl #32
0x1266c24dc    dc  d348fc94       lsr x20, x4, #8
0x1266c24e0    e0  8b1412b5       add x21, x21, x20, lsl #4
0x1266c24e4    e4  f94002a2       ldr x2, [x21]
0x1266c24e8    e8  794012b4       ldrh w20, [x21, #8]
0x1266c24ec    ec  f1000a9f       cmp x20, #0x2 (2)
0x1266c24f0    f0  5400004d       b.le #+0x8 (addr 0x1266c24f8)
0x1266c24f4    f4  d4200000       brk #0x0
0x1266c24f8    f8  d63f0040       blr x2
0x1266c24fc    fc  580009a1       ldr x1, pc+308 (addr 0x00000001266c2630)    ;; object: 0x2ff96b6425a1 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1266c2500   100  f842703b       ldur cp, [x1, #39]
0x1266c2504   104  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2508   108  f9400fe2       ldr x2, [sp, #24]
0x1266c250c   10c  f940d343       ldr x3, [x26, #416]
0x1266c2510   110  a9000be3       stp x3, x2, [sp]
0x1266c2514   114  f9000be0       str x0, [sp, #16]
0x1266c2518   118  d2800040       movz x0, #0x2
0x1266c251c   11c  b8417024       ldur w4, [x1, #23]
0x1266c2520   120  d2a1cd55       movz x21, #0xe6a0000
0x1266c2524   124  f2c00035       movk x21, #0x1, lsl #32
0x1266c2528   128  d348fc94       lsr x20, x4, #8
0x1266c252c   12c  8b1412b5       add x21, x21, x20, lsl #4
0x1266c2530   130  f94002a2       ldr x2, [x21]
0x1266c2534   134  794012b4       ldrh w20, [x21, #8]
0x1266c2538   138  f1000a9f       cmp x20, #0x2 (2)
0x1266c253c   13c  5400004d       b.le #+0x8 (addr 0x1266c2544)
0x1266c2540   140  d4200000       brk #0x0
0x1266c2544   144  d63f0040       blr x2
0x1266c2548   148  f85d0342       ldur x2, [x26, #-48]
0x1266c254c   14c  f85d8344       ldur x4, [x26, #-40]
0x1266c2550   150  9100a045       add x5, x2, #0x28 (40)
0x1266c2554   154  eb0400bf       cmp x5, x4
0x1266c2558   158  54000542       b.hs #+0xa8 (addr 0x1266c2600)
0x1266c255c   15c  9100a044       add x4, x2, #0x28 (40)
0x1266c2560   160  f81d0344       stur x4, [x26, #-48]
0x1266c2564   164  91000442       add x2, x2, #0x1 (1)
0x1266c2568   168  58000684       ldr x4, pc+208 (addr 0x00000001266c2638)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1266c256c   16c  f81ff044       stur x4, [x2, #-1]
0x1266c2570   170  f9413744       ldr x4, [x26, #616]
0x1266c2574   174  f8007044       stur x4, [x2, #7]
0x1266c2578   178  f800f044       stur x4, [x2, #15]
0x1266c257c   17c  f940d344       ldr x4, [x26, #416]
0x1266c2580   180  f8017044       stur x4, [x2, #23]
0x1266c2584   184  f801f044       stur x4, [x2, #31]
0x1266c2588   188  f94003e4       ldr x4, [sp]
0x1266c258c   18c  f240009f       tst x4, #0x1
0x1266c2590   190  54000740       b.eq #+0xe8 (addr 0x1266c2678)
0x1266c2594   194  58000565       ldr x5, pc+172 (addr 0x00000001266c2640)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1266c2598   198  f81ff045       stur x5, [x2, #-1]
0x1266c259c   19c  f8017044       stur x4, [x2, #23]
0x1266c25a0   1a0  f240001f       tst x0, #0x1
0x1266c25a4   1a4  540006c0       b.eq #+0xd8 (addr 0x1266c267c)
0x1266c25a8   1a8  58000404       ldr x4, pc+128 (addr 0x00000001266c2628)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c25ac   1ac  f81ff044       stur x4, [x2, #-1]
0x1266c25b0   1b0  f801f040       stur x0, [x2, #31]
0x1266c25b4   1b4  aa0203e0       mov x0, x2
0x1266c25b8   1b8  17ffffb1       b #-0x13c (addr 0x1266c247c)
0x1266c25bc   1bc  d2c01c02       movz x2, #0xe000000000
0x1266c25c0   1c0  d10043ff       sub sp, sp, #0x10 (16)
0x1266c25c4   1c4  f90007ff       str xzr, [sp, #8]
0x1266c25c8   1c8  f90003e2       str x2, [sp]
0x1266c25cc   1cc  d29d4f01       movz x1, #0xea78
0x1266c25d0   1d0  f2a06081       movk x1, #0x304, lsl #16
0x1266c25d4   1d4  f2c00021       movk x1, #0x1, lsl #32
0x1266c25d8   1d8  d2800020       movz x0, #0x1
0x1266c25dc   1dc  5800037b       ldr cp, pc+108 (addr 0x00000001266c2648)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c25e0   1e0  580003d0       ldr x16, pc+120 (addr 0x00000001266c2658)
0x1266c25e4   1e4  d63f0200       blr x16
0x1266c25e8   1e8  17ffff8f       b #-0x1c4 (addr 0x1266c2424)
0x1266c25ec   1ec  d2800501       movz x1, #0x28
0x1266c25f0   1f0  58000310       ldr x16, pc+96 (addr 0x00000001266c2650)
0x1266c25f4   1f4  d63f0200       blr x16
0x1266c25f8   1f8  d1000402       sub x2, x0, #0x1 (1)
0x1266c25fc   1fc  17ffff94       b #-0x1b0 (addr 0x1266c244c)
0x1266c2600   200  f90007e0       str x0, [sp, #8]
0x1266c2604   204  d2800501       movz x1, #0x28
0x1266c2608   208  58000250       ldr x16, pc+72 (addr 0x00000001266c2650)
0x1266c260c   20c  d63f0200       blr x16
0x1266c2610   210  d1000402       sub x2, x0, #0x1 (1)
0x1266c2614   214  f94007e0       ldr x0, [sp, #8]
0x1266c2618   218  17ffffd1       b #-0xbc (addr 0x1266c255c)
0x1266c261c   21c  d503201f       nop
0x1266c2620   220  580001ff       constant pool begin (num_const = 15)    ;; constant pool
0x1266c2624   224  d63f03e0       constant
0x1266c2628   228  b5f49259       constant
0x1266c262c   22c  00001dad       constant
0x1266c2630   230  6b6425a1       constant
0x1266c2634   234  00002ff9       constant
0x1266c2638   238  b5f49181       constant
0x1266c263c   23c  00001dad       constant
0x1266c2640   240  b5f49201       constant
0x1266c2644   244  00001dad       constant
0x1266c2648   248  24400109       constant
0x1266c264c   24c  00002347       constant
0x1266c2650   250  0360ace0       constant
0x1266c2654   254  00000001       constant
0x1266c2658   258  036a61e0       constant
0x1266c265c   25c  00000001       constant
0x1266c2660   260  f8558350       ldur x16, [x26, #-168]
0x1266c2664   264  d61f0200       br x16
0x1266c2668   268  f8560350       ldur x16, [x26, #-160]
0x1266c266c   26c  d61f0200       br x16
0x1266c2670   270  97fffffc       bl #-0x10 (addr 0x1266c2660)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x1266c2674   274  97fffffb       bl #-0x14 (addr 0x1266c2660)    ;; debug: deopt position, script offset '613'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 1
0x1266c2678   278  97fffffa       bl #-0x18 (addr 0x1266c2660)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 2
0x1266c267c   27c  97fffff9       bl #-0x1c (addr 0x1266c2660)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 3
0x1266c2680   280  97fffffa       bl #-0x18 (addr 0x1266c2668)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 4
0x1266c2684   284  97fffff9       bl #-0x1c (addr 0x1266c2668)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 5
0x1266c2688   288  97fffff8       bl #-0x20 (addr 0x1266c2668)    ;; debug: deopt position, script offset '5ca'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 6

Source positions:
 pc offset  position
        14      1482
        24      1509
        38      1596
        64      1250
        6c      1277
        78      1621
        a4      1555
        b0      1536
        fc      1561
       148      1523
       188      1250
       1a0      1277
       1b4      1621
       1bc      1482
       1ec      1596
       200      1523

Inlined functions (count = 1)
 0x1dadb5f429d9 <SharedFunctionInfo TreeNode>

Deoptimization Input Data (deopt points = 7)
 index  bytecode-offset    pc
     0                1    NA 
     1                1    NA 
     2                2    NA 
     3                8    NA 
     4               20    fc 
     5               34   148 
     6               -1   1e8 

Safepoints (stack slots = 8, entries = 5, byte size = 42)
0x1266c24fc     fc  slots (sp->fp): 00100000  deopt      4 trampoline:    280
0x1266c2548    148  slots (sp->fp): 10100000  deopt      5 trampoline:    284
0x1266c25e8    1e8  slots (sp->fp): 00100000  deopt      6 trampoline:    288
0x1266c25f8    1f8  slots (sp->fp): 00000000
0x1266c2610    210  slots (sp->fp): 11100000

RelocInfo (size = 170)
0x1266c246c  full embedded object  (0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>)
0x1266c24b0  full embedded object  (0x2ff96b6425a1 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>)
0x1266c2568  full embedded object  (0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>)
0x1266c2594  full embedded object  (0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>)
0x1266c25dc  full embedded object  (0x234724400109 <NativeContext[302]>)
0x1266c2620  constant pool (size 64)
0x1266c2670  deopt script offset  (1509)
0x1266c2670  deopt inlining id  (-1)
0x1266c2670  deopt reason  (not a Smi)
0x1266c2670  deopt index
0x1266c2674  deopt script offset  (1555)
0x1266c2674  deopt inlining id  (-1)
0x1266c2674  deopt reason  (overflow)
0x1266c2674  deopt index
0x1266c2678  deopt script offset  (1250)
0x1266c2678  deopt inlining id  (0)
0x1266c2678  deopt reason  (Smi)
0x1266c2678  deopt index
0x1266c267c  deopt script offset  (1277)
0x1266c267c  deopt inlining id  (0)
0x1266c267c  deopt reason  (Smi)
0x1266c267c  deopt index
0x1266c2680  deopt script offset  (1536)
0x1266c2680  deopt inlining id  (-1)
0x1266c2680  deopt reason  ((unknown))
0x1266c2680  deopt index
0x1266c2684  deopt script offset  (1561)
0x1266c2684  deopt inlining id  (-1)
0x1266c2684  deopt reason  ((unknown))
0x1266c2684  deopt index
0x1266c2688  deopt script offset  (1482)
0x1266c2688  deopt inlining id  (-1)
0x1266c2688  deopt reason  ((unknown))
0x1266c2688  deopt index

--- End code ---
[completed compiling 0x2ff96b6425a1 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> (target TURBOFAN_JS) - took 0.000, 0.916, 0.500 ms]
[completed optimizing 0x2ff96b6425a1 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)> (target TURBOFAN_JS)]
[marking 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> for optimization to MAGLEV, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> (target MAGLEV), mode: ConcurrencyMode::kSynchronous]
0x1ae954e43171: [Code]
 - map: 0x1d42df7817e9 <Map[88](CODE_TYPE)>
 - kind: MAGLEV
 - deoptimization_data_or_interpreter_data: 0x1ae954e42e79 <ProtectedFixedArray[36]>
 - position_table: 0x1bc26a780011 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - parameter_count: 2
 - instruction_stream: 0x0001266c26c1 <InstructionStream MAGLEV>
 - instruction_start: 0x1266c26e0
 - is_turbofanned: 0
 - stack_slots: 8
 - marked_for_deoptimization: 0
 - embedded_objects_cleared: 0
 - can_have_weak_objects: 0
 - instruction_size: 728
 - metadata_size: 60
 - inlined_bytecode_size: 0
 - osr_offset: -1
 - handler_table_offset: 60
 - unwinding_info_offset: 60
 - code_comments_offset: 60
 - instruction_stream.relocation_info: 0x1ae954e430a1 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - instruction_stream.body_size: 788

--- Disassembly: ---
kind = MAGLEV
name = itemCheck
compiler = maglev
address = 0x1ae954e43171

Instructions (size = 728)
0x1266c26e0     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c26e4     4  910003fd       mov fp, sp
0x1266c26e8     8  a9bf6fe1       stp x1, cp, [sp, #-16]!
0x1266c26ec     c  a9bf03ff       stp xzr, x0, [sp, #-16]!
0x1266c26f0    10  d10043ff       sub sp, sp, #0x10 (16)
0x1266c26f4    14  d106c3f0       sub x16, sp, #0x1b0 (432)
0x1266c26f8    18  f8520351       ldur x17, [x26, #-224]
0x1266c26fc    1c  eb11021f       cmp x16, x17
0x1266c2700    20  54000b23       b.lo #+0x164 (addr 0x1266c2864)
0x1266c2704    24  f9400fa0       ldr x0, [fp, #24]
0x1266c2708    28  36001480       tbz w0, #0, #+0x290 (addr 0x1266c2998)
0x1266c270c    2c  f85ff010       ldur x16, [x0, #-1]
0x1266c2710    30  58001191       ldr x17, pc+560 (addr 0x00000001266c2940)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c2714    34  eb11021f       cmp x16, x17
0x1266c2718    38  54001401       b.ne #+0x280 (addr 0x1266c2998)
0x1266c271c    3c  f8417001       ldur x1, [x0, #23]
0x1266c2720    40  f940db50       ldr x16, [x26, #432]
0x1266c2724    44  eb10003f       cmp x1, x16
0x1266c2728    48  540000c0       b.eq #+0x18 (addr 0x1266c2740)
0x1266c272c    4c  f841f002       ldur x2, [x0, #31]
0x1266c2730    50  f81e03a2       stur x2, [fp, #-32]
0x1266c2734    54  f940db50       ldr x16, [x26, #432]
0x1266c2738    58  eb10005f       cmp x2, x16
0x1266c273c    5c  54000241       b.ne #+0x48 (addr 0x1266c2784)
0x1266c2740    60  58001042       ldr x2, pc+520 (addr 0x00000001266c2948)    ;; object: 0x1dadb5f42be9 <FeedbackCell[one closure]>
0x1266c2744    64  b8413043       ldur w3, [x2, #19]
0x1266c2748    68  71003863       subs w3, w3, #0xe (14)
0x1266c274c    6c  b8013043       stur w3, [x2, #19]
0x1266c2750    70  5400094b       b.lt #+0x128 (addr 0x1266c2878)
0x1266c2754    74  d2c00020       movz x0, #0x100000000
0x1266c2758    78  f85e83a9       ldur x9, [fp, #-24]
0x1266c275c    7c  d280004a       movz x10, #0x2
0x1266c2760    80  eb09015f       cmp x10, x9
0x1266c2764    84  5400004a       b.ge #+0x8 (addr 0x1266c276c)
0x1266c2768    88  aa0903ea       mov x10, x9
0x1266c276c    8c  910003bf       mov sp, fp
0x1266c2770    90  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c2774    94  91000550       add x16, x10, #0x1 (1)
0x1266c2778    98  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c277c    9c  8b306fff       add sp, sp, x16, lsl #3
0x1266c2780    a0  d65f03c0       ret
0x1266c2784    a4  aa0103e3       mov x3, x1
0x1266c2788    a8  58000e41       ldr x1, pc+456 (addr 0x00000001266c2950)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1266c278c    ac  58000e7b       ldr cp, pc+460 (addr 0x00000001266c2958)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x1266c2790    b0  aa0303e4       mov x4, x3
0x1266c2794    b4  f940d343       ldr x3, [x26, #416]
0x1266c2798    b8  a9bf13e3       stp x3, x4, [sp, #-16]!
0x1266c279c    bc  52800040       movz w0, #0x2
0x1266c27a0    c0  18000e44       ldr w4, pc+456 (addr 0x00000001266c2968)    ;; js dispatch handle:0x2c4600 Builtin::InterpreterEntryTrampoline
0x1266c27a4    c4  d2a1cd55       movz x21, #0xe6a0000
0x1266c27a8    c8  f2c00035       movk x21, #0x1, lsl #32
0x1266c27ac    cc  d2988c10       movz x16, #0xc460
0x1266c27b0    d0  f2a00050       movk x16, #0x2, lsl #16
0x1266c27b4    d4  f8706aa2       ldr x2, [x21, x16]
0x1266c27b8    d8  d63f0040       blr x2
0x1266c27bc    dc  aa0003e1       mov x1, x0
0x1266c27c0    e0  37000ee0       tbnz w0, #0, #+0x1dc (addr 0x1266c299c)
0x1266c27c4    e4  d360fc00       lsr x0, x0, #32
0x1266c27c8    e8  31000402       adds w2, w0, #0x1 (1)
0x1266c27cc    ec  54000ea6       b.vs #+0x1d4 (addr 0x1266c29a0)
0x1266c27d0    f0  f81d83a2       stur x2, [fp, #-40]
0x1266c27d4    f4  58000be1       ldr x1, pc+380 (addr 0x00000001266c2950)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1266c27d8    f8  58000c1b       ldr cp, pc+384 (addr 0x00000001266c2958)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x1266c27dc    fc  f940d343       ldr x3, [x26, #416]
0x1266c27e0   100  f85e03b0       ldur x16, [fp, #-32]
0x1266c27e4   104  a9bf43e3       stp x3, x16, [sp, #-16]!
0x1266c27e8   108  52800040       movz w0, #0x2
0x1266c27ec   10c  18000be4       ldr w4, pc+380 (addr 0x00000001266c2968)
0x1266c27f0   110  d2a1cd55       movz x21, #0xe6a0000
0x1266c27f4   114  f2c00035       movk x21, #0x1, lsl #32
0x1266c27f8   118  d2988c10       movz x16, #0xc460
0x1266c27fc   11c  f2a00050       movk x16, #0x2, lsl #16
0x1266c2800   120  f8706aa2       ldr x2, [x21, x16]
0x1266c2804   124  d63f0040       blr x2
0x1266c2808   128  aa0003e1       mov x1, x0
0x1266c280c   12c  37000cc0       tbnz w0, #0, #+0x198 (addr 0x1266c29a4)
0x1266c2810   130  d360fc00       lsr x0, x0, #32
0x1266c2814   134  f85d83a2       ldur x2, [fp, #-40]
0x1266c2818   138  2b000043       adds w3, w2, w0
0x1266c281c   13c  54000c66       b.vs #+0x18c (addr 0x1266c29a8)
0x1266c2820   140  58000940       ldr x0, pc+296 (addr 0x00000001266c2948)    ;; object: 0x1dadb5f42be9 <FeedbackCell[one closure]>
0x1266c2824   144  b8413001       ldur w1, [x0, #19]
0x1266c2828   148  7100c421       subs w1, w1, #0x31 (49)
0x1266c282c   14c  b8013001       stur w1, [x0, #19]
0x1266c2830   150  5400042b       b.lt #+0x84 (addr 0x1266c28b4)
0x1266c2834   154  d3607c60       lsl x0, x3, #32
0x1266c2838   158  f85e83a9       ldur x9, [fp, #-24]
0x1266c283c   15c  d280004a       movz x10, #0x2
0x1266c2840   160  eb09015f       cmp x10, x9
0x1266c2844   164  5400004a       b.ge #+0x8 (addr 0x1266c284c)
0x1266c2848   168  aa0903ea       mov x10, x9
0x1266c284c   16c  910003bf       mov sp, fp
0x1266c2850   170  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c2854   174  91000550       add x16, x10, #0x1 (1)
0x1266c2858   178  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c285c   17c  8b306fff       add sp, sp, x16, lsl #3
0x1266c2860   180  d65f03c0       ret
0x1266c2864   184  d2c03600       movz x0, #0x1b000000000
0x1266c2868   188  58000850       ldr x16, pc+264 (addr 0x00000001266c2970)
0x1266c286c   18c  d63f0200       blr x16
0x1266c2870   190  17ffffa5       b #-0x16c (addr 0x1266c2704)
0x1266c2874   194  d4200000       brk #0x0
0x1266c2878   198  a9bf03e1       stp x1, x0, [sp, #-16]!
0x1266c287c   19c  a9bf0bff       stp xzr, x2, [sp, #-16]!
0x1266c2880   1a0  f85f03a3       ldur x3, [fp, #-16]
0x1266c2884   1a4  a9bf7fe3       stp x3, xzr, [sp, #-16]!
0x1266c2888   1a8  580006db       ldr cp, pc+216 (addr 0x00000001266c2960)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c288c   1ac  d2800020       movz x0, #0x1
0x1266c2890   1b0  d29d9b01       movz x1, #0xecd8
0x1266c2894   1b4  f2a06081       movk x1, #0x304, lsl #16
0x1266c2898   1b8  f2c00021       movk x1, #0x1, lsl #32
0x1266c289c   1bc  58000730       ldr x16, pc+228 (addr 0x00000001266c2980)
0x1266c28a0   1c0  d63f0200       blr x16
0x1266c28a4   1c4  a8c10bff       ldp xzr, x2, [sp], #16
0x1266c28a8   1c8  a8c103e1       ldp x1, x0, [sp], #16
0x1266c28ac   1cc  17ffffaa       b #-0x158 (addr 0x1266c2754)
0x1266c28b0   1d0  d4200000       brk #0x0
0x1266c28b4   1d4  a9bf0fff       stp xzr, x3, [sp, #-16]!
0x1266c28b8   1d8  f85f03a1       ldur x1, [fp, #-16]
0x1266c28bc   1dc  a9bf7fe1       stp x1, xzr, [sp, #-16]!
0x1266c28c0   1e0  5800051b       ldr cp, pc+160 (addr 0x00000001266c2960)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c28c4   1e4  d2800020       movz x0, #0x1
0x1266c28c8   1e8  d29d9b01       movz x1, #0xecd8
0x1266c28cc   1ec  f2a06081       movk x1, #0x304, lsl #16
0x1266c28d0   1f0  f2c00021       movk x1, #0x1, lsl #32
0x1266c28d4   1f4  58000570       ldr x16, pc+172 (addr 0x00000001266c2980)
0x1266c28d8   1f8  d63f0200       blr x16
0x1266c28dc   1fc  a8c10fff       ldp xzr, x3, [sp], #16
0x1266c28e0   200  17ffffd5       b #-0xac (addr 0x1266c2834)
0x1266c28e4   204  d4200000       brk #0x0
0x1266c28e8   208  1e62007e       scvtf d30, w3
0x1266c28ec   20c  f85d0340       ldur x0, [x26, #-48]
0x1266c28f0   210  91004000       add x0, x0, #0x10 (16)
0x1266c28f4   214  f85d8350       ldur x16, [x26, #-40]
0x1266c28f8   218  eb10001f       cmp x0, x16
0x1266c28fc   21c  54000102       b.hs #+0x20 (addr 0x1266c291c)
0x1266c2900   220  f81d0340       stur x0, [x26, #-48]
0x1266c2904   224  d1003c00       sub x0, x0, #0xf (15)
0x1266c2908   228  f9412750       ldr x16, [x26, #584]
0x1266c290c   22c  f81ff010       stur x16, [x0, #-1]
0x1266c2910   230  fc00701e       stur d30, [x0, #7]
0x1266c2914   234  17ffffc9       b #-0xdc (addr 0x1266c2838)
0x1266c2918   238  d4200000       brk #0x0
0x1266c291c   23c  6dbf7bef       stp d15, d30, [sp, #-16]!
0x1266c2920   240  52800201       movz w1, #0x10
0x1266c2924   244  580002b0       ldr x16, pc+84 (addr 0x00000001266c2978)
0x1266c2928   248  d63f0200       blr x16
0x1266c292c   24c  6cc17bef       ldp d15, d30, [sp], #16
0x1266c2930   250  17fffff6       b #-0x28 (addr 0x1266c2908)
0x1266c2934   254  d4200000       brk #0x0
0x1266c2938   258  5800027f       constant pool begin (num_const = 19)    ;; constant pool
0x1266c293c   25c  d63f03e0       constant
0x1266c2940   260  b5f49259       constant
0x1266c2944   264  00001dad       constant
0x1266c2948   268  b5f42be9       constant
0x1266c294c   26c  00001dad       constant
0x1266c2950   270  b5f4b951       constant
0x1266c2954   274  00001dad       constant
0x1266c2958   278  b5f4b861       constant
0x1266c295c   27c  00001dad       constant
0x1266c2960   280  24400109       constant
0x1266c2964   284  00002347       constant
0x1266c2968   288  002c4600       constant
0x1266c296c   28c  00000000       constant
0x1266c2970   290  03609ba0       constant
0x1266c2974   294  00000001       constant
0x1266c2978   298  0360ace0       constant
0x1266c297c   29c  00000001       constant
0x1266c2980   2a0  036a61e0       constant
0x1266c2984   2a4  00000001       constant
0x1266c2988   2a8  f8558350       ldur x16, [x26, #-168]
0x1266c298c   2ac  d61f0200       br x16
0x1266c2990   2b0  f8560350       ldur x16, [x26, #-160]
0x1266c2994   2b4  d61f0200       br x16
0x1266c2998   2b8  97fffffc       bl #-0x10 (addr 0x1266c2988)    ;; debug: deopt position, script offset '536'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 0
0x1266c299c   2bc  97fffffb       bl #-0x14 (addr 0x1266c2988)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 1
0x1266c29a0   2c0  97fffffa       bl #-0x18 (addr 0x1266c2988)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 2
0x1266c29a4   2c4  97fffff9       bl #-0x1c (addr 0x1266c2988)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 3
0x1266c29a8   2c8  97fffff8       bl #-0x20 (addr 0x1266c2988)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 4
0x1266c29ac   2cc  97fffff9       bl #-0x1c (addr 0x1266c2990)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 5
0x1266c29b0   2d0  97fffff8       bl #-0x20 (addr 0x1266c2990)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 6
0x1266c29b4   2d4  97fffff7       bl #-0x24 (addr 0x1266c2990)    ;; debug: deopt position, script offset '520'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 7

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 8)
 index  bytecode-offset    pc
     0                0   2b8 
     1               30   2bc 
     2               30   2c0 
     3               46   2c4 
     4               46   2c8 
     5               26   2cc 
     6               42   2d0 
     7               -1   2d4 

Safepoints (stack slots = 8, entries = 6, byte size = 58, tagged slots = 1)
0x1266c27bc     dc  num extra spill slots: 0  deopt      5 trampoline:    2cc
0x1266c2808    128  num extra spill slots: 0  deopt      6 trampoline:    2d0
0x1266c2870    190  num extra spill slots: 0  deopt      7 trampoline:    2d4
0x1266c28a4    1c4  num extra spill slots: 4  registers: 111
0x1266c28dc    1fc  num extra spill slots: 2
0x1266c292c    24c  num extra spill slots: 2

RelocInfo (size = 189)
0x1266c2710  full embedded object  (0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>)
0x1266c2740  full embedded object  (0x1dadb5f42be9 <FeedbackCell[one closure]>)
0x1266c2788  full embedded object  (0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>)
0x1266c278c  full embedded object  (0x1dadb5f4b861 <FunctionContext[7]>)
0x1266c27a0  js dispatch handle (BUILTIN InterpreterEntryTrampoline)  (2901504)
0x1266c2888  full embedded object  (0x234724400109 <NativeContext[302]>)
0x1266c2938  constant pool (size 80)
0x1266c2998  deopt script offset  (1334)
0x1266c2998  deopt inlining id  (-1)
0x1266c2998  deopt reason  (wrong map)
0x1266c2998  deopt index
0x1266c299c  deopt script offset  (1411)
0x1266c299c  deopt inlining id  (-1)
0x1266c299c  deopt reason  (not a Smi)
0x1266c299c  deopt index
0x1266c29a0  deopt script offset  (1411)
0x1266c29a0  deopt inlining id  (-1)
0x1266c29a0  deopt reason  (overflow)
0x1266c29a0  deopt index
0x1266c29a4  deopt script offset  (1434)
0x1266c29a4  deopt inlining id  (-1)
0x1266c29a4  deopt reason  (not a Smi)
0x1266c29a4  deopt index
0x1266c29a8  deopt script offset  (1434)
0x1266c29a8  deopt inlining id  (-1)
0x1266c29a8  deopt reason  (overflow)
0x1266c29a8  deopt index
0x1266c29ac  deopt script offset  (1413)
0x1266c29ac  deopt inlining id  (-1)
0x1266c29ac  deopt reason  ((unknown))
0x1266c29ac  deopt index
0x1266c29b0  deopt script offset  (1436)
0x1266c29b0  deopt inlining id  (-1)
0x1266c29b0  deopt reason  ((unknown))
0x1266c29b0  deopt index
0x1266c29b4  deopt script offset  (1312)
0x1266c29b4  deopt inlining id  (-1)
0x1266c29b4  deopt reason  ((unknown))
0x1266c29b4  deopt index

[completed compiling 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> (target MAGLEV) - took 0.000, 0.334, 0.541 ms]
[marking 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> for optimization to TURBOFAN_JS, ConcurrencyMode::kConcurrent, reason: hot and stable]
[compiling method 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> (target TURBOFAN_JS), mode: ConcurrencyMode::kConcurrent]
--- Raw source ---
(node) {
    if (node.left === null || node.right === null) {
        return 1;
    }
    return 1 + itemCheck(node.left) + itemCheck(node.right);
}


--- Optimized code ---
optimization_id = 7
source_position = 1312
kind = TURBOFAN_JS
name = itemCheck
compiler = turbofan
address = 0x1ae954e43531

Instructions (size = 512)
0x1266c2a20     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x1266c2a24     4  910003fd       mov fp, sp
0x1266c2a28     8  a9be03ff       stp xzr, x0, [sp, #-32]!
0x1266c2a2c     c  a9016fe1       stp x1, cp, [sp, #16]
0x1266c2a30    10  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2a34    14  f8520342       ldur x2, [x26, #-224]
0x1266c2a38    18  f9000bfb       str cp, [sp, #16]
0x1266c2a3c    1c  eb2263ff       cmp sp, x2
0x1266c2a40    20  54000a69       b.ls #+0x14c (addr 0x1266c2b8c)
0x1266c2a44    24  f94027e2       ldr x2, [sp, #72]
0x1266c2a48    28  f240005f       tst x2, #0x1
0x1266c2a4c    2c  54000d60       b.eq #+0x1ac (addr 0x1266c2bf8)
0x1266c2a50    30  f85ff044       ldur x4, [x2, #-1]
0x1266c2a54    34  58000ba5       ldr x5, pc+372 (addr 0x00000001266c2bc8)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c2a58    38  eb05009f       cmp x4, x5
0x1266c2a5c    3c  54000d01       b.ne #+0x1a0 (addr 0x1266c2bfc)
0x1266c2a60    40  f8417044       ldur x4, [x2, #23]
0x1266c2a64    44  f940db46       ldr x6, [x26, #432]
0x1266c2a68    48  eb06009f       cmp x4, x6
0x1266c2a6c    4c  540008c0       b.eq #+0x118 (addr 0x1266c2b84)
0x1266c2a70    50  f841f047       ldur x7, [x2, #31]
0x1266c2a74    54  f90007e7       str x7, [sp, #8]
0x1266c2a78    58  eb0600ff       cmp x7, x6
0x1266c2a7c    5c  54000800       b.eq #+0x100 (addr 0x1266c2b7c)
0x1266c2a80    60  58000a81       ldr x1, pc+336 (addr 0x00000001266c2bd0)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1266c2a84    64  f842703b       ldur cp, [x1, #39]
0x1266c2a88    68  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2a8c    6c  f940d343       ldr x3, [x26, #416]
0x1266c2a90    70  a90013e3       stp x3, x4, [sp]
0x1266c2a94    74  d2800040       movz x0, #0x2
0x1266c2a98    78  b8417024       ldur w4, [x1, #23]
0x1266c2a9c    7c  d2a1cd55       movz x21, #0xe6a0000
0x1266c2aa0    80  f2c00035       movk x21, #0x1, lsl #32
0x1266c2aa4    84  d348fc94       lsr x20, x4, #8
0x1266c2aa8    88  8b1412b5       add x21, x21, x20, lsl #4
0x1266c2aac    8c  f94002a2       ldr x2, [x21]
0x1266c2ab0    90  794012b4       ldrh w20, [x21, #8]
0x1266c2ab4    94  f1000a9f       cmp x20, #0x2 (2)
0x1266c2ab8    98  5400004d       b.le #+0x8 (addr 0x1266c2ac0)
0x1266c2abc    9c  d4200000       brk #0x0
0x1266c2ac0    a0  d63f0040       blr x2
0x1266c2ac4    a4  f240001f       tst x0, #0x1
0x1266c2ac8    a8  540009c1       b.ne #+0x138 (addr 0x1266c2c00)
0x1266c2acc    ac  9360fc02       asr x2, x0, #32
0x1266c2ad0    b0  31000442       adds w2, w2, #0x1 (1)
0x1266c2ad4    b4  54000986       b.vs #+0x130 (addr 0x1266c2c04)
0x1266c2ad8    b8  f94027e4       ldr x4, [sp, #72]
0x1266c2adc    bc  f85ff085       ldur x5, [x4, #-1]
0x1266c2ae0    c0  58000746       ldr x6, pc+232 (addr 0x00000001266c2bc8)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1266c2ae4    c4  eb0600bf       cmp x5, x6
0x1266c2ae8    c8  54000901       b.ne #+0x120 (addr 0x1266c2c08)
0x1266c2aec    cc  58000721       ldr x1, pc+228 (addr 0x00000001266c2bd0)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1266c2af0    d0  f842703b       ldur cp, [x1, #39]
0x1266c2af4    d4  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2af8    d8  f9400fe5       ldr x5, [sp, #24]
0x1266c2afc    dc  f940d343       ldr x3, [x26, #416]
0x1266c2b00    e0  a90017e3       stp x3, x5, [sp]
0x1266c2b04    e4  f9000be2       str x2, [sp, #16]
0x1266c2b08    e8  d2800040       movz x0, #0x2
0x1266c2b0c    ec  b8417024       ldur w4, [x1, #23]
0x1266c2b10    f0  d2a1cd55       movz x21, #0xe6a0000
0x1266c2b14    f4  f2c00035       movk x21, #0x1, lsl #32
0x1266c2b18    f8  d348fc94       lsr x20, x4, #8
0x1266c2b1c    fc  8b1412b5       add x21, x21, x20, lsl #4
0x1266c2b20   100  f94002a2       ldr x2, [x21]
0x1266c2b24   104  794012b4       ldrh w20, [x21, #8]
0x1266c2b28   108  f1000a9f       cmp x20, #0x2 (2)
0x1266c2b2c   10c  5400004d       b.le #+0x8 (addr 0x1266c2b34)
0x1266c2b30   110  d4200000       brk #0x0
0x1266c2b34   114  d63f0040       blr x2
0x1266c2b38   118  f240001f       tst x0, #0x1
0x1266c2b3c   11c  54000681       b.ne #+0xd0 (addr 0x1266c2c0c)
0x1266c2b40   120  9360fc02       asr x2, x0, #32
0x1266c2b44   124  f94003e4       ldr x4, [sp]
0x1266c2b48   128  2b020082       adds w2, w4, w2
0x1266c2b4c   12c  54000626       b.vs #+0xc4 (addr 0x1266c2c10)
0x1266c2b50   130  d3607c40       lsl x0, x2, #32
0x1266c2b54   134  f85e83a3       ldur x3, [fp, #-24]
0x1266c2b58   138  910003bf       mov sp, fp
0x1266c2b5c   13c  a8c17bfd       ldp fp, lr, [sp], #16
0x1266c2b60   140  f100087f       cmp x3, #0x2 (2)
0x1266c2b64   144  5400004a       b.ge #+0x8 (addr 0x1266c2b6c)
0x1266c2b68   148  d2800043       movz x3, #0x2
0x1266c2b6c   14c  91000470       add x16, x3, #0x1 (1)
0x1266c2b70   150  927ffa10       and x16, x16, #0xfffffffffffffffe
0x1266c2b74   154  8b306fff       add sp, sp, x16, lsl #3
0x1266c2b78   158  d65f03c0       ret
0x1266c2b7c   15c  d2c00020       movz x0, #0x100000000
0x1266c2b80   160  17fffff5       b #-0x2c (addr 0x1266c2b54)
0x1266c2b84   164  d2c00020       movz x0, #0x100000000
0x1266c2b88   168  17fffff3       b #-0x34 (addr 0x1266c2b54)
0x1266c2b8c   16c  d2c00702       movz x2, #0x3800000000
0x1266c2b90   170  d10043ff       sub sp, sp, #0x10 (16)
0x1266c2b94   174  f90007ff       str xzr, [sp, #8]
0x1266c2b98   178  f90003e2       str x2, [sp]
0x1266c2b9c   17c  d29d4f01       movz x1, #0xea78
0x1266c2ba0   180  f2a06081       movk x1, #0x304, lsl #16
0x1266c2ba4   184  f2c00021       movk x1, #0x1, lsl #32
0x1266c2ba8   188  d2800020       movz x0, #0x1
0x1266c2bac   18c  5800017b       ldr cp, pc+44 (addr 0x00000001266c2bd8)    ;; object: 0x234724400109 <NativeContext[302]>
0x1266c2bb0   190  58000190       ldr x16, pc+48 (addr 0x00000001266c2be0)
0x1266c2bb4   194  d63f0200       blr x16
0x1266c2bb8   198  17ffffa3       b #-0x174 (addr 0x1266c2a44)
0x1266c2bbc   19c  d503201f       nop
0x1266c2bc0   1a0  5800013f       constant pool begin (num_const = 9)    ;; constant pool
0x1266c2bc4   1a4  d63f03e0       constant
0x1266c2bc8   1a8  b5f49259       constant
0x1266c2bcc   1ac  00001dad       constant
0x1266c2bd0   1b0  b5f4b951       constant
0x1266c2bd4   1b4  00001dad       constant
0x1266c2bd8   1b8  24400109       constant
0x1266c2bdc   1bc  00002347       constant
0x1266c2be0   1c0  036a61e0       constant
0x1266c2be4   1c4  00000001       constant
0x1266c2be8   1c8  f8558350       ldur x16, [x26, #-168]
0x1266c2bec   1cc  d61f0200       br x16
0x1266c2bf0   1d0  f8560350       ldur x16, [x26, #-160]
0x1266c2bf4   1d4  d61f0200       br x16
0x1266c2bf8   1d8  97fffffc       bl #-0x10 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '536'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 0
0x1266c2bfc   1dc  97fffffb       bl #-0x14 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '536'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 1
0x1266c2c00   1e0  97fffffa       bl #-0x18 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 2
0x1266c2c04   1e4  97fffff9       bl #-0x1c (addr 0x1266c2be8)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 3
0x1266c2c08   1e8  97fffff8       bl #-0x20 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '5ab'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 4
0x1266c2c0c   1ec  97fffff7       bl #-0x24 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 5
0x1266c2c10   1f0  97fffff6       bl #-0x28 (addr 0x1266c2be8)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 6
0x1266c2c14   1f4  97fffff7       bl #-0x24 (addr 0x1266c2bf0)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 7
0x1266c2c18   1f8  97fffff6       bl #-0x28 (addr 0x1266c2bf0)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 8
0x1266c2c1c   1fc  97fffff5       bl #-0x2c (addr 0x1266c2bf0)    ;; debug: deopt position, script offset '520'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 9

Source positions:
 pc offset  position
        14      1312
        24      1334
        50      1356
        60      1413
        a4      1411
        b8      1451
        cc      1436
       118      1434
       130      1458
       15c      1391
       16c      1312

Inlined functions (count = 0)

Deoptimization Input Data (deopt points = 10)
 index  bytecode-offset    pc
     0                0    NA 
     1                0    NA 
     2               30    NA 
     3               30    NA 
     4               30    NA 
     5               46    NA 
     6               46    NA 
     7               26    a4 
     8               42   118 
     9               -1   198 

Safepoints (stack slots = 8, entries = 3, byte size = 30)
0x1266c2ac4     a4  slots (sp->fp): 01100000  deopt      7 trampoline:    1f4
0x1266c2b38    118  slots (sp->fp): 00100000  deopt      8 trampoline:    1f8
0x1266c2bb8    198  slots (sp->fp): 00100000  deopt      9 trampoline:    1fc

RelocInfo (size = dd)
0x1266c2a54  full embedded object  (0x1dadb5f49259 <Map[28](HOLEY_ELEMENTS)>)
0x1266c2a80  full embedded object  (0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>)
0x1266c2bac  full embedded object  (0x234724400109 <NativeContext[12e]>)
0x1266c2bc0  constant pool (size 28)
0x1266c2bf8  deopt script offset  (536)
0x1266c2bf8  deopt inlining id  (ffffffffffffffff)
0x1266c2bf8  deopt reason  (Smi)
0x1266c2bf8  deopt index
0x1266c2bfc  deopt script offset  (536)
0x1266c2bfc  deopt inlining id  (ffffffffffffffff)
0x1266c2bfc  deopt reason  (wrong map)
0x1266c2bfc  deopt index
0x1266c2c00  deopt script offset  (583)
0x1266c2c00  deopt inlining id  (ffffffffffffffff)
0x1266c2c00  deopt reason  (not a Smi)
0x1266c2c00  deopt index
0x1266c2c04  deopt script offset  (583)
0x1266c2c04  deopt inlining id  (ffffffffffffffff)
0x1266c2c04  deopt reason  (overflow)
0x1266c2c04  deopt index
0x1266c2c08  deopt script offset  (5ab)
0x1266c2c08  deopt inlining id  (ffffffffffffffff)
0x1266c2c08  deopt reason  (wrong map)
0x1266c2c08  deopt index
0x1266c2c0c  deopt script offset  (59a)
0x1266c2c0c  deopt inlining id  (ffffffffffffffff)
0x1266c2c0c  deopt reason  (not a Smi)
0x1266c2c0c  deopt index
0x1266c2c10  deopt script offset  (59a)
0x1266c2c10  deopt inlining id  (ffffffffffffffff)
0x1266c2c10  deopt reason  (overflow)
0x1266c2c10  deopt index
0x1266c2c14  deopt script offset  (585)
0x1266c2c14  deopt inlining id  (ffffffffffffffff)
0x1266c2c14  deopt reason  ((unknown))
0x1266c2c14  deopt index
0x1266c2c18  deopt script offset  (59c)
0x1266c2c18  deopt inlining id  (ffffffffffffffff)
0x1266c2c18  deopt reason  ((unknown))
0x1266c2c18  deopt index
0x1266c2c1c  deopt script offset  (520)
0x1266c2c1c  deopt inlining id  (ffffffffffffffff)
0x1266c2c1c  deopt reason  ((unknown))
0x1266c2c1c  deopt index

--- End code ---
[completed compiling 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> (target TURBOFAN_JS) - took 0.000, 0.375, 0.459 ms]
[completed optimizing 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)> (target TURBOFAN_JS)]
[marking 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> for optimization to MAGLEV, ConcurrencyMode::kConcurrent, reason: hot and stable]
[OSR - setting osr urgency. function: work, old urgency: 0, new urgency: 1]
[OSR - compilation started. function: work, osr offset: 38, mode: ConcurrencyMode::kConcurrent]
[compiling method 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> (target MAGLEV) OSR, mode: ConcurrencyMode::kSynchronous]
0x1ae954e55b41: [Code]
 - map: 0x1d42df7817e9 <Map[88](CODE_TYPE)>
 - kind: MAGLEV
 - deoptimization_data_or_interpreter_data: 0x1ae954e54891 <ProtectedFixedArray[186]>
 - position_table: 0x1bc26a780011 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - parameter_count: 3
 - instruction_stream: 0x000126747ba1 <InstructionStream MAGLEV>
 - instruction_start: 0x126747bc0
 - is_turbofanned: 0
 - stack_slots: 22
 - marked_for_deoptimization: 0
 - embedded_objects_cleared: 0
 - can_have_weak_objects: 0
 - instruction_size: 4280
 - metadata_size: 224
 - inlined_bytecode_size: 230
 - osr_offset: 38
 - handler_table_offset: 224
 - unwinding_info_offset: 224
 - code_comments_offset: 224
 - instruction_stream.relocation_info: 0x1ae954e55641 <Other heap object (TRUSTED_BYTE_ARRAY_TYPE)>
 - instruction_stream.body_size: 4504

--- Disassembly: ---
kind = MAGLEV
name = work
compiler = maglev
address = 0x1ae954e55b41

Instructions (size = 4280)
0x126747bc0     0  d4200000       brk #0x0
0x126747bc4     4  d10103ff       sub sp, sp, #0x40 (64)
0x126747bc8     8  d106c3f0       sub x16, sp, #0x1b0 (432)
0x126747bcc     c  f8520351       ldur x17, [x26, #-224]
0x126747bd0    10  eb11021f       cmp x16, x17
0x126747bd4    14  54004083       b.lo #+0x810 (addr 0x1267483e4)
0x126747bd8    18  f85c03a0       ldur x0, [fp, #-64]
0x126747bdc    1c  37007da0       tbnz w0, #0, #+0xfb4 (addr 0x126748b90)
0x126747be0    20  d360fc00       lsr x0, x0, #32
0x126747be4    24  f81a83a0       stur x0, [fp, #-88]
0x126747be8    28  f9400fa1       ldr x1, [fp, #24]
0x126747bec    2c  37007d41       tbnz w1, #0, #+0xfa8 (addr 0x126748b94)
0x126747bf0    30  d360fc21       lsr x1, x1, #32
0x126747bf4    34  f81903a1       stur x1, [fp, #-112]
0x126747bf8    38  6b01001f       cmp w0, w1
0x126747bfc    3c  54003f0a       b.ge #+0x7e0 (addr 0x1267483dc)
0x126747c00    40  f85f83a2       ldur x2, [fp, #-8]
0x126747c04    44  f8437043       ldur x3, [x2, #55]
0x126747c08    48  f81d03a3       stur x3, [fp, #-48]
0x126747c0c    4c  f843f044       ldur x4, [x2, #63]
0x126747c10    50  58007750       ldr x16, pc+3816 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126747c14    54  eb10009f       cmp x4, x16
0x126747c18    58  54007c01       b.ne #+0xf80 (addr 0x126748b98)
0x126747c1c    5c  f94013a4       ldr x4, [fp, #32]
0x126747c20    60  37007be4       tbnz w4, #0, #+0xf7c (addr 0x126748b9c)
0x126747c24    64  d360fc84       lsr x4, x4, #32
0x126747c28    68  f81a03a4       stur x4, [fp, #-96]
0x126747c2c    6c  52800005       movz w5, #0x0
0x126747c30    70  6b05009f       cmp w4, w5
0x126747c34    74  54000c4d       b.le #+0x188 (addr 0x126747dbc)
0x126747c38    78  5800765b       ldr cp, pc+3784 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747c3c    7c  f842f366       ldur x6, [cp, #47]
0x126747c40    80  f81d83a6       stur x6, [fp, #-40]
0x126747c44    84  f940d750       ldr x16, [x26, #424]
0x126747c48    88  eb1000df       cmp x6, x16
0x126747c4c    8c  54003d60       b.eq #+0x7ac (addr 0x1267483f8)
0x126747c50    90  f843f367       ldur x7, [cp, #63]
0x126747c54    94  71000488       subs w8, w4, #0x1 (1)
0x126747c58    98  54007a46       b.vs #+0xf48 (addr 0x126748ba0)
0x126747c5c    9c  f81983a8       stur x8, [fp, #-104]
0x126747c60    a0  580074d0       ldr x16, pc+3736 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126747c64    a4  eb1000ff       cmp x7, x16
0x126747c68    a8  540079e1       b.ne #+0xf3c (addr 0x126748ba4)
0x126747c6c    ac  d3607d07       lsl x7, x8, #32
0x126747c70    b0  f81b83a7       stur x7, [fp, #-72]
0x126747c74    b4  aa0103e9       mov x9, x1
0x126747c78    b8  58007401       ldr x1, pc+3712 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126747c7c    bc  f940d343       ldr x3, [x26, #416]
0x126747c80    c0  a9bf1fe3       stp x3, x7, [sp, #-16]!
0x126747c84    c4  52800040       movz w0, #0x2
0x126747c88    c8  18007684       ldr w4, pc+3792 (addr 0x0000000126748b58)    ;; js dispatch handle:0x2c4700 TURBOFAN_JS
0x126747c8c    cc  d2a1cd55       movz x21, #0xe6a0000
0x126747c90    d0  f2c00035       movk x21, #0x1, lsl #32
0x126747c94    d4  d2988e10       movz x16, #0xc470
0x126747c98    d8  f2a00050       movk x16, #0x2, lsl #16
0x126747c9c    dc  f8706aa2       ldr x2, [x21, x16]
0x126747ca0    e0  d63f0040       blr x2
0x126747ca4    e4  f81b03a0       stur x0, [fp, #-80]
0x126747ca8    e8  580072c1       ldr x1, pc+3672 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747cac    ec  f843f022       ldur x2, [x1, #63]
0x126747cb0    f0  58007250       ldr x16, pc+3656 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126747cb4    f4  eb10005f       cmp x2, x16
0x126747cb8    f8  54007781       b.ne #+0xef0 (addr 0x126748ba8)
0x126747cbc    fc  580071e1       ldr x1, pc+3644 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126747cc0   100  5800721b       ldr cp, pc+3648 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747cc4   104  f940d343       ldr x3, [x26, #416]
0x126747cc8   108  f85b83b0       ldur x16, [fp, #-72]
0x126747ccc   10c  a9bf43e3       stp x3, x16, [sp, #-16]!
0x126747cd0   110  52800040       movz w0, #0x2
0x126747cd4   114  18007424       ldr w4, pc+3716 (addr 0x0000000126748b58)
0x126747cd8   118  d2a1cd55       movz x21, #0xe6a0000
0x126747cdc   11c  f2c00035       movk x21, #0x1, lsl #32
0x126747ce0   120  d2988e10       movz x16, #0xc470
0x126747ce4   124  f2a00050       movk x16, #0x2, lsl #16
0x126747ce8   128  f8706aa2       ldr x2, [x21, x16]
0x126747cec   12c  d63f0040       blr x2
0x126747cf0   130  f85d83a1       ldur x1, [fp, #-40]
0x126747cf4   134  580070b0       ldr x16, pc+3604 (addr 0x0000000126748b08)    ;; object: 0x1dadb5f4b8f9 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x126747cf8   138  eb10003f       cmp x1, x16
0x126747cfc   13c  54007581       b.ne #+0xeb0 (addr 0x126748bac)
0x126747d00   140  f85d0342       ldur x2, [x26, #-48]
0x126747d04   144  9100a042       add x2, x2, #0x28 (40)
0x126747d08   148  f85d8350       ldur x16, [x26, #-40]
0x126747d0c   14c  eb10005f       cmp x2, x16
0x126747d10   150  54003a42       b.hs #+0x748 (addr 0x126748458)
0x126747d14   154  f81d0342       stur x2, [x26, #-48]
0x126747d18   158  d1009c42       sub x2, x2, #0x27 (39)
0x126747d1c   15c  aa0203e1       mov x1, x2
0x126747d20   160  58006f83       ldr x3, pc+3568 (addr 0x0000000126748b10)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126747d24   164  f81ff023       stur x3, [x1, #-1]
0x126747d28   168  f9413743       ldr x3, [x26, #616]
0x126747d2c   16c  f8007023       stur x3, [x1, #7]
0x126747d30   170  f800f023       stur x3, [x1, #15]
0x126747d34   174  f940c744       ldr x4, [x26, #392]
0x126747d38   178  f8017024       stur x4, [x1, #23]
0x126747d3c   17c  f801f024       stur x4, [x1, #31]
0x126747d40   180  f85b03a5       ldur x5, [fp, #-80]
0x126747d44   184  36007365       tbz w5, #0, #+0xe6c (addr 0x126748bb0)
0x126747d48   188  f8017025       stur x5, [x1, #23]
0x126747d4c   18c  36000085       tbz w5, #0, #+0x10 (addr 0x126747d5c)
0x126747d50   190  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747d54   194  f9400231       ldr x17, [x17]
0x126747d58   198  37103911       tbnz w17, #2, #+0x720 (addr 0x126748478)
0x126747d5c   19c  58006de6       ldr x6, pc+3516 (addr 0x0000000126748b18)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126747d60   1a0  f81ff026       stur x6, [x1, #-1]
0x126747d64   1a4  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747d68   1a8  f9400231       ldr x17, [x17]
0x126747d6c   1ac  371039b1       tbnz w17, #2, #+0x734 (addr 0x1267484a0)
0x126747d70   1b0  36007220       tbz w0, #0, #+0xe44 (addr 0x126748bb4)
0x126747d74   1b4  f801f020       stur x0, [x1, #31]
0x126747d78   1b8  36000080       tbz w0, #0, #+0x10 (addr 0x126747d88)
0x126747d7c   1bc  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747d80   1c0  f9400231       ldr x17, [x17]
0x126747d84   1c4  37103a31       tbnz w17, #2, #+0x744 (addr 0x1267484c8)
0x126747d88   1c8  58006cc0       ldr x0, pc+3480 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126747d8c   1cc  f81ff020       stur x0, [x1, #-1]
0x126747d90   1d0  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747d94   1d4  f9400231       ldr x17, [x17]
0x126747d98   1d8  37103a91       tbnz w17, #2, #+0x750 (addr 0x1267484e8)
0x126747d9c   1dc  52800005       movz w5, #0x0
0x126747da0   1e0  58006b06       ldr x6, pc+3424 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747da4   1e4  f9413748       ldr x8, [x26, #616]
0x126747da8   1e8  f940c749       ldr x9, [x26, #392]
0x126747dac   1ec  f940db4a       ldr x10, [x26, #432]
0x126747db0   1f0  f85f83a2       ldur x2, [fp, #-8]
0x126747db4   1f4  f85a83a0       ldur x0, [fp, #-88]
0x126747db8   1f8  14000029       b #+0xa4 (addr 0x126747e5c)
0x126747dbc   1fc  58006a26       ldr x6, pc+3396 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747dc0   200  f842f0c7       ldur x7, [x6, #47]
0x126747dc4   204  f81b03a7       stur x7, [fp, #-80]
0x126747dc8   208  f940d750       ldr x16, [x26, #424]
0x126747dcc   20c  eb1000ff       cmp x7, x16
0x126747dd0   210  540039c0       b.eq #+0x738 (addr 0x126748508)
0x126747dd4   214  580069b0       ldr x16, pc+3380 (addr 0x0000000126748b08)    ;; object: 0x1dadb5f4b8f9 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x126747dd8   218  eb1000ff       cmp x7, x16
0x126747ddc   21c  54006ee1       b.ne #+0xddc (addr 0x126748bb8)
0x126747de0   220  f85d0347       ldur x7, [x26, #-48]
0x126747de4   224  9100a0e7       add x7, x7, #0x28 (40)
0x126747de8   228  f85d8350       ldur x16, [x26, #-40]
0x126747dec   22c  eb1000ff       cmp x7, x16
0x126747df0   230  54003a22       b.hs #+0x744 (addr 0x126748534)
0x126747df4   234  f81d0347       stur x7, [x26, #-48]
0x126747df8   238  d1009ce7       sub x7, x7, #0x27 (39)
0x126747dfc   23c  aa0703e1       mov x1, x7
0x126747e00   240  58006888       ldr x8, pc+3344 (addr 0x0000000126748b10)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126747e04   244  f81ff028       stur x8, [x1, #-1]
0x126747e08   248  f9413748       ldr x8, [x26, #616]
0x126747e0c   24c  f8007028       stur x8, [x1, #7]
0x126747e10   250  f800f028       stur x8, [x1, #15]
0x126747e14   254  f940c749       ldr x9, [x26, #392]
0x126747e18   258  f8017029       stur x9, [x1, #23]
0x126747e1c   25c  f801f029       stur x9, [x1, #31]
0x126747e20   260  f940db4a       ldr x10, [x26, #432]
0x126747e24   264  f801702a       stur x10, [x1, #23]
0x126747e28   268  5800678b       ldr x11, pc+3312 (addr 0x0000000126748b18)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126747e2c   26c  f81ff02b       stur x11, [x1, #-1]
0x126747e30   270  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747e34   274  f9400231       ldr x17, [x17]
0x126747e38   278  371039b1       tbnz w17, #2, #+0x734 (addr 0x12674856c)
0x126747e3c   27c  f801f02a       stur x10, [x1, #31]
0x126747e40   280  5800670b       ldr x11, pc+3296 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126747e44   284  f81ff02b       stur x11, [x1, #-1]
0x126747e48   288  926eb431       and x17, x1, #0xfffffffffffc0000
0x126747e4c   28c  f9400231       ldr x17, [x17]
0x126747e50   290  37103a31       tbnz w17, #2, #+0x744 (addr 0x126748594)
0x126747e54   294  aa0803e3       mov x3, x8
0x126747e58   298  aa0903e4       mov x4, x9
0x126747e5c   29c  f81b03a1       stur x1, [fp, #-80]
0x126747e60   2a0  f85d03a7       ldur x7, [fp, #-48]
0x126747e64   2a4  58006630       ldr x16, pc+3268 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126747e68   2a8  eb1000ff       cmp x7, x16
0x126747e6c   2ac  54006a81       b.ne #+0xd50 (addr 0x126748bbc)
0x126747e70   2b0  f85ff030       ldur x16, [x1, #-1]
0x126747e74   2b4  58006571       ldr x17, pc+3244 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126747e78   2b8  eb11021f       cmp x16, x17
0x126747e7c   2bc  54006a21       b.ne #+0xd44 (addr 0x126748bc0)
0x126747e80   2c0  f8417027       ldur x7, [x1, #23]
0x126747e84   2c4  f940db50       ldr x16, [x26, #432]
0x126747e88   2c8  eb1000ff       cmp x7, x16
0x126747e8c   2cc  540000c0       b.eq #+0x18 (addr 0x126747ea4)
0x126747e90   2d0  f841f02b       ldur x11, [x1, #31]
0x126747e94   2d4  f81d03ab       stur x11, [fp, #-48]
0x126747e98   2d8  f940db50       ldr x16, [x26, #432]
0x126747e9c   2dc  eb10017f       cmp x11, x16
0x126747ea0   2e0  54000061       b.ne #+0xc (addr 0x126747eac)
0x126747ea4   2e4  52800021       movz w1, #0x1
0x126747ea8   2e8  1400003a       b #+0xe8 (addr 0x126747f90)
0x126747eac   2ec  f84370cc       ldur x12, [x6, #55]
0x126747eb0   2f0  580063d0       ldr x16, pc+3192 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126747eb4   2f4  eb10019f       cmp x12, x16
0x126747eb8   2f8  54006861       b.ne #+0xd0c (addr 0x126748bc4)
0x126747ebc   2fc  aa0103ec       mov x12, x1
0x126747ec0   300  58006341       ldr x1, pc+3176 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126747ec4   304  aa0603fb       mov cp, x6
0x126747ec8   308  f940d343       ldr x3, [x26, #416]
0x126747ecc   30c  a9bf1fe3       stp x3, x7, [sp, #-16]!
0x126747ed0   310  52800040       movz w0, #0x2
0x126747ed4   314  180063e4       ldr w4, pc+3196 (addr 0x0000000126748b50)    ;; js dispatch handle:0x2c4600 TURBOFAN_JS
0x126747ed8   318  d2a1cd55       movz x21, #0xe6a0000
0x126747edc   31c  f2c00035       movk x21, #0x1, lsl #32
0x126747ee0   320  d2988c10       movz x16, #0xc460
0x126747ee4   324  f2a00050       movk x16, #0x2, lsl #16
0x126747ee8   328  f8706aa2       ldr x2, [x21, x16]
0x126747eec   32c  d63f0040       blr x2
0x126747ef0   330  aa0003e1       mov x1, x0
0x126747ef4   334  370066a0       tbnz w0, #0, #+0xcd4 (addr 0x126748bc8)
0x126747ef8   338  d360fc00       lsr x0, x0, #32
0x126747efc   33c  31000402       adds w2, w0, #0x1 (1)
0x126747f00   340  54006666       b.vs #+0xccc (addr 0x126748bcc)
0x126747f04   344  f81883a2       stur x2, [fp, #-120]
0x126747f08   348  58005fc0       ldr x0, pc+3064 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747f0c   34c  f8437003       ldur x3, [x0, #55]
0x126747f10   350  580060d0       ldr x16, pc+3096 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126747f14   354  eb10007f       cmp x3, x16
0x126747f18   358  540065c1       b.ne #+0xcb8 (addr 0x126748bd0)
0x126747f1c   35c  58006061       ldr x1, pc+3084 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126747f20   360  aa0003fb       mov cp, x0
0x126747f24   364  f940d343       ldr x3, [x26, #416]
0x126747f28   368  f85d03b0       ldur x16, [fp, #-48]
0x126747f2c   36c  a9bf43e3       stp x3, x16, [sp, #-16]!
0x126747f30   370  52800040       movz w0, #0x2
0x126747f34   374  180060e4       ldr w4, pc+3100 (addr 0x0000000126748b50)
0x126747f38   378  d2a1cd55       movz x21, #0xe6a0000
0x126747f3c   37c  f2c00035       movk x21, #0x1, lsl #32
0x126747f40   380  d2988c10       movz x16, #0xc460
0x126747f44   384  f2a00050       movk x16, #0x2, lsl #16
0x126747f48   388  f8706aa2       ldr x2, [x21, x16]
0x126747f4c   38c  d63f0040       blr x2
0x126747f50   390  aa0003e1       mov x1, x0
0x126747f54   394  37006400       tbnz w0, #0, #+0xc80 (addr 0x126748bd4)
0x126747f58   398  d360fc00       lsr x0, x0, #32
0x126747f5c   39c  f85883a2       ldur x2, [fp, #-120]
0x126747f60   3a0  2b000043       adds w3, w2, w0
0x126747f64   3a4  540063a6       b.vs #+0xc74 (addr 0x126748bd8)
0x126747f68   3a8  aa0303e1       mov x1, x3
0x126747f6c   3ac  f9413743       ldr x3, [x26, #616]
0x126747f70   3b0  f940c744       ldr x4, [x26, #392]
0x126747f74   3b4  52800005       movz w5, #0x0
0x126747f78   3b8  58005c46       ldr x6, pc+2952 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126747f7c   3bc  f9413748       ldr x8, [x26, #616]
0x126747f80   3c0  f940c749       ldr x9, [x26, #392]
0x126747f84   3c4  f940db4a       ldr x10, [x26, #432]
0x126747f88   3c8  f85f83a2       ldur x2, [fp, #-8]
0x126747f8c   3cc  f85a83a0       ldur x0, [fp, #-88]
0x126747f90   3d0  f81783a1       stur x1, [fp, #-136]
0x126747f94   3d4  f85c83a7       ldur x7, [fp, #-56]
0x126747f98   3d8  37006227       tbnz w7, #0, #+0xc44 (addr 0x126748bdc)
0x126747f9c   3dc  d360fce7       lsr x7, x7, #32
0x126747fa0   3e0  2b0100eb       adds w11, w7, w1
0x126747fa4   3e4  540061e6       b.vs #+0xc3c (addr 0x126748be0)
0x126747fa8   3e8  f81883ab       stur x11, [fp, #-120]
0x126747fac   3ec  31000407       adds w7, w0, #0x1 (1)
0x126747fb0   3f0  540061a6       b.vs #+0xc34 (addr 0x126748be4)
0x126747fb4   3f4  f81803a7       stur x7, [fp, #-128]
0x126747fb8   3f8  58005bc0       ldr x0, pc+2936 (addr 0x0000000126748b30)    ;; object: 0x1dadb5f42bd1 <FeedbackCell[one closure]>
0x126747fbc   3fc  b841300c       ldur w12, [x0, #19]
0x126747fc0   400  71006d8c       subs w12, w12, #0x1b (27)
0x126747fc4   404  b801300c       stur w12, [x0, #19]
0x126747fc8   408  54002fab       b.lt #+0x5f4 (addr 0x1267485bc)
0x126747fcc   40c  58005b6c       ldr x12, pc+2924 (addr 0x0000000126748b38)    ;; object: 0x18ddcf638021 <FeedbackVector[15]>
0x126747fd0   410  3940518d       ldrb w13, [x12, #20]
0x126747fd4   414  d3400dad       ubfx x13, x13, #0, #4
0x126747fd8   418  3500352d       cbnz w13, #+0x6a4 (addr 0x12674867c)
0x126747fdc   41c  f85803a1       ldur x1, [fp, #-128]
0x126747fe0   420  f85883a0       ldur x0, [fp, #-120]
0x126747fe4   424  f81803a0       stur x0, [fp, #-128]
0x126747fe8   428  f81883a1       stur x1, [fp, #-120]
0x126747fec   42c  f85903a2       ldur x2, [fp, #-112]
0x126747ff0   430  6b02003f       cmp w1, w2
0x126747ff4   434  54001f0a       b.ge #+0x3e0 (addr 0x1267483d4)
0x126747ff8   438  f85f83a3       ldur x3, [fp, #-8]
0x126747ffc   43c  f8437064       ldur x4, [x3, #55]
0x126748000   440  f81c03a4       stur x4, [fp, #-64]
0x126748004   444  f843f065       ldur x5, [x3, #63]
0x126748008   448  58005790       ldr x16, pc+2800 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x12674800c   44c  eb1000bf       cmp x5, x16
0x126748010   450  54005ec1       b.ne #+0xbd8 (addr 0x126748be8)
0x126748014   454  f85a03a5       ldur x5, [fp, #-96]
0x126748018   458  52800006       movz w6, #0x0
0x12674801c   45c  6b0600bf       cmp w5, w6
0x126748020   460  54000c6d       b.le #+0x18c (addr 0x1267481ac)
0x126748024   464  580056e7       ldr x7, pc+2780 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126748028   468  f842f0e8       ldur x8, [x7, #47]
0x12674802c   46c  f81b03a8       stur x8, [fp, #-80]
0x126748030   470  f940d750       ldr x16, [x26, #424]
0x126748034   474  eb10011f       cmp x8, x16
0x126748038   478  540035c0       b.eq #+0x6b8 (addr 0x1267486f0)
0x12674803c   47c  f843f0e9       ldur x9, [x7, #63]
0x126748040   480  710004aa       subs w10, w5, #0x1 (1)
0x126748044   484  54005d46       b.vs #+0xba8 (addr 0x126748bec)
0x126748048   488  f81783aa       stur x10, [fp, #-136]
0x12674804c   48c  58005570       ldr x16, pc+2732 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126748050   490  eb10013f       cmp x9, x16
0x126748054   494  54005ce1       b.ne #+0xb9c (addr 0x126748bf0)
0x126748058   498  d3607d49       lsl x9, x10, #32
0x12674805c   49c  f81d03a9       stur x9, [fp, #-48]
0x126748060   4a0  580054c1       ldr x1, pc+2712 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126748064   4a4  aa0703fb       mov cp, x7
0x126748068   4a8  f940d343       ldr x3, [x26, #416]
0x12674806c   4ac  a9bf27e3       stp x3, x9, [sp, #-16]!
0x126748070   4b0  52800040       movz w0, #0x2
0x126748074   4b4  18005724       ldr w4, pc+2788 (addr 0x0000000126748b58)
0x126748078   4b8  d2a1cd55       movz x21, #0xe6a0000
0x12674807c   4bc  f2c00035       movk x21, #0x1, lsl #32
0x126748080   4c0  d2988e10       movz x16, #0xc470
0x126748084   4c4  f2a00050       movk x16, #0x2, lsl #16
0x126748088   4c8  f8706aa2       ldr x2, [x21, x16]
0x12674808c   4cc  d63f0040       blr x2
0x126748090   4d0  f81d83a0       stur x0, [fp, #-40]
0x126748094   4d4  58005361       ldr x1, pc+2668 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126748098   4d8  f843f022       ldur x2, [x1, #63]
0x12674809c   4dc  580052f0       ldr x16, pc+2652 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267480a0   4e0  eb10005f       cmp x2, x16
0x1267480a4   4e4  54005a81       b.ne #+0xb50 (addr 0x126748bf4)
0x1267480a8   4e8  58005281       ldr x1, pc+2640 (addr 0x0000000126748af8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267480ac   4ec  580052bb       ldr cp, pc+2644 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x1267480b0   4f0  f940d343       ldr x3, [x26, #416]
0x1267480b4   4f4  f85d03b0       ldur x16, [fp, #-48]
0x1267480b8   4f8  a9bf43e3       stp x3, x16, [sp, #-16]!
0x1267480bc   4fc  52800040       movz w0, #0x2
0x1267480c0   500  180054c4       ldr w4, pc+2712 (addr 0x0000000126748b58)
0x1267480c4   504  d2a1cd55       movz x21, #0xe6a0000
0x1267480c8   508  f2c00035       movk x21, #0x1, lsl #32
0x1267480cc   50c  d2988e10       movz x16, #0xc470
0x1267480d0   510  f2a00050       movk x16, #0x2, lsl #16
0x1267480d4   514  f8706aa2       ldr x2, [x21, x16]
0x1267480d8   518  d63f0040       blr x2
0x1267480dc   51c  f85b03a1       ldur x1, [fp, #-80]
0x1267480e0   520  58005150       ldr x16, pc+2600 (addr 0x0000000126748b08)    ;; object: 0x1dadb5f4b8f9 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x1267480e4   524  eb10003f       cmp x1, x16
0x1267480e8   528  54005881       b.ne #+0xb10 (addr 0x126748bf8)
0x1267480ec   52c  f85d0342       ldur x2, [x26, #-48]
0x1267480f0   530  9100a042       add x2, x2, #0x28 (40)
0x1267480f4   534  f85d8350       ldur x16, [x26, #-40]
0x1267480f8   538  eb10005f       cmp x2, x16
0x1267480fc   53c  540032a2       b.hs #+0x654 (addr 0x126748750)
0x126748100   540  f81d0342       stur x2, [x26, #-48]
0x126748104   544  d1009c42       sub x2, x2, #0x27 (39)
0x126748108   548  aa0203e1       mov x1, x2
0x12674810c   54c  58005023       ldr x3, pc+2564 (addr 0x0000000126748b10)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126748110   550  f81ff023       stur x3, [x1, #-1]
0x126748114   554  f9413743       ldr x3, [x26, #616]
0x126748118   558  f8007023       stur x3, [x1, #7]
0x12674811c   55c  f800f023       stur x3, [x1, #15]
0x126748120   560  f940c744       ldr x4, [x26, #392]
0x126748124   564  f8017024       stur x4, [x1, #23]
0x126748128   568  f801f024       stur x4, [x1, #31]
0x12674812c   56c  f85d83a5       ldur x5, [fp, #-40]
0x126748130   570  36005665       tbz w5, #0, #+0xacc (addr 0x126748bfc)
0x126748134   574  f8017025       stur x5, [x1, #23]
0x126748138   578  36000085       tbz w5, #0, #+0x10 (addr 0x126748148)
0x12674813c   57c  926eb431       and x17, x1, #0xfffffffffffc0000
0x126748140   580  f9400231       ldr x17, [x17]
0x126748144   584  37103171       tbnz w17, #2, #+0x62c (addr 0x126748770)
0x126748148   588  58004e86       ldr x6, pc+2512 (addr 0x0000000126748b18)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x12674814c   58c  f81ff026       stur x6, [x1, #-1]
0x126748150   590  926eb431       and x17, x1, #0xfffffffffffc0000
0x126748154   594  f9400231       ldr x17, [x17]
0x126748158   598  37103211       tbnz w17, #2, #+0x640 (addr 0x126748798)
0x12674815c   59c  36005520       tbz w0, #0, #+0xaa4 (addr 0x126748c00)
0x126748160   5a0  f801f020       stur x0, [x1, #31]
0x126748164   5a4  36000080       tbz w0, #0, #+0x10 (addr 0x126748174)
0x126748168   5a8  926eb431       and x17, x1, #0xfffffffffffc0000
0x12674816c   5ac  f9400231       ldr x17, [x17]
0x126748170   5b0  37103291       tbnz w17, #2, #+0x650 (addr 0x1267487c0)
0x126748174   5b4  58004d60       ldr x0, pc+2476 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126748178   5b8  f81ff020       stur x0, [x1, #-1]
0x12674817c   5bc  926eb431       and x17, x1, #0xfffffffffffc0000
0x126748180   5c0  f9400231       ldr x17, [x17]
0x126748184   5c4  371032f1       tbnz w17, #2, #+0x65c (addr 0x1267487e0)
0x126748188   5c8  52800006       movz w6, #0x0
0x12674818c   5cc  58004ba7       ldr x7, pc+2420 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x126748190   5d0  f9413749       ldr x9, [x26, #616]
0x126748194   5d4  f940c74a       ldr x10, [x26, #392]
0x126748198   5d8  f940db4b       ldr x11, [x26, #432]
0x12674819c   5dc  f85a03a5       ldur x5, [fp, #-96]
0x1267481a0   5e0  f85903a2       ldur x2, [fp, #-112]
0x1267481a4   5e4  f85803a0       ldur x0, [fp, #-128]
0x1267481a8   5e8  14000029       b #+0xa4 (addr 0x12674824c)
0x1267481ac   5ec  58004aa7       ldr x7, pc+2388 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x1267481b0   5f0  f842f0e8       ldur x8, [x7, #47]
0x1267481b4   5f4  f81d83a8       stur x8, [fp, #-40]
0x1267481b8   5f8  f940d750       ldr x16, [x26, #424]
0x1267481bc   5fc  eb10011f       cmp x8, x16
0x1267481c0   600  54003200       b.eq #+0x640 (addr 0x126748800)
0x1267481c4   604  58004a30       ldr x16, pc+2372 (addr 0x0000000126748b08)    ;; object: 0x1dadb5f4b8f9 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>
0x1267481c8   608  eb10011f       cmp x8, x16
0x1267481cc   60c  540051c1       b.ne #+0xa38 (addr 0x126748c04)
0x1267481d0   610  f85d0348       ldur x8, [x26, #-48]
0x1267481d4   614  9100a108       add x8, x8, #0x28 (40)
0x1267481d8   618  f85d8350       ldur x16, [x26, #-40]
0x1267481dc   61c  eb10011f       cmp x8, x16
0x1267481e0   620  54003262       b.hs #+0x64c (addr 0x12674882c)
0x1267481e4   624  f81d0348       stur x8, [x26, #-48]
0x1267481e8   628  d1009d08       sub x8, x8, #0x27 (39)
0x1267481ec   62c  aa0803e1       mov x1, x8
0x1267481f0   630  58004909       ldr x9, pc+2336 (addr 0x0000000126748b10)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1267481f4   634  f81ff029       stur x9, [x1, #-1]
0x1267481f8   638  f9413749       ldr x9, [x26, #616]
0x1267481fc   63c  f8007029       stur x9, [x1, #7]
0x126748200   640  f800f029       stur x9, [x1, #15]
0x126748204   644  f940c74a       ldr x10, [x26, #392]
0x126748208   648  f801702a       stur x10, [x1, #23]
0x12674820c   64c  f801f02a       stur x10, [x1, #31]
0x126748210   650  f940db4b       ldr x11, [x26, #432]
0x126748214   654  f801702b       stur x11, [x1, #23]
0x126748218   658  5800480c       ldr x12, pc+2304 (addr 0x0000000126748b18)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x12674821c   65c  f81ff02c       stur x12, [x1, #-1]
0x126748220   660  926eb431       and x17, x1, #0xfffffffffffc0000
0x126748224   664  f9400231       ldr x17, [x17]
0x126748228   668  371031f1       tbnz w17, #2, #+0x63c (addr 0x126748864)
0x12674822c   66c  f801f02b       stur x11, [x1, #31]
0x126748230   670  5800478c       ldr x12, pc+2288 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126748234   674  f81ff02c       stur x12, [x1, #-1]
0x126748238   678  926eb431       and x17, x1, #0xfffffffffffc0000
0x12674823c   67c  f9400231       ldr x17, [x17]
0x126748240   680  37103271       tbnz w17, #2, #+0x64c (addr 0x12674888c)
0x126748244   684  aa0903e3       mov x3, x9
0x126748248   688  aa0a03e4       mov x4, x10
0x12674824c   68c  f81d83a1       stur x1, [fp, #-40]
0x126748250   690  f85c03a8       ldur x8, [fp, #-64]
0x126748254   694  580046b0       ldr x16, pc+2260 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126748258   698  eb10011f       cmp x8, x16
0x12674825c   69c  54004d61       b.ne #+0x9ac (addr 0x126748c08)
0x126748260   6a0  f85ff030       ldur x16, [x1, #-1]
0x126748264   6a4  580045f1       ldr x17, pc+2236 (addr 0x0000000126748b20)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126748268   6a8  eb11021f       cmp x16, x17
0x12674826c   6ac  54004d01       b.ne #+0x9a0 (addr 0x126748c0c)
0x126748270   6b0  f8417028       ldur x8, [x1, #23]
0x126748274   6b4  f940db50       ldr x16, [x26, #432]
0x126748278   6b8  eb10011f       cmp x8, x16
0x12674827c   6bc  540000c0       b.eq #+0x18 (addr 0x126748294)
0x126748280   6c0  f841f02c       ldur x12, [x1, #31]
0x126748284   6c4  f81c03ac       stur x12, [fp, #-64]
0x126748288   6c8  f940db50       ldr x16, [x26, #432]
0x12674828c   6cc  eb10019f       cmp x12, x16
0x126748290   6d0  54000061       b.ne #+0xc (addr 0x12674829c)
0x126748294   6d4  52800021       movz w1, #0x1
0x126748298   6d8  1400003b       b #+0xec (addr 0x126748384)
0x12674829c   6dc  f84370ed       ldur x13, [x7, #55]
0x1267482a0   6e0  58004450       ldr x16, pc+2184 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267482a4   6e4  eb1001bf       cmp x13, x16
0x1267482a8   6e8  54004b41       b.ne #+0x968 (addr 0x126748c10)
0x1267482ac   6ec  aa0103ed       mov x13, x1
0x1267482b0   6f0  580043c1       ldr x1, pc+2168 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267482b4   6f4  aa0703fb       mov cp, x7
0x1267482b8   6f8  f940d343       ldr x3, [x26, #416]
0x1267482bc   6fc  a9bf23e3       stp x3, x8, [sp, #-16]!
0x1267482c0   700  52800040       movz w0, #0x2
0x1267482c4   704  18004464       ldr w4, pc+2188 (addr 0x0000000126748b50)
0x1267482c8   708  d2a1cd55       movz x21, #0xe6a0000
0x1267482cc   70c  f2c00035       movk x21, #0x1, lsl #32
0x1267482d0   710  d2988c10       movz x16, #0xc460
0x1267482d4   714  f2a00050       movk x16, #0x2, lsl #16
0x1267482d8   718  f8706aa2       ldr x2, [x21, x16]
0x1267482dc   71c  d63f0040       blr x2
0x1267482e0   720  aa0003e1       mov x1, x0
0x1267482e4   724  37004980       tbnz w0, #0, #+0x930 (addr 0x126748c14)
0x1267482e8   728  d360fc00       lsr x0, x0, #32
0x1267482ec   72c  31000402       adds w2, w0, #0x1 (1)
0x1267482f0   730  54004946       b.vs #+0x928 (addr 0x126748c18)
0x1267482f4   734  f81783a2       stur x2, [fp, #-136]
0x1267482f8   738  58004040       ldr x0, pc+2056 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x1267482fc   73c  f8437003       ldur x3, [x0, #55]
0x126748300   740  58004150       ldr x16, pc+2088 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126748304   744  eb10007f       cmp x3, x16
0x126748308   748  540048a1       b.ne #+0x914 (addr 0x126748c1c)
0x12674830c   74c  580040e1       ldr x1, pc+2076 (addr 0x0000000126748b28)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126748310   750  aa0003fb       mov cp, x0
0x126748314   754  f940d343       ldr x3, [x26, #416]
0x126748318   758  f85c03b0       ldur x16, [fp, #-64]
0x12674831c   75c  a9bf43e3       stp x3, x16, [sp, #-16]!
0x126748320   760  52800040       movz w0, #0x2
0x126748324   764  18004164       ldr w4, pc+2092 (addr 0x0000000126748b50)
0x126748328   768  d2a1cd55       movz x21, #0xe6a0000
0x12674832c   76c  f2c00035       movk x21, #0x1, lsl #32
0x126748330   770  d2988c10       movz x16, #0xc460
0x126748334   774  f2a00050       movk x16, #0x2, lsl #16
0x126748338   778  f8706aa2       ldr x2, [x21, x16]
0x12674833c   77c  d63f0040       blr x2
0x126748340   780  aa0003e1       mov x1, x0
0x126748344   784  370046e0       tbnz w0, #0, #+0x8dc (addr 0x126748c20)
0x126748348   788  d360fc00       lsr x0, x0, #32
0x12674834c   78c  f85783a2       ldur x2, [fp, #-136]
0x126748350   790  2b000043       adds w3, w2, w0
0x126748354   794  54004686       b.vs #+0x8d0 (addr 0x126748c24)
0x126748358   798  aa0303e1       mov x1, x3
0x12674835c   79c  f9413743       ldr x3, [x26, #616]
0x126748360   7a0  f940c744       ldr x4, [x26, #392]
0x126748364   7a4  52800006       movz w6, #0x0
0x126748368   7a8  58003cc7       ldr x7, pc+1944 (addr 0x0000000126748b00)    ;; object: 0x1dadb5f4b861 <FunctionContext[7]>
0x12674836c   7ac  f9413749       ldr x9, [x26, #616]
0x126748370   7b0  f940c74a       ldr x10, [x26, #392]
0x126748374   7b4  f940db4b       ldr x11, [x26, #432]
0x126748378   7b8  f85a03a5       ldur x5, [fp, #-96]
0x12674837c   7bc  f85903a2       ldur x2, [fp, #-112]
0x126748380   7c0  f85803a0       ldur x0, [fp, #-128]
0x126748384   7c4  f81683a1       stur x1, [fp, #-152]
0x126748388   7c8  2b010008       adds w8, w0, w1
0x12674838c   7cc  540044e6       b.vs #+0x89c (addr 0x126748c28)
0x126748390   7d0  f81783a8       stur x8, [fp, #-136]
0x126748394   7d4  f85883ac       ldur x12, [fp, #-120]
0x126748398   7d8  3100058d       adds w13, w12, #0x1 (1)
0x12674839c   7dc  54004486       b.vs #+0x890 (addr 0x126748c2c)
0x1267483a0   7e0  f81703ad       stur x13, [fp, #-144]
0x1267483a4   7e4  58003c6e       ldr x14, pc+1932 (addr 0x0000000126748b30)    ;; object: 0x1dadb5f42bd1 <FeedbackCell[one closure]>
0x1267483a8   7e8  b84131cf       ldur w15, [x14, #19]
0x1267483ac   7ec  71006def       subs w15, w15, #0x1b (27)
0x1267483b0   7f0  b80131cf       stur w15, [x14, #19]
0x1267483b4   7f4  5400280b       b.lt #+0x500 (addr 0x1267488b4)
0x1267483b8   7f8  58003c0f       ldr x15, pc+1920 (addr 0x0000000126748b38)    ;; object: 0x18ddcf638021 <FeedbackVector[15]>
0x1267483bc   7fc  394051f3       ldrb w19, [x15, #20]
0x1267483c0   800  d3400e73       ubfx x19, x19, #0, #4
0x1267483c4   804  35002e93       cbnz w19, #+0x5d0 (addr 0x126748994)
0x1267483c8   808  f85703a1       ldur x1, [fp, #-144]
0x1267483cc   80c  f85783a0       ldur x0, [fp, #-136]
0x1267483d0   810  17ffff05       b #-0x3ec (addr 0x126747fe4)
0x1267483d4   814  d3607c01       lsl x1, x0, #32
0x1267483d8   818  14000002       b #+0x8 (addr 0x1267483e0)
0x1267483dc   81c  f85c83a1       ldur x1, [fp, #-56]
0x1267483e0   820  14000214       b #+0x850 (addr 0x126748c30)
0x1267483e4   824  d2c03600       movz x0, #0x1b000000000
0x1267483e8   828  58003c10       ldr x16, pc+1920 (addr 0x0000000126748b68)
0x1267483ec   82c  d63f0200       blr x16
0x1267483f0   830  17fffdfa       b #-0x818 (addr 0x126747bd8)
0x1267483f4   834  d4200000       brk #0x0
0x1267483f8   838  58003a50       ldr x16, pc+1864 (addr 0x0000000126748b40)    ;; object: 0x1dadb5f42671 <String[8]: #TreeNode>
0x1267483fc   83c  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x126748400   840  58003a5b       ldr cp, pc+1864 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x126748404   844  d2800020       movz x0, #0x1
0x126748408   848  d29b9e81       movz x1, #0xdcf4
0x12674840c   84c  f2a06081       movk x1, #0x304, lsl #16
0x126748410   850  f2c00021       movk x1, #0x1, lsl #32
0x126748414   854  58003b30       ldr x16, pc+1892 (addr 0x0000000126748b78)
0x126748418   858  d63f0200       blr x16
0x12674841c   85c  d4200000       brk #0x0
0x126748420   860  d4200000       brk #0x0
0x126748424   864  1e62011e       scvtf d30, w8
0x126748428   868  f85d0347       ldur x7, [x26, #-48]
0x12674842c   86c  910040e7       add x7, x7, #0x10 (16)
0x126748430   870  f85d8350       ldur x16, [x26, #-40]
0x126748434   874  eb1000ff       cmp x7, x16
0x126748438   878  54003022       b.hs #+0x604 (addr 0x126748a3c)
0x12674843c   87c  f81d0347       stur x7, [x26, #-48]
0x126748440   880  d1003ce7       sub x7, x7, #0xf (15)
0x126748444   884  f9412750       ldr x16, [x26, #584]
0x126748448   888  f81ff0f0       stur x16, [x7, #-1]
0x12674844c   88c  fc0070fe       stur d30, [x7, #7]
0x126748450   890  17fffe08       b #-0x7e0 (addr 0x126747c70)
0x126748454   894  d4200000       brk #0x0
0x126748458   898  a9bf03e1       stp x1, x0, [sp, #-16]!
0x12674845c   89c  52800501       movz w1, #0x28
0x126748460   8a0  58003890       ldr x16, pc+1808 (addr 0x0000000126748b70)
0x126748464   8a4  d63f0200       blr x16
0x126748468   8a8  aa0003e2       mov x2, x0
0x12674846c   8ac  a8c103e1       ldp x1, x0, [sp], #16
0x126748470   8b0  17fffe2b       b #-0x754 (addr 0x126747d1c)
0x126748474   8b4  d4200000       brk #0x0
0x126748478   8b8  926eb4b1       and x17, x5, #0xfffffffffffc0000
0x12674847c   8bc  f9400231       ldr x17, [x17]
0x126748480   8c0  360fc6f1       tbz w17, #1, #-0x724 (addr 0x126747d5c)
0x126748484   8c4  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x126748488   8c8  91005c25       add x5, x1, #0x17 (23)
0x12674848c   8cc  580036b0       ldr x16, pc+1748 (addr 0x0000000126748b60)
0x126748490   8d0  d63f0200       blr x16
0x126748494   8d4  a8c117ff       ldp xzr, x5, [sp], #16
0x126748498   8d8  17fffe31       b #-0x73c (addr 0x126747d5c)
0x12674849c   8dc  d4200000       brk #0x0
0x1267484a0   8e0  926eb4d1       and x17, x6, #0xfffffffffffc0000
0x1267484a4   8e4  f9400231       ldr x17, [x17]
0x1267484a8   8e8  360fc651       tbz w17, #1, #-0x738 (addr 0x126747d70)
0x1267484ac   8ec  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x1267484b0   8f0  d1000425       sub x5, x1, #0x1 (1)
0x1267484b4   8f4  58003570       ldr x16, pc+1708 (addr 0x0000000126748b60)
0x1267484b8   8f8  d63f0200       blr x16
0x1267484bc   8fc  a8c117ff       ldp xzr, x5, [sp], #16
0x1267484c0   900  17fffe2c       b #-0x750 (addr 0x126747d70)
0x1267484c4   904  d4200000       brk #0x0
0x1267484c8   908  926eb411       and x17, x0, #0xfffffffffffc0000
0x1267484cc   90c  f9400231       ldr x17, [x17]
0x1267484d0   910  360fc5d1       tbz w17, #1, #-0x748 (addr 0x126747d88)
0x1267484d4   914  91007c25       add x5, x1, #0x1f (31)
0x1267484d8   918  58003450       ldr x16, pc+1672 (addr 0x0000000126748b60)
0x1267484dc   91c  d63f0200       blr x16
0x1267484e0   920  17fffe2a       b #-0x758 (addr 0x126747d88)
0x1267484e4   924  d4200000       brk #0x0
0x1267484e8   928  926eb411       and x17, x0, #0xfffffffffffc0000
0x1267484ec   92c  f9400231       ldr x17, [x17]
0x1267484f0   930  360fc571       tbz w17, #1, #-0x754 (addr 0x126747d9c)
0x1267484f4   934  d1000425       sub x5, x1, #0x1 (1)
0x1267484f8   938  58003350       ldr x16, pc+1640 (addr 0x0000000126748b60)
0x1267484fc   93c  d63f0200       blr x16
0x126748500   940  17fffe27       b #-0x764 (addr 0x126747d9c)
0x126748504   944  d4200000       brk #0x0
0x126748508   948  580031d0       ldr x16, pc+1592 (addr 0x0000000126748b40)    ;; object: 0x1dadb5f42671 <String[8]: #TreeNode>
0x12674850c   94c  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x126748510   950  580031db       ldr cp, pc+1592 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x126748514   954  d2800020       movz x0, #0x1
0x126748518   958  d29b9e81       movz x1, #0xdcf4
0x12674851c   95c  f2a06081       movk x1, #0x304, lsl #16
0x126748520   960  f2c00021       movk x1, #0x1, lsl #32
0x126748524   964  580032b0       ldr x16, pc+1620 (addr 0x0000000126748b78)
0x126748528   968  d63f0200       blr x16
0x12674852c   96c  d4200000       brk #0x0
0x126748530   970  d4200000       brk #0x0
0x126748534   974  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748538   978  a9bf0be3       stp x3, x2, [sp, #-16]!
0x12674853c   97c  a9bf13e5       stp x5, x4, [sp, #-16]!
0x126748540   980  a9bf1bff       stp xzr, x6, [sp, #-16]!
0x126748544   984  52800501       movz w1, #0x28
0x126748548   988  58003150       ldr x16, pc+1576 (addr 0x0000000126748b70)
0x12674854c   98c  d63f0200       blr x16
0x126748550   990  aa0003e7       mov x7, x0
0x126748554   994  a8c11bff       ldp xzr, x6, [sp], #16
0x126748558   998  a8c113e5       ldp x5, x4, [sp], #16
0x12674855c   99c  a8c10be3       ldp x3, x2, [sp], #16
0x126748560   9a0  a8c103e1       ldp x1, x0, [sp], #16
0x126748564   9a4  17fffe26       b #-0x768 (addr 0x126747dfc)
0x126748568   9a8  d4200000       brk #0x0
0x12674856c   9ac  926eb571       and x17, x11, #0xfffffffffffc0000
0x126748570   9b0  f9400231       ldr x17, [x17]
0x126748574   9b4  360fc651       tbz w17, #1, #-0x738 (addr 0x126747e3c)
0x126748578   9b8  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x12674857c   9bc  d1000425       sub x5, x1, #0x1 (1)
0x126748580   9c0  58002f10       ldr x16, pc+1504 (addr 0x0000000126748b60)
0x126748584   9c4  d63f0200       blr x16
0x126748588   9c8  a8c117ff       ldp xzr, x5, [sp], #16
0x12674858c   9cc  17fffe2c       b #-0x750 (addr 0x126747e3c)
0x126748590   9d0  d4200000       brk #0x0
0x126748594   9d4  926eb571       and x17, x11, #0xfffffffffffc0000
0x126748598   9d8  f9400231       ldr x17, [x17]
0x12674859c   9dc  360fc5d1       tbz w17, #1, #-0x748 (addr 0x126747e54)
0x1267485a0   9e0  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x1267485a4   9e4  d1000425       sub x5, x1, #0x1 (1)
0x1267485a8   9e8  58002dd0       ldr x16, pc+1464 (addr 0x0000000126748b60)
0x1267485ac   9ec  d63f0200       blr x16
0x1267485b0   9f0  a8c117ff       ldp xzr, x5, [sp], #16
0x1267485b4   9f4  17fffe28       b #-0x760 (addr 0x126747e54)
0x1267485b8   9f8  d4200000       brk #0x0
0x1267485bc   9fc  f852034c       ldur x12, [x26, #-224]
0x1267485c0   a00  eb2c63ff       cmp sp, x12
0x1267485c4   a04  540002e8       b.hi #+0x5c (addr 0x126748620)
0x1267485c8   a08  a9bf03e1       stp x1, x0, [sp, #-16]!
0x1267485cc   a0c  a9bf0be3       stp x3, x2, [sp, #-16]!
0x1267485d0   a10  a9bf13e5       stp x5, x4, [sp, #-16]!
0x1267485d4   a14  a9bf1be7       stp x7, x6, [sp, #-16]!
0x1267485d8   a18  a9bf23e9       stp x9, x8, [sp, #-16]!
0x1267485dc   a1c  a9bf2beb       stp x11, x10, [sp, #-16]!
0x1267485e0   a20  f85f03ac       ldur x12, [fp, #-16]
0x1267485e4   a24  a9bf7fec       stp x12, xzr, [sp, #-16]!
0x1267485e8   a28  58002b1b       ldr cp, pc+1376 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267485ec   a2c  d2800020       movz x0, #0x1
0x1267485f0   a30  d29da101       movz x1, #0xed08
0x1267485f4   a34  f2a06081       movk x1, #0x304, lsl #16
0x1267485f8   a38  f2c00021       movk x1, #0x1, lsl #32
0x1267485fc   a3c  58002bf0       ldr x16, pc+1404 (addr 0x0000000126748b78)
0x126748600   a40  d63f0200       blr x16
0x126748604   a44  a8c12beb       ldp x11, x10, [sp], #16
0x126748608   a48  a8c123e9       ldp x9, x8, [sp], #16
0x12674860c   a4c  a8c11be7       ldp x7, x6, [sp], #16
0x126748610   a50  a8c113e5       ldp x5, x4, [sp], #16
0x126748614   a54  a8c10be3       ldp x3, x2, [sp], #16
0x126748618   a58  a8c103e1       ldp x1, x0, [sp], #16
0x12674861c   a5c  17fffe6c       b #-0x650 (addr 0x126747fcc)
0x126748620   a60  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748624   a64  a9bf0be3       stp x3, x2, [sp, #-16]!
0x126748628   a68  a9bf13e5       stp x5, x4, [sp, #-16]!
0x12674862c   a6c  a9bf1be7       stp x7, x6, [sp, #-16]!
0x126748630   a70  a9bf23e9       stp x9, x8, [sp, #-16]!
0x126748634   a74  a9bf2beb       stp x11, x10, [sp, #-16]!
0x126748638   a78  f85f03ac       ldur x12, [fp, #-16]
0x12674863c   a7c  a9bf7fec       stp x12, xzr, [sp, #-16]!
0x126748640   a80  5800285b       ldr cp, pc+1288 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x126748644   a84  d2800020       movz x0, #0x1
0x126748648   a88  d29d9b01       movz x1, #0xecd8
0x12674864c   a8c  f2a06081       movk x1, #0x304, lsl #16
0x126748650   a90  f2c00021       movk x1, #0x1, lsl #32
0x126748654   a94  58002930       ldr x16, pc+1316 (addr 0x0000000126748b78)
0x126748658   a98  d63f0200       blr x16
0x12674865c   a9c  a8c12beb       ldp x11, x10, [sp], #16
0x126748660   aa0  a8c123e9       ldp x9, x8, [sp], #16
0x126748664   aa4  a8c11be7       ldp x7, x6, [sp], #16
0x126748668   aa8  a8c113e5       ldp x5, x4, [sp], #16
0x12674866c   aac  a8c10be3       ldp x3, x2, [sp], #16
0x126748670   ab0  a8c103e1       ldp x1, x0, [sp], #16
0x126748674   ab4  17fffe56       b #-0x6a8 (addr 0x126747fcc)
0x126748678   ab8  d4200000       brk #0x0
0x12674867c   abc  f846718d       ldur x13, [x12, #103]
0x126748680   ac0  71000dbf       cmp w13, #0x3 (3)
0x126748684   ac4  54000140       b.eq #+0x28 (addr 0x1267486ac)
0x126748688   ac8  927ef9ad       and x13, x13, #0xfffffffffffffffd
0x12674868c   acc  f84071ad       ldur x13, [x13, #7]
0x126748690   ad0  b84331b0       ldur w16, [x13, #51]
0x126748694   ad4  37300090       tbnz w16, #6, #+0x10 (addr 0x1267486a4)
0x126748698   ad8  b84331b0       ldur w16, [x13, #51]
0x12674869c   adc  37200270       tbnz w16, #4, #+0x4c (addr 0x1267486e8)
0x1267486a0   ae0  14000003       b #+0xc (addr 0x1267486ac)
0x1267486a4   ae4  d280006d       movz x13, #0x3
0x1267486a8   ae8  f806718d       stur x13, [x12, #103]
0x1267486ac   aec  d280000d       movz x13, #0x0
0x1267486b0   af0  3940518c       ldrb w12, [x12, #20]
0x1267486b4   af4  d340098c       ubfx x12, x12, #0, #3
0x1267486b8   af8  b4ffc92c       cbz x12, #-0x6dc (addr 0x126747fdc)
0x1267486bc   afc  d2c004d0       movz x16, #0x2600000000
0x1267486c0   b00  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x1267486c4   b04  5800243b       ldr cp, pc+1156 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267486c8   b08  d2800020       movz x0, #0x1
0x1267486cc   b0c  d28f6501       movz x1, #0x7b28
0x1267486d0   b10  f2a06081       movk x1, #0x304, lsl #16
0x1267486d4   b14  f2c00021       movk x1, #0x1, lsl #32
0x1267486d8   b18  58002510       ldr x16, pc+1184 (addr 0x0000000126748b78)
0x1267486dc   b1c  d63f0200       blr x16
0x1267486e0   b20  aa0003ed       mov x13, x0
0x1267486e4   b24  34ffc7cd       cbz w13, #-0x708 (addr 0x126747fdc)
0x1267486e8   b28  14000153       b #+0x54c (addr 0x126748c34)
0x1267486ec   b2c  d4200000       brk #0x0
0x1267486f0   b30  58002290       ldr x16, pc+1104 (addr 0x0000000126748b40)    ;; object: 0x1dadb5f42671 <String[8]: #TreeNode>
0x1267486f4   b34  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x1267486f8   b38  5800229b       ldr cp, pc+1104 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267486fc   b3c  d2800020       movz x0, #0x1
0x126748700   b40  d29b9e81       movz x1, #0xdcf4
0x126748704   b44  f2a06081       movk x1, #0x304, lsl #16
0x126748708   b48  f2c00021       movk x1, #0x1, lsl #32
0x12674870c   b4c  58002370       ldr x16, pc+1132 (addr 0x0000000126748b78)
0x126748710   b50  d63f0200       blr x16
0x126748714   b54  d4200000       brk #0x0
0x126748718   b58  d4200000       brk #0x0
0x12674871c   b5c  1e62015e       scvtf d30, w10
0x126748720   b60  f85d0349       ldur x9, [x26, #-48]
0x126748724   b64  91004129       add x9, x9, #0x10 (16)
0x126748728   b68  f85d8350       ldur x16, [x26, #-40]
0x12674872c   b6c  eb10013f       cmp x9, x16
0x126748730   b70  54001aa2       b.hs #+0x354 (addr 0x126748a84)
0x126748734   b74  f81d0349       stur x9, [x26, #-48]
0x126748738   b78  d1003d29       sub x9, x9, #0xf (15)
0x12674873c   b7c  f9412750       ldr x16, [x26, #584]
0x126748740   b80  f81ff130       stur x16, [x9, #-1]
0x126748744   b84  fc00713e       stur d30, [x9, #7]
0x126748748   b88  17fffe45       b #-0x6ec (addr 0x12674805c)
0x12674874c   b8c  d4200000       brk #0x0
0x126748750   b90  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748754   b94  52800501       movz w1, #0x28
0x126748758   b98  580020d0       ldr x16, pc+1048 (addr 0x0000000126748b70)
0x12674875c   b9c  d63f0200       blr x16
0x126748760   ba0  aa0003e2       mov x2, x0
0x126748764   ba4  a8c103e1       ldp x1, x0, [sp], #16
0x126748768   ba8  17fffe68       b #-0x660 (addr 0x126748108)
0x12674876c   bac  d4200000       brk #0x0
0x126748770   bb0  926eb4b1       and x17, x5, #0xfffffffffffc0000
0x126748774   bb4  f9400231       ldr x17, [x17]
0x126748778   bb8  360fce91       tbz w17, #1, #-0x630 (addr 0x126748148)
0x12674877c   bbc  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x126748780   bc0  91005c25       add x5, x1, #0x17 (23)
0x126748784   bc4  58001ef0       ldr x16, pc+988 (addr 0x0000000126748b60)
0x126748788   bc8  d63f0200       blr x16
0x12674878c   bcc  a8c117ff       ldp xzr, x5, [sp], #16
0x126748790   bd0  17fffe6e       b #-0x648 (addr 0x126748148)
0x126748794   bd4  d4200000       brk #0x0
0x126748798   bd8  926eb4d1       and x17, x6, #0xfffffffffffc0000
0x12674879c   bdc  f9400231       ldr x17, [x17]
0x1267487a0   be0  360fcdf1       tbz w17, #1, #-0x644 (addr 0x12674815c)
0x1267487a4   be4  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x1267487a8   be8  d1000425       sub x5, x1, #0x1 (1)
0x1267487ac   bec  58001db0       ldr x16, pc+948 (addr 0x0000000126748b60)
0x1267487b0   bf0  d63f0200       blr x16
0x1267487b4   bf4  a8c117ff       ldp xzr, x5, [sp], #16
0x1267487b8   bf8  17fffe69       b #-0x65c (addr 0x12674815c)
0x1267487bc   bfc  d4200000       brk #0x0
0x1267487c0   c00  926eb411       and x17, x0, #0xfffffffffffc0000
0x1267487c4   c04  f9400231       ldr x17, [x17]
0x1267487c8   c08  360fcd71       tbz w17, #1, #-0x654 (addr 0x126748174)
0x1267487cc   c0c  91007c25       add x5, x1, #0x1f (31)
0x1267487d0   c10  58001c90       ldr x16, pc+912 (addr 0x0000000126748b60)
0x1267487d4   c14  d63f0200       blr x16
0x1267487d8   c18  17fffe67       b #-0x664 (addr 0x126748174)
0x1267487dc   c1c  d4200000       brk #0x0
0x1267487e0   c20  926eb411       and x17, x0, #0xfffffffffffc0000
0x1267487e4   c24  f9400231       ldr x17, [x17]
0x1267487e8   c28  360fcd11       tbz w17, #1, #-0x660 (addr 0x126748188)
0x1267487ec   c2c  d1000425       sub x5, x1, #0x1 (1)
0x1267487f0   c30  58001b90       ldr x16, pc+880 (addr 0x0000000126748b60)
0x1267487f4   c34  d63f0200       blr x16
0x1267487f8   c38  17fffe64       b #-0x670 (addr 0x126748188)
0x1267487fc   c3c  d4200000       brk #0x0
0x126748800   c40  58001a10       ldr x16, pc+832 (addr 0x0000000126748b40)    ;; object: 0x1dadb5f42671 <String[8]: #TreeNode>
0x126748804   c44  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x126748808   c48  58001a1b       ldr cp, pc+832 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x12674880c   c4c  d2800020       movz x0, #0x1
0x126748810   c50  d29b9e81       movz x1, #0xdcf4
0x126748814   c54  f2a06081       movk x1, #0x304, lsl #16
0x126748818   c58  f2c00021       movk x1, #0x1, lsl #32
0x12674881c   c5c  58001af0       ldr x16, pc+860 (addr 0x0000000126748b78)
0x126748820   c60  d63f0200       blr x16
0x126748824   c64  d4200000       brk #0x0
0x126748828   c68  d4200000       brk #0x0
0x12674882c   c6c  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748830   c70  a9bf0be3       stp x3, x2, [sp, #-16]!
0x126748834   c74  a9bf13e5       stp x5, x4, [sp, #-16]!
0x126748838   c78  a9bf1be7       stp x7, x6, [sp, #-16]!
0x12674883c   c7c  52800501       movz w1, #0x28
0x126748840   c80  58001990       ldr x16, pc+816 (addr 0x0000000126748b70)
0x126748844   c84  d63f0200       blr x16
0x126748848   c88  aa0003e8       mov x8, x0
0x12674884c   c8c  a8c11be7       ldp x7, x6, [sp], #16
0x126748850   c90  a8c113e5       ldp x5, x4, [sp], #16
0x126748854   c94  a8c10be3       ldp x3, x2, [sp], #16
0x126748858   c98  a8c103e1       ldp x1, x0, [sp], #16
0x12674885c   c9c  17fffe64       b #-0x670 (addr 0x1267481ec)
0x126748860   ca0  d4200000       brk #0x0
0x126748864   ca4  926eb591       and x17, x12, #0xfffffffffffc0000
0x126748868   ca8  f9400231       ldr x17, [x17]
0x12674886c   cac  360fce11       tbz w17, #1, #-0x640 (addr 0x12674822c)
0x126748870   cb0  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x126748874   cb4  d1000425       sub x5, x1, #0x1 (1)
0x126748878   cb8  58001750       ldr x16, pc+744 (addr 0x0000000126748b60)
0x12674887c   cbc  d63f0200       blr x16
0x126748880   cc0  a8c117ff       ldp xzr, x5, [sp], #16
0x126748884   cc4  17fffe6a       b #-0x658 (addr 0x12674822c)
0x126748888   cc8  d4200000       brk #0x0
0x12674888c   ccc  926eb591       and x17, x12, #0xfffffffffffc0000
0x126748890   cd0  f9400231       ldr x17, [x17]
0x126748894   cd4  360fcd91       tbz w17, #1, #-0x650 (addr 0x126748244)
0x126748898   cd8  a9bf17ff       stp xzr, x5, [sp, #-16]!
0x12674889c   cdc  d1000425       sub x5, x1, #0x1 (1)
0x1267488a0   ce0  58001610       ldr x16, pc+704 (addr 0x0000000126748b60)
0x1267488a4   ce4  d63f0200       blr x16
0x1267488a8   ce8  a8c117ff       ldp xzr, x5, [sp], #16
0x1267488ac   cec  17fffe66       b #-0x668 (addr 0x126748244)
0x1267488b0   cf0  d4200000       brk #0x0
0x1267488b4   cf4  f852034f       ldur x15, [x26, #-224]
0x1267488b8   cf8  eb2f63ff       cmp sp, x15
0x1267488bc   cfc  54000368       b.hi #+0x6c (addr 0x126748928)
0x1267488c0   d00  a9bf03e1       stp x1, x0, [sp, #-16]!
0x1267488c4   d04  a9bf0be3       stp x3, x2, [sp, #-16]!
0x1267488c8   d08  a9bf13e5       stp x5, x4, [sp, #-16]!
0x1267488cc   d0c  a9bf1be7       stp x7, x6, [sp, #-16]!
0x1267488d0   d10  a9bf23e9       stp x9, x8, [sp, #-16]!
0x1267488d4   d14  a9bf2beb       stp x11, x10, [sp, #-16]!
0x1267488d8   d18  a9bf33ed       stp x13, x12, [sp, #-16]!
0x1267488dc   d1c  a9bf3bff       stp xzr, x14, [sp, #-16]!
0x1267488e0   d20  f85f03af       ldur x15, [fp, #-16]
0x1267488e4   d24  a9bf7fef       stp x15, xzr, [sp, #-16]!
0x1267488e8   d28  5800131b       ldr cp, pc+608 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267488ec   d2c  d2800020       movz x0, #0x1
0x1267488f0   d30  d29da101       movz x1, #0xed08
0x1267488f4   d34  f2a06081       movk x1, #0x304, lsl #16
0x1267488f8   d38  f2c00021       movk x1, #0x1, lsl #32
0x1267488fc   d3c  580013f0       ldr x16, pc+636 (addr 0x0000000126748b78)
0x126748900   d40  d63f0200       blr x16
0x126748904   d44  a8c13bff       ldp xzr, x14, [sp], #16
0x126748908   d48  a8c133ed       ldp x13, x12, [sp], #16
0x12674890c   d4c  a8c12beb       ldp x11, x10, [sp], #16
0x126748910   d50  a8c123e9       ldp x9, x8, [sp], #16
0x126748914   d54  a8c11be7       ldp x7, x6, [sp], #16
0x126748918   d58  a8c113e5       ldp x5, x4, [sp], #16
0x12674891c   d5c  a8c10be3       ldp x3, x2, [sp], #16
0x126748920   d60  a8c103e1       ldp x1, x0, [sp], #16
0x126748924   d64  17fffea5       b #-0x56c (addr 0x1267483b8)
0x126748928   d68  a9bf03e1       stp x1, x0, [sp, #-16]!
0x12674892c   d6c  a9bf0be3       stp x3, x2, [sp, #-16]!
0x126748930   d70  a9bf13e5       stp x5, x4, [sp, #-16]!
0x126748934   d74  a9bf1be7       stp x7, x6, [sp, #-16]!
0x126748938   d78  a9bf23e9       stp x9, x8, [sp, #-16]!
0x12674893c   d7c  a9bf2beb       stp x11, x10, [sp, #-16]!
0x126748940   d80  a9bf33ed       stp x13, x12, [sp, #-16]!
0x126748944   d84  a9bf3bff       stp xzr, x14, [sp, #-16]!
0x126748948   d88  f85f03af       ldur x15, [fp, #-16]
0x12674894c   d8c  a9bf7fef       stp x15, xzr, [sp, #-16]!
0x126748950   d90  58000fdb       ldr cp, pc+504 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x126748954   d94  d2800020       movz x0, #0x1
0x126748958   d98  d29d9b01       movz x1, #0xecd8
0x12674895c   d9c  f2a06081       movk x1, #0x304, lsl #16
0x126748960   da0  f2c00021       movk x1, #0x1, lsl #32
0x126748964   da4  580010b0       ldr x16, pc+532 (addr 0x0000000126748b78)
0x126748968   da8  d63f0200       blr x16
0x12674896c   dac  a8c13bff       ldp xzr, x14, [sp], #16
0x126748970   db0  a8c133ed       ldp x13, x12, [sp], #16
0x126748974   db4  a8c12beb       ldp x11, x10, [sp], #16
0x126748978   db8  a8c123e9       ldp x9, x8, [sp], #16
0x12674897c   dbc  a8c11be7       ldp x7, x6, [sp], #16
0x126748980   dc0  a8c113e5       ldp x5, x4, [sp], #16
0x126748984   dc4  a8c10be3       ldp x3, x2, [sp], #16
0x126748988   dc8  a8c103e1       ldp x1, x0, [sp], #16
0x12674898c   dcc  17fffe8b       b #-0x5d4 (addr 0x1267483b8)
0x126748990   dd0  d4200000       brk #0x0
0x126748994   dd4  f84671f3       ldur x19, [x15, #103]
0x126748998   dd8  71000e7f       cmp w19, #0x3 (3)
0x12674899c   ddc  54000140       b.eq #+0x28 (addr 0x1267489c4)
0x1267489a0   de0  927efa73       and x19, x19, #0xfffffffffffffffd
0x1267489a4   de4  f8407273       ldur x19, [x19, #7]
0x1267489a8   de8  b8433270       ldur w16, [x19, #51]
0x1267489ac   dec  37300090       tbnz w16, #6, #+0x10 (addr 0x1267489bc)
0x1267489b0   df0  b8433270       ldur w16, [x19, #51]
0x1267489b4   df4  37200270       tbnz w16, #4, #+0x4c (addr 0x126748a00)
0x1267489b8   df8  14000003       b #+0xc (addr 0x1267489c4)
0x1267489bc   dfc  d2800073       movz x19, #0x3
0x1267489c0   e00  f80671f3       stur x19, [x15, #103]
0x1267489c4   e04  d2800013       movz x19, #0x0
0x1267489c8   e08  394051ef       ldrb w15, [x15, #20]
0x1267489cc   e0c  d34009ef       ubfx x15, x15, #0, #3
0x1267489d0   e10  b4ffcfcf       cbz x15, #-0x608 (addr 0x1267483c8)
0x1267489d4   e14  d2c004d0       movz x16, #0x2600000000
0x1267489d8   e18  a9bf7ff0       stp x16, xzr, [sp, #-16]!
0x1267489dc   e1c  58000b7b       ldr cp, pc+364 (addr 0x0000000126748b48)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267489e0   e20  d2800020       movz x0, #0x1
0x1267489e4   e24  d28f6501       movz x1, #0x7b28
0x1267489e8   e28  f2a06081       movk x1, #0x304, lsl #16
0x1267489ec   e2c  f2c00021       movk x1, #0x1, lsl #32
0x1267489f0   e30  58000c50       ldr x16, pc+392 (addr 0x0000000126748b78)
0x1267489f4   e34  d63f0200       blr x16
0x1267489f8   e38  aa0003f3       mov x19, x0
0x1267489fc   e3c  34ffce73       cbz w19, #-0x634 (addr 0x1267483c8)
0x126748a00   e40  1400008e       b #+0x238 (addr 0x126748c38)
0x126748a04   e44  d4200000       brk #0x0
0x126748a08   e48  1e62001e       scvtf d30, w0
0x126748a0c   e4c  f85d0341       ldur x1, [x26, #-48]
0x126748a10   e50  91004021       add x1, x1, #0x10 (16)
0x126748a14   e54  f85d8350       ldur x16, [x26, #-40]
0x126748a18   e58  eb10003f       cmp x1, x16
0x126748a1c   e5c  54000582       b.hs #+0xb0 (addr 0x126748acc)
0x126748a20   e60  f81d0341       stur x1, [x26, #-48]
0x126748a24   e64  d1003c21       sub x1, x1, #0xf (15)
0x126748a28   e68  f9412750       ldr x16, [x26, #584]
0x126748a2c   e6c  f81ff030       stur x16, [x1, #-1]
0x126748a30   e70  fc00703e       stur d30, [x1, #7]
0x126748a34   e74  17fffe69       b #-0x65c (addr 0x1267483d8)
0x126748a38   e78  d4200000       brk #0x0
0x126748a3c   e7c  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748a40   e80  a9bf0be3       stp x3, x2, [sp, #-16]!
0x126748a44   e84  a9bf13e5       stp x5, x4, [sp, #-16]!
0x126748a48   e88  a9bf1be8       stp x8, x6, [sp, #-16]!
0x126748a4c   e8c  a9bf6fff       stp xzr, cp, [sp, #-16]!
0x126748a50   e90  6dbf7bef       stp d15, d30, [sp, #-16]!
0x126748a54   e94  52800201       movz w1, #0x10
0x126748a58   e98  580008d0       ldr x16, pc+280 (addr 0x0000000126748b70)
0x126748a5c   e9c  d63f0200       blr x16
0x126748a60   ea0  aa0003e7       mov x7, x0
0x126748a64   ea4  6cc17bef       ldp d15, d30, [sp], #16
0x126748a68   ea8  a8c16fff       ldp xzr, cp, [sp], #16
0x126748a6c   eac  a8c11be8       ldp x8, x6, [sp], #16
0x126748a70   eb0  a8c113e5       ldp x5, x4, [sp], #16
0x126748a74   eb4  a8c10be3       ldp x3, x2, [sp], #16
0x126748a78   eb8  a8c103e1       ldp x1, x0, [sp], #16
0x126748a7c   ebc  17fffe72       b #-0x638 (addr 0x126748444)
0x126748a80   ec0  d4200000       brk #0x0
0x126748a84   ec4  a9bf03e1       stp x1, x0, [sp, #-16]!
0x126748a88   ec8  a9bf0be3       stp x3, x2, [sp, #-16]!
0x126748a8c   ecc  a9bf13e5       stp x5, x4, [sp, #-16]!
0x126748a90   ed0  a9bf1be7       stp x7, x6, [sp, #-16]!
0x126748a94   ed4  a9bf23ea       stp x10, x8, [sp, #-16]!
0x126748a98   ed8  6dbf7bef       stp d15, d30, [sp, #-16]!
0x126748a9c   edc  52800201       movz w1, #0x10
0x126748aa0   ee0  58000690       ldr x16, pc+208 (addr 0x0000000126748b70)
0x126748aa4   ee4  d63f0200       blr x16
0x126748aa8   ee8  aa0003e9       mov x9, x0
0x126748aac   eec  6cc17bef       ldp d15, d30, [sp], #16
0x126748ab0   ef0  a8c123ea       ldp x10, x8, [sp], #16
0x126748ab4   ef4  a8c11be7       ldp x7, x6, [sp], #16
0x126748ab8   ef8  a8c113e5       ldp x5, x4, [sp], #16
0x126748abc   efc  a8c10be3       ldp x3, x2, [sp], #16
0x126748ac0   f00  a8c103e1       ldp x1, x0, [sp], #16
0x126748ac4   f04  17ffff1e       b #-0x388 (addr 0x12674873c)
0x126748ac8   f08  d4200000       brk #0x0
0x126748acc   f0c  6dbf7bef       stp d15, d30, [sp, #-16]!
0x126748ad0   f10  52800201       movz w1, #0x10
0x126748ad4   f14  580004f0       ldr x16, pc+156 (addr 0x0000000126748b70)
0x126748ad8   f18  d63f0200       blr x16
0x126748adc   f1c  aa0003e1       mov x1, x0
0x126748ae0   f20  6cc17bef       ldp d15, d30, [sp], #16
0x126748ae4   f24  17ffffd1       b #-0xbc (addr 0x126748a28)
0x126748ae8   f28  d4200000       brk #0x0
0x126748aec   f2c  5800049f       constant pool begin (num_const = 36)    ;; constant pool
0x126748af0   f30  d63f03e0       constant
0x126748af4   f34  d503201f       constant
0x126748af8   f38  b5f4b821       constant
0x126748afc   f3c  00001dad       constant
0x126748b00   f40  b5f4b861       constant
0x126748b04   f44  00001dad       constant
0x126748b08   f48  b5f4b8f9       constant
0x126748b0c   f4c  00001dad       constant
0x126748b10   f50  b5f49181       constant
0x126748b14   f54  00001dad       constant
0x126748b18   f58  b5f49201       constant
0x126748b1c   f5c  00001dad       constant
0x126748b20   f60  b5f49259       constant
0x126748b24   f64  00001dad       constant
0x126748b28   f68  b5f4b951       constant
0x126748b2c   f6c  00001dad       constant
0x126748b30   f70  b5f42bd1       constant
0x126748b34   f74  00001dad       constant
0x126748b38   f78  cf638021       constant
0x126748b3c   f7c  000018dd       constant
0x126748b40   f80  b5f42671       constant
0x126748b44   f84  00001dad       constant
0x126748b48   f88  24400109       constant
0x126748b4c   f8c  00002347       constant
0x126748b50   f90  002c4600       constant
0x126748b54   f94  00000000       constant
0x126748b58   f98  002c4700       constant
0x126748b5c   f9c  00000000       constant
0x126748b60   fa0  035fce40       constant
0x126748b64   fa4  00000001       constant
0x126748b68   fa8  03609ba0       constant
0x126748b6c   fac  00000001       constant
0x126748b70   fb0  0360ace0       constant
0x126748b74   fb4  00000001       constant
0x126748b78   fb8  036a61e0       constant
0x126748b7c   fbc  00000001       constant
0x126748b80   fc0  f8558350       ldur x16, [x26, #-168]
0x126748b84   fc4  d61f0200       br x16
0x126748b88   fc8  f8560350       ldur x16, [x26, #-160]
0x126748b8c   fcc  d61f0200       br x16
0x126748b90   fd0  97fffffc       bl #-0x10 (addr 0x126748b80)    ;; debug: deopt position, script offset '404'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x126748b94   fd4  97fffffb       bl #-0x14 (addr 0x126748b80)    ;; debug: deopt position, script offset '404'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 1
0x126748b98   fd8  97fffffa       bl #-0x18 (addr 0x126748b80)    ;; debug: deopt position, script offset '404'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 2
0x126748b9c   fdc  97fffff9       bl #-0x1c (addr 0x126748b80)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 3
0x126748ba0   fe0  97fffff8       bl #-0x20 (addr 0x126748b80)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 4
0x126748ba4   fe4  97fffff7       bl #-0x24 (addr 0x126748b80)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 5
0x126748ba8   fe8  97fffff6       bl #-0x28 (addr 0x126748b80)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 6
0x126748bac   fec  97fffff5       bl #-0x2c (addr 0x126748b80)    ;; debug: deopt position, script offset '5f3'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong call target constructor'
                                                             ;; debug: deopt index 7
0x126748bb0   ff0  97fffff4       bl #-0x30 (addr 0x126748b80)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 8
0x126748bb4   ff4  97fffff3       bl #-0x34 (addr 0x126748b80)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 9
0x126748bb8   ff8  97fffff2       bl #-0x38 (addr 0x126748b80)    ;; debug: deopt position, script offset '63c'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong call target constructor'
                                                             ;; debug: deopt index a
0x126748bbc   ffc  97fffff1       bl #-0x3c (addr 0x126748b80)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index b
0x126748bc0  1000  97fffff0       bl #-0x40 (addr 0x126748b80)    ;; debug: deopt position, script offset '536'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index c
0x126748bc4  1004  97ffffef       bl #-0x44 (addr 0x126748b80)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index d
0x126748bc8  1008  97ffffee       bl #-0x48 (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index e
0x126748bcc  100c  97ffffed       bl #-0x4c (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index f
0x126748bd0  1010  97ffffec       bl #-0x50 (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 10
0x126748bd4  1014  97ffffeb       bl #-0x54 (addr 0x126748b80)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 11
0x126748bd8  1018  97ffffea       bl #-0x58 (addr 0x126748b80)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 12
0x126748bdc  101c  97ffffe9       bl #-0x5c (addr 0x126748b80)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 13
0x126748be0  1020  97ffffe8       bl #-0x60 (addr 0x126748b80)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 14
0x126748be4  1024  97ffffe7       bl #-0x64 (addr 0x126748b80)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 15
0x126748be8  1028  97ffffe6       bl #-0x68 (addr 0x126748b80)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 16
0x126748bec  102c  97ffffe5       bl #-0x6c (addr 0x126748b80)    ;; debug: deopt position, script offset '613'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 17
0x126748bf0  1030  97ffffe4       bl #-0x70 (addr 0x126748b80)    ;; debug: deopt position, script offset '613'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 18
0x126748bf4  1034  97ffffe3       bl #-0x74 (addr 0x126748b80)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 19
0x126748bf8  1038  97ffffe2       bl #-0x78 (addr 0x126748b80)    ;; debug: deopt position, script offset '5f3'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason 'wrong call target constructor'
                                                             ;; debug: deopt index 1a
0x126748bfc  103c  97ffffe1       bl #-0x7c (addr 0x126748b80)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id '5'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 1b
0x126748c00  1040  97ffffe0       bl #-0x80 (addr 0x126748b80)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id '5'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 1c
0x126748c04  1044  97ffffdf       bl #-0x84 (addr 0x126748b80)    ;; debug: deopt position, script offset '63c'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason 'wrong call target constructor'
                                                             ;; debug: deopt index 1d
0x126748c08  1048  97ffffde       bl #-0x88 (addr 0x126748b80)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 1e
0x126748c0c  104c  97ffffdd       bl #-0x8c (addr 0x126748b80)    ;; debug: deopt position, script offset '536'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 1f
0x126748c10  1050  97ffffdc       bl #-0x90 (addr 0x126748b80)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 20
0x126748c14  1054  97ffffdb       bl #-0x94 (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 21
0x126748c18  1058  97ffffda       bl #-0x98 (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 22
0x126748c1c  105c  97ffffd9       bl #-0x9c (addr 0x126748b80)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 23
0x126748c20  1060  97ffffd8       bl #-0xa0 (addr 0x126748b80)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 24
0x126748c24  1064  97ffffd7       bl #-0xa4 (addr 0x126748b80)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 25
0x126748c28  1068  97ffffd6       bl #-0xa8 (addr 0x126748b80)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 26
0x126748c2c  106c  97ffffd5       bl #-0xac (addr 0x126748b80)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 27
0x126748c30  1070  97ffffd4       bl #-0xb0 (addr 0x126748b80)    ;; debug: deopt position, script offset '454'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Insufficient type feedback for generic global access'
                                                             ;; debug: deopt index 28
0x126748c34  1074  97ffffd3       bl #-0xb4 (addr 0x126748b80)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'prepare for on stack replacement (OSR)'
                                                             ;; debug: deopt index 29
0x126748c38  1078  97ffffd2       bl #-0xb8 (addr 0x126748b80)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'prepare for on stack replacement (OSR)'
                                                             ;; debug: deopt index 2a
0x126748c3c  107c  97ffffd3       bl #-0xb4 (addr 0x126748b88)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2b
0x126748c40  1080  97ffffd2       bl #-0xb8 (addr 0x126748b88)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2c
0x126748c44  1084  97ffffd1       bl #-0xbc (addr 0x126748b88)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2d
0x126748c48  1088  97ffffd0       bl #-0xc0 (addr 0x126748b88)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id '3'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2e
0x126748c4c  108c  97ffffcf       bl #-0xc4 (addr 0x126748b88)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 2f
0x126748c50  1090  97ffffce       bl #-0xc8 (addr 0x126748b88)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 30
0x126748c54  1094  97ffffcd       bl #-0xcc (addr 0x126748b88)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 31
0x126748c58  1098  97ffffcc       bl #-0xd0 (addr 0x126748b88)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id '7'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 32
0x126748c5c  109c  97ffffcb       bl #-0xd4 (addr 0x126748b88)    ;; debug: deopt position, script offset '3c5'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 33
0x126748c60  10a0  97ffffca       bl #-0xd8 (addr 0x126748b88)    ;; debug: deopt position, script offset '5f7'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 34
0x126748c64  10a4  97ffffc9       bl #-0xdc (addr 0x126748b88)    ;; debug: deopt position, script offset '640'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 35
0x126748c68  10a8  97ffffc8       bl #-0xe0 (addr 0x126748b88)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 36
0x126748c6c  10ac  97ffffc7       bl #-0xe4 (addr 0x126748b88)    ;; debug: deopt position, script offset '5f7'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 37
0x126748c70  10b0  97ffffc6       bl #-0xe8 (addr 0x126748b88)    ;; debug: deopt position, script offset '640'
                                                             ;; debug: deopt position, inlining id '4'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 38
0x126748c74  10b4  97ffffc5       bl #-0xec (addr 0x126748b88)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 39

Inlined functions (count = 3)
 0x1dadb5f42991 <SharedFunctionInfo bottomUpTree>
 0x1dadb5f429d9 <SharedFunctionInfo TreeNode>
 0x1dadb5f42949 <SharedFunctionInfo itemCheck>

Deoptimization Input Data (deopt points = 58)
 index  bytecode-offset    pc
     0                6   fd0 
     1                6   fd4 
     2                6   fd8 
     3                1   fdc 
     4                1   fe0 
     5                1   fe4 
     6               34   fe8 
     7               41   fec 
     8                2   ff0 
     9                8   ff4 
    10               59   ff8 
    11               22   ffc 
    12                0  1000 
    13               26  1004 
    14               30  1008 
    15               30  100c 
    16               30  1010 
    17               46  1014 
    18               46  1018 
    19               26  101c 
    20               26  1020 
    21               26  1024 
    22                6  1028 
    23               16  102c 
    24               16  1030 
    25               34  1034 
    26               41  1038 
    27                2  103c 
    28                8  1040 
    29               59  1044 
    30               22  1048 
    31                0  104c 
    32               26  1050 
    33               30  1054 
    34               30  1058 
    35               30  105c 
    36               46  1060 
    37               46  1064 
    38               26  1068 
    39               26  106c 
    40               42  1070 
    41               26  1074 
    42               26  1078 
    43               20  107c 
    44               34  1080 
    45               26  1084 
    46               42  1088 
    47               20  108c 
    48               34  1090 
    49               26  1094 
    50               42  1098 
    51               38  109c 
    52                8  10a0 
    53               50  10a4 
    54               38  10a8 
    55                8  10ac 
    56               50  10b0 
    57               38  10b4 

Safepoints (stack slots = 22, entries = 26, byte size = 224, tagged slots = 7)
0x126747ca4     e4  num extra spill slots: 0  deopt     43 trampoline:   107c
0x126747cf0    130  num extra spill slots: 0  deopt     44 trampoline:   1080
0x126747ef0    330  num extra spill slots: 0  deopt     45 trampoline:   1084
0x126747f50    390  num extra spill slots: 0  deopt     46 trampoline:   1088
0x126748090    4d0  num extra spill slots: 0  deopt     47 trampoline:   108c
0x1267480dc    51c  num extra spill slots: 0  deopt     48 trampoline:   1090
0x1267482e0    720  num extra spill slots: 0  deopt     49 trampoline:   1094
0x126748340    780  num extra spill slots: 0  deopt     50 trampoline:   1098
0x1267483f0    830  num extra spill slots: 0  deopt     51 trampoline:   109c
0x12674841c    85c  num extra spill slots: 0  deopt     52 trampoline:   10a0
0x126748468    8a8  num extra spill slots: 2  registers: 11
0x12674852c    96c  num extra spill slots: 0  deopt     53 trampoline:   10a4
0x126748550    990  num extra spill slots: 8  registers: 1001100
0x126748604    a44  num extra spill slots: 12  registers: 11101011101  deopt     54 trampoline:   10a8
0x12674865c    a9c  num extra spill slots: 12  registers: 11101011101
0x1267486e0    b20  num extra spill slots: 0
0x126748714    b54  num extra spill slots: 0  deopt     55 trampoline:   10ac
0x126748760    ba0  num extra spill slots: 2  registers: 11
0x126748824    c64  num extra spill slots: 0  deopt     56 trampoline:   10b0
0x126748848    c88  num extra spill slots: 8  registers: 10011000
0x126748904    d44  num extra spill slots: 16  registers: 100111010011000  deopt     57 trampoline:   10b4
0x12674896c    dac  num extra spill slots: 16  registers: 100111010011000
0x1267489f8    e38  num extra spill slots: 0
0x126748a60    ea0  num extra spill slots: 12  registers: 101001100
0x126748aa8    ee8  num extra spill slots: 12  registers: 110011000
0x126748adc    f1c  num extra spill slots: 2

RelocInfo (size = 1257)
0x126747c10  full embedded object  (0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>)
0x126747c38  full embedded object  (0x1dadb5f4b861 <FunctionContext[7]>)
0x126747c88  js dispatch handle (TURBOFAN_JS)  (2901760)
0x126747cf4  full embedded object  (0x1dadb5f4b8f9 <JSFunction TreeNode (sfi = 0x1dadb5f429d9)>)
0x126747d20  full embedded object  (0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>)
0x126747d5c  full embedded object  (0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>)
0x126747d88  full embedded object  (0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>)
0x126747e64  full embedded object  (0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>)
0x126747ed4  js dispatch handle (TURBOFAN_JS)  (2901504)
0x126747fb8  full embedded object  (0x1dadb5f42bd1 <FeedbackCell[one closure]>)
0x126747fcc  full embedded object  (0x18ddcf638021 <FeedbackVector[15]>)
0x1267483f8  full embedded object  (0x1dadb5f42671 <String[8]: #TreeNode>)
0x126748400  full embedded object  (0x234724400109 <NativeContext[302]>)
0x126748aec  constant pool (size 148)
0x126748b90  deopt script offset  (1028)
0x126748b90  deopt inlining id  (-1)
0x126748b90  deopt reason  (not a Smi)
0x126748b90  deopt index
0x126748b94  deopt script offset  (1028)
0x126748b94  deopt inlining id  (-1)
0x126748b94  deopt reason  (not a Smi)
0x126748b94  deopt index
0x126748b98  deopt script offset  (1028)
0x126748b98  deopt inlining id  (-1)
0x126748b98  deopt reason  (wrong call target)
0x126748b98  deopt index
0x126748b9c  deopt script offset  (1509)
0x126748b9c  deopt inlining id  (0)
0x126748b9c  deopt reason  (not a Smi)
0x126748b9c  deopt index
0x126748ba0  deopt script offset  (1509)
0x126748ba0  deopt inlining id  (0)
0x126748ba0  deopt reason  (overflow)
0x126748ba0  deopt index
0x126748ba4  deopt script offset  (1509)
0x126748ba4  deopt inlining id  (0)
0x126748ba4  deopt reason  (wrong call target)
0x126748ba4  deopt index
0x126748ba8  deopt script offset  (1561)
0x126748ba8  deopt inlining id  (0)
0x126748ba8  deopt reason  (wrong call target)
0x126748ba8  deopt index
0x126748bac  deopt script offset  (1523)
0x126748bac  deopt inlining id  (0)
0x126748bac  deopt reason  (wrong call target constructor)
0x126748bac  deopt index
0x126748bb0  deopt script offset  (1250)
0x126748bb0  deopt inlining id  (1)
0x126748bb0  deopt reason  (Smi)
0x126748bb0  deopt index
0x126748bb4  deopt script offset  (1277)
0x126748bb4  deopt inlining id  (1)
0x126748bb4  deopt reason  (Smi)
0x126748bb4  deopt index
0x126748bb8  deopt script offset  (1596)
0x126748bb8  deopt inlining id  (0)
0x126748bb8  deopt reason  (wrong call target constructor)
0x126748bb8  deopt index
0x126748bbc  deopt script offset  (1066)
0x126748bbc  deopt inlining id  (-1)
0x126748bbc  deopt reason  (wrong call target)
0x126748bbc  deopt index
0x126748bc0  deopt script offset  (1334)
0x126748bc0  deopt inlining id  (3)
0x126748bc0  deopt reason  (wrong map)
0x126748bc0  deopt index
0x126748bc4  deopt script offset  (1413)
0x126748bc4  deopt inlining id  (3)
0x126748bc4  deopt reason  (wrong call target)
0x126748bc4  deopt index
0x126748bc8  deopt script offset  (1411)
0x126748bc8  deopt inlining id  (3)
0x126748bc8  deopt reason  (not a Smi)
0x126748bc8  deopt index
0x126748bcc  deopt script offset  (1411)
0x126748bcc  deopt inlining id  (3)
0x126748bcc  deopt reason  (overflow)
0x126748bcc  deopt index
0x126748bd0  deopt script offset  (1411)
0x126748bd0  deopt inlining id  (3)
0x126748bd0  deopt reason  (wrong call target)
0x126748bd0  deopt index
0x126748bd4  deopt script offset  (1434)
0x126748bd4  deopt inlining id  (3)
0x126748bd4  deopt reason  (not a Smi)
0x126748bd4  deopt index
0x126748bd8  deopt script offset  (1434)
0x126748bd8  deopt inlining id  (3)
0x126748bd8  deopt reason  (overflow)
0x126748bd8  deopt index
0x126748bdc  deopt script offset  (1066)
0x126748bdc  deopt inlining id  (-1)
0x126748bdc  deopt reason  (not a Smi)
0x126748bdc  deopt index
0x126748be0  deopt script offset  (1066)
0x126748be0  deopt inlining id  (-1)
0x126748be0  deopt reason  (overflow)
0x126748be0  deopt index
0x126748be4  deopt script offset  (1066)
0x126748be4  deopt inlining id  (-1)
0x126748be4  deopt reason  (overflow)
0x126748be4  deopt index
0x126748be8  deopt script offset  (1010)
0x126748be8  deopt inlining id  (-1)
0x126748be8  deopt reason  (wrong call target)
0x126748be8  deopt index
0x126748bec  deopt script offset  (1555)
0x126748bec  deopt inlining id  (4)
0x126748bec  deopt reason  (overflow)
0x126748bec  deopt index
0x126748bf0  deopt script offset  (1555)
0x126748bf0  deopt inlining id  (4)
0x126748bf0  deopt reason  (wrong call target)
0x126748bf0  deopt index
0x126748bf4  deopt script offset  (1561)
0x126748bf4  deopt inlining id  (4)
0x126748bf4  deopt reason  (wrong call target)
0x126748bf4  deopt index
0x126748bf8  deopt script offset  (1523)
0x126748bf8  deopt inlining id  (4)
0x126748bf8  deopt reason  (wrong call target constructor)
0x126748bf8  deopt index
0x126748bfc  deopt script offset  (1250)
0x126748bfc  deopt inlining id  (5)
0x126748bfc  deopt reason  (Smi)
0x126748bfc  deopt index
0x126748c00  deopt script offset  (1277)
0x126748c00  deopt inlining id  (5)
0x126748c00  deopt reason  (Smi)
0x126748c00  deopt index
0x126748c04  deopt script offset  (1596)
0x126748c04  deopt inlining id  (4)
0x126748c04  deopt reason  (wrong call target constructor)
0x126748c04  deopt index
0x126748c08  deopt script offset  (1010)
0x126748c08  deopt inlining id  (-1)
0x126748c08  deopt reason  (wrong call target)
0x126748c08  deopt index
0x126748c0c  deopt script offset  (1334)
0x126748c0c  deopt inlining id  (7)
0x126748c0c  deopt reason  (wrong map)
0x126748c0c  deopt index
0x126748c10  deopt script offset  (1413)
0x126748c10  deopt inlining id  (7)
0x126748c10  deopt reason  (wrong call target)
0x126748c10  deopt index
0x126748c14  deopt script offset  (1411)
0x126748c14  deopt inlining id  (7)
0x126748c14  deopt reason  (not a Smi)
0x126748c14  deopt index
0x126748c18  deopt script offset  (1411)
0x126748c18  deopt inlining id  (7)
0x126748c18  deopt reason  (overflow)
0x126748c18  deopt index
0x126748c1c  deopt script offset  (1411)
0x126748c1c  deopt inlining id  (7)
0x126748c1c  deopt reason  (wrong call target)
0x126748c1c  deopt index
0x126748c20  deopt script offset  (1434)
0x126748c20  deopt inlining id  (7)
0x126748c20  deopt reason  (not a Smi)
0x126748c20  deopt index
0x126748c24  deopt script offset  (1434)
0x126748c24  deopt inlining id  (7)
0x126748c24  deopt reason  (overflow)
0x126748c24  deopt index
0x126748c28  deopt script offset  (1010)
0x126748c28  deopt inlining id  (-1)
0x126748c28  deopt reason  (overflow)
0x126748c28  deopt index
0x126748c2c  deopt script offset  (1010)
0x126748c2c  deopt inlining id  (-1)
0x126748c2c  deopt reason  (overflow)
0x126748c2c  deopt index
0x126748c30  deopt script offset  (1108)
0x126748c30  deopt inlining id  (-1)
0x126748c30  deopt reason  (Insufficient type feedback for generic global access)
0x126748c30  deopt index
0x126748c34  deopt script offset  (1066)
0x126748c34  deopt inlining id  (-1)
0x126748c34  deopt reason  (prepare for on stack replacement (OSR))
0x126748c34  deopt index
0x126748c38  deopt script offset  (1010)
0x126748c38  deopt inlining id  (-1)
0x126748c38  deopt reason  (prepare for on stack replacement (OSR))
0x126748c38  deopt index
0x126748c3c  deopt script offset  (1536)
0x126748c3c  deopt inlining id  (0)
0x126748c3c  deopt reason  ((unknown))
0x126748c3c  deopt index
0x126748c40  deopt script offset  (1561)
0x126748c40  deopt inlining id  (0)
0x126748c40  deopt reason  ((unknown))
0x126748c40  deopt index
0x126748c44  deopt script offset  (1413)
0x126748c44  deopt inlining id  (3)
0x126748c44  deopt reason  ((unknown))
0x126748c44  deopt index
0x126748c48  deopt script offset  (1436)
0x126748c48  deopt inlining id  (3)
0x126748c48  deopt reason  ((unknown))
0x126748c48  deopt index
0x126748c4c  deopt script offset  (1536)
0x126748c4c  deopt inlining id  (4)
0x126748c4c  deopt reason  ((unknown))
0x126748c4c  deopt index
0x126748c50  deopt script offset  (1561)
0x126748c50  deopt inlining id  (4)
0x126748c50  deopt reason  ((unknown))
0x126748c50  deopt index
0x126748c54  deopt script offset  (1413)
0x126748c54  deopt inlining id  (7)
0x126748c54  deopt reason  ((unknown))
0x126748c54  deopt index
0x126748c58  deopt script offset  (1436)
0x126748c58  deopt inlining id  (7)
0x126748c58  deopt reason  ((unknown))
0x126748c58  deopt index
0x126748c5c  deopt script offset  (965)
0x126748c5c  deopt inlining id  (-1)
0x126748c5c  deopt reason  ((unknown))
0x126748c5c  deopt index
0x126748c60  deopt script offset  (1527)
0x126748c60  deopt inlining id  (0)
0x126748c60  deopt reason  ((unknown))
0x126748c60  deopt index
0x126748c64  deopt script offset  (1600)
0x126748c64  deopt inlining id  (0)
0x126748c64  deopt reason  ((unknown))
0x126748c64  deopt index
0x126748c68  deopt script offset  (1010)
0x126748c68  deopt inlining id  (-1)
0x126748c68  deopt reason  ((unknown))
0x126748c68  deopt index
0x126748c6c  deopt script offset  (1527)
0x126748c6c  deopt inlining id  (4)
0x126748c6c  deopt reason  ((unknown))
0x126748c6c  deopt index
0x126748c70  deopt script offset  (1600)
0x126748c70  deopt inlining id  (4)
0x126748c70  deopt reason  ((unknown))
0x126748c70  deopt index
0x126748c74  deopt script offset  (1010)
0x126748c74  deopt inlining id  (-1)
0x126748c74  deopt reason  ((unknown))
0x126748c74  deopt index

[completed compiling 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> (target MAGLEV) OSR - took 0.000, 2.208, 2.542 ms]
[OSR - available (compilation completed or cache hit). function: work, osr offset: 38, mode: ConcurrencyMode::kConcurrent]
[OSR - entry. function: work, osr offset: 38]
[OSR - setting osr urgency. function: work, old urgency: 0, new urgency: 1]
[OSR - compilation started. function: work, osr offset: 38, mode: ConcurrencyMode::kConcurrent]
[compiling method 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> (target TURBOFAN_JS) OSR, mode: ConcurrencyMode::kConcurrent]
[OSR - unavailable (failed or in progress). function: work, osr offset: 38, mode: ConcurrencyMode::kConcurrent]
--- Raw source ---
(iterations, depth) {
    let check = 0;
    for (let i = 0; i < iterations; i++) {
        check += itemCheck(bottomUpTree(depth));
    }
    console.log(`${iterations}\x5ct trees of depth ${depth}\x5ct check: ${check}`);
}


--- Optimized code ---
optimization_id = 9
source_position = 965
kind = TURBOFAN_JS
name = work
compiler = turbofan
address = 0x1ae954e56a11

Instructions (size = 2388)
0x126748d80     0  a9bf7bfd       stp fp, lr, [sp, #-16]!
0x126748d84     4  910003fd       mov fp, sp
0x126748d88     8  a9be03ff       stp xzr, x0, [sp, #-32]!
0x126748d8c     c  a9016fe1       stp x1, cp, [sp, #16]
0x126748d90    10  d4200000       brk #0x0
0x126748d94    14  910183f0       add x16, sp, #0x60 (96)
0x126748d98    18  eb1d021f       cmp x16, fp
0x126748d9c    1c  54000040       b.eq #+0x8 (addr 0x126748da4)
0x126748da0    20  d4200000       brk #0x0
0x126748da4    24  d10103ff       sub sp, sp, #0x40 (64)
0x126748da8    28  f8520344       ldur x4, [x26, #-224]
0x126748dac    2c  f9001ffb       str cp, [sp, #56]
0x126748db0    30  d10423e5       sub x5, sp, #0x108 (264)
0x126748db4    34  eb0400bf       cmp x5, x4
0x126748db8    38  54003429       b.ls #+0x684 (addr 0x12674943c)
0x126748dbc    3c  f94033e4       ldr x4, [sp, #96]
0x126748dc0    40  f240009f       tst x4, #0x1
0x126748dc4    44  54004361       b.ne #+0x86c (addr 0x126749630)
0x126748dc8    48  f9405fe5       ldr x5, [sp, #184]
0x126748dcc    4c  f24000bf       tst x5, #0x1
0x126748dd0    50  54004321       b.ne #+0x864 (addr 0x126749634)
0x126748dd4    54  eb05009f       cmp x4, x5
0x126748dd8    58  5400008b       b.lt #+0x10 (addr 0x126748de8)
0x126748ddc    5c  f94037f0       ldr x16, [sp, #104]
0x126748de0    60  f9001bf0       str x16, [sp, #48]
0x126748de4    64  14000190       b #+0x640 (addr 0x126749424)
0x126748de8    68  f9401fe6       ldr x6, [sp, #56]
0x126748dec    6c  f84370c7       ldur x7, [x6, #55]
0x126748df0    70  f843f0c8       ldur x8, [x6, #63]
0x126748df4    74  58003f21       ldr x1, pc+2020 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126748df8    78  eb01011f       cmp x8, x1
0x126748dfc    7c  54004441       b.ne #+0x888 (addr 0x126749684)
0x126748e00    80  f94063e8       ldr x8, [sp, #192]
0x126748e04    84  f240011f       tst x8, #0x1
0x126748e08    88  540041a1       b.ne #+0x834 (addr 0x12674963c)
0x126748e0c    8c  f9000fe7       str x7, [sp, #24]
0x126748e10    90  f100011f       cmp x8, #0x0 (0)
0x126748e14    94  5400030c       b.gt #+0x60 (addr 0x126748e74)
0x126748e18    98  f85d0349       ldur x9, [x26, #-48]
0x126748e1c    9c  f85d834a       ldur x10, [x26, #-40]
0x126748e20    a0  9100a12b       add x11, x9, #0x28 (40)
0x126748e24    a4  eb0a017f       cmp x11, x10
0x126748e28    a8  54003222       b.hs #+0x644 (addr 0x12674946c)
0x126748e2c    ac  9100a12a       add x10, x9, #0x28 (40)
0x126748e30    b0  f81d034a       stur x10, [x26, #-48]
0x126748e34    b4  91000529       add x9, x9, #0x1 (1)
0x126748e38    b8  f941374a       ldr x10, [x26, #616]
0x126748e3c    bc  f800712a       stur x10, [x9, #7]
0x126748e40    c0  f800f12a       stur x10, [x9, #15]
0x126748e44    c4  f940db4b       ldr x11, [x26, #432]
0x126748e48    c8  f801712b       stur x11, [x9, #23]
0x126748e4c    cc  58003cac       ldr x12, pc+1940 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126748e50    d0  f81ff12c       stur x12, [x9, #-1]
0x126748e54    d4  f801f12b       stur x11, [x9, #31]
0x126748e58    d8  f9001be9       str x9, [sp, #48]
0x126748e5c    dc  f940d343       ldr x3, [x26, #416]
0x126748e60    e0  aa0c03e7       mov x7, x12
0x126748e64    e4  58003c28       ldr x8, pc+1924 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126748e68    e8  aa0a03e6       mov x6, x10
0x126748e6c    ec  58003c25       ldr x5, pc+1924 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126748e70    f0  14000045       b #+0x114 (addr 0x126748f84)
0x126748e74    f4  9360fd09       asr x9, x8, #32
0x126748e78    f8  71000529       subs w9, w9, #0x1 (1)
0x126748e7c    fc  54003e26       b.vs #+0x7c4 (addr 0x126749640)
0x126748e80   100  f842703b       ldur cp, [x1, #39]
0x126748e84   104  d3607d29       lsl x9, x9, #32
0x126748e88   108  d10043ff       sub sp, sp, #0x10 (16)
0x126748e8c   10c  f940d343       ldr x3, [x26, #416]
0x126748e90   110  a90027e3       stp x3, x9, [sp]
0x126748e94   114  f9001fe9       str x9, [sp, #56]
0x126748e98   118  d2800040       movz x0, #0x2
0x126748e9c   11c  b8417024       ldur w4, [x1, #23]
0x126748ea0   120  d2a1cd55       movz x21, #0xe6a0000
0x126748ea4   124  f2c00035       movk x21, #0x1, lsl #32
0x126748ea8   128  d348fc94       lsr x20, x4, #8
0x126748eac   12c  8b1412b5       add x21, x21, x20, lsl #4
0x126748eb0   130  f94002a2       ldr x2, [x21]
0x126748eb4   134  794012b4       ldrh w20, [x21, #8]
0x126748eb8   138  f1000a9f       cmp x20, #0x2 (2)
0x126748ebc   13c  5400004d       b.le #+0x8 (addr 0x126748ec4)
0x126748ec0   140  d4200000       brk #0x0
0x126748ec4   144  d63f0040       blr x2
0x126748ec8   148  58003881       ldr x1, pc+1808 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126748ecc   14c  f842703b       ldur cp, [x1, #39]
0x126748ed0   150  d10043ff       sub sp, sp, #0x10 (16)
0x126748ed4   154  f9401fe4       ldr x4, [sp, #56]
0x126748ed8   158  f940d343       ldr x3, [x26, #416]
0x126748edc   15c  a90013e3       stp x3, x4, [sp]
0x126748ee0   160  f9001be0       str x0, [sp, #48]
0x126748ee4   164  d2800040       movz x0, #0x2
0x126748ee8   168  b8417024       ldur w4, [x1, #23]
0x126748eec   16c  d2a1cd55       movz x21, #0xe6a0000
0x126748ef0   170  f2c00035       movk x21, #0x1, lsl #32
0x126748ef4   174  d348fc94       lsr x20, x4, #8
0x126748ef8   178  8b1412b5       add x21, x21, x20, lsl #4
0x126748efc   17c  f94002a2       ldr x2, [x21]
0x126748f00   180  794012b4       ldrh w20, [x21, #8]
0x126748f04   184  f1000a9f       cmp x20, #0x2 (2)
0x126748f08   188  5400004d       b.le #+0x8 (addr 0x126748f10)
0x126748f0c   18c  d4200000       brk #0x0
0x126748f10   190  d63f0040       blr x2
0x126748f14   194  f85d0344       ldur x4, [x26, #-48]
0x126748f18   198  f85d8345       ldur x5, [x26, #-40]
0x126748f1c   19c  9100a086       add x6, x4, #0x28 (40)
0x126748f20   1a0  eb0500df       cmp x6, x5
0x126748f24   1a4  54002bc2       b.hs #+0x578 (addr 0x12674949c)
0x126748f28   1a8  9100a085       add x5, x4, #0x28 (40)
0x126748f2c   1ac  f81d0345       stur x5, [x26, #-48]
0x126748f30   1b0  91000484       add x4, x4, #0x1 (1)
0x126748f34   1b4  580035e5       ldr x5, pc+1724 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126748f38   1b8  f81ff085       stur x5, [x4, #-1]
0x126748f3c   1bc  f9413746       ldr x6, [x26, #616]
0x126748f40   1c0  f8007086       stur x6, [x4, #7]
0x126748f44   1c4  f800f086       stur x6, [x4, #15]
0x126748f48   1c8  f940d343       ldr x3, [x26, #416]
0x126748f4c   1cc  f8017083       stur x3, [x4, #23]
0x126748f50   1d0  f801f083       stur x3, [x4, #31]
0x126748f54   1d4  f94013e7       ldr x7, [sp, #32]
0x126748f58   1d8  f24000ff       tst x7, #0x1
0x126748f5c   1dc  54003740       b.eq #+0x6e8 (addr 0x126749644)
0x126748f60   1e0  58003448       ldr x8, pc+1672 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126748f64   1e4  f81ff088       stur x8, [x4, #-1]
0x126748f68   1e8  f8017087       stur x7, [x4, #23]
0x126748f6c   1ec  f240001f       tst x0, #0x1
0x126748f70   1f0  540036c0       b.eq #+0x6d8 (addr 0x126749648)
0x126748f74   1f4  58003367       ldr x7, pc+1644 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126748f78   1f8  f81ff087       stur x7, [x4, #-1]
0x126748f7c   1fc  f801f080       stur x0, [x4, #31]
0x126748f80   200  f9001be4       str x4, [sp, #48]
0x126748f84   204  580033a1       ldr x1, pc+1652 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126748f88   208  f9400fe4       ldr x4, [sp, #24]
0x126748f8c   20c  eb01009f       cmp x4, x1
0x126748f90   210  540035e1       b.ne #+0x6bc (addr 0x12674964c)
0x126748f94   214  f9401be9       ldr x9, [sp, #48]
0x126748f98   218  f8417124       ldur x4, [x9, #23]
0x126748f9c   21c  f940db4a       ldr x10, [x26, #432]
0x126748fa0   220  eb0a009f       cmp x4, x10
0x126748fa4   224  54000800       b.eq #+0x100 (addr 0x1267490a4)
0x126748fa8   228  f841f12b       ldur x11, [x9, #31]
0x126748fac   22c  f90013eb       str x11, [sp, #32]
0x126748fb0   230  eb0a017f       cmp x11, x10
0x126748fb4   234  54000780       b.eq #+0xf0 (addr 0x1267490a4)
0x126748fb8   238  f842703b       ldur cp, [x1, #39]
0x126748fbc   23c  d10043ff       sub sp, sp, #0x10 (16)
0x126748fc0   240  a90013e3       stp x3, x4, [sp]
0x126748fc4   244  d2800040       movz x0, #0x2
0x126748fc8   248  b8417024       ldur w4, [x1, #23]
0x126748fcc   24c  d2a1cd55       movz x21, #0xe6a0000
0x126748fd0   250  f2c00035       movk x21, #0x1, lsl #32
0x126748fd4   254  d348fc94       lsr x20, x4, #8
0x126748fd8   258  8b1412b5       add x21, x21, x20, lsl #4
0x126748fdc   25c  f94002a2       ldr x2, [x21]
0x126748fe0   260  794012b4       ldrh w20, [x21, #8]
0x126748fe4   264  f1000a9f       cmp x20, #0x2 (2)
0x126748fe8   268  5400004d       b.le #+0x8 (addr 0x126748ff0)
0x126748fec   26c  d4200000       brk #0x0
0x126748ff0   270  d63f0040       blr x2
0x126748ff4   274  f240001f       tst x0, #0x1
0x126748ff8   278  540032c1       b.ne #+0x658 (addr 0x126749650)
0x126748ffc   27c  9360fc04       asr x4, x0, #32
0x126749000   280  31000484       adds w4, w4, #0x1 (1)
0x126749004   284  54003286       b.vs #+0x650 (addr 0x126749654)
0x126749008   288  f9401be9       ldr x9, [sp, #48]
0x12674900c   28c  f85ff125       ldur x5, [x9, #-1]
0x126749010   290  58002e86       ldr x6, pc+1488 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126749014   294  eb0600bf       cmp x5, x6
0x126749018   298  54003201       b.ne #+0x640 (addr 0x126749658)
0x12674901c   29c  58002ee1       ldr x1, pc+1500 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126749020   2a0  f842703b       ldur cp, [x1, #39]
0x126749024   2a4  d10043ff       sub sp, sp, #0x10 (16)
0x126749028   2a8  f9401be5       ldr x5, [sp, #48]
0x12674902c   2ac  f940d343       ldr x3, [x26, #416]
0x126749030   2b0  a90017e3       stp x3, x5, [sp]
0x126749034   2b4  f90017e4       str x4, [sp, #40]
0x126749038   2b8  d2800040       movz x0, #0x2
0x12674903c   2bc  b8417024       ldur w4, [x1, #23]
0x126749040   2c0  d2a1cd55       movz x21, #0xe6a0000
0x126749044   2c4  f2c00035       movk x21, #0x1, lsl #32
0x126749048   2c8  d348fc94       lsr x20, x4, #8
0x12674904c   2cc  8b1412b5       add x21, x21, x20, lsl #4
0x126749050   2d0  f94002a2       ldr x2, [x21]
0x126749054   2d4  794012b4       ldrh w20, [x21, #8]
0x126749058   2d8  f1000a9f       cmp x20, #0x2 (2)
0x12674905c   2dc  5400004d       b.le #+0x8 (addr 0x126749064)
0x126749060   2e0  d4200000       brk #0x0
0x126749064   2e4  d63f0040       blr x2
0x126749068   2e8  f240001f       tst x0, #0x1
0x12674906c   2ec  54002f81       b.ne #+0x5f0 (addr 0x12674965c)
0x126749070   2f0  9360fc04       asr x4, x0, #32
0x126749074   2f4  f9400fe5       ldr x5, [sp, #24]
0x126749078   2f8  2b0400a4       adds w4, w5, w4
0x12674907c   2fc  54002f26       b.vs #+0x5e4 (addr 0x126749660)
0x126749080   300  aa0403e9       mov x9, x4
0x126749084   304  58002b65       ldr x5, pc+1388 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126749088   308  58002b81       ldr x1, pc+1392 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x12674908c   30c  f940d343       ldr x3, [x26, #416]
0x126749090   310  58002a87       ldr x7, pc+1360 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126749094   314  f940db4a       ldr x10, [x26, #432]
0x126749098   318  58002a88       ldr x8, pc+1360 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x12674909c   31c  f9413746       ldr x6, [x26, #616]
0x1267490a0   320  14000002       b #+0x8 (addr 0x1267490a8)
0x1267490a4   324  d2800029       movz x9, #0x1
0x1267490a8   328  f94037eb       ldr x11, [sp, #104]
0x1267490ac   32c  f240017f       tst x11, #0x1
0x1267490b0   330  54002da1       b.ne #+0x5b4 (addr 0x126749664)
0x1267490b4   334  9360fd6c       asr x12, x11, #32
0x1267490b8   338  2b09018c       adds w12, w12, w9
0x1267490bc   33c  54002d66       b.vs #+0x5ac (addr 0x126749668)
0x1267490c0   340  f94033ed       ldr x13, [sp, #96]
0x1267490c4   344  9360fdae       asr x14, x13, #32
0x1267490c8   348  310005ce       adds w14, w14, #0x1 (1)
0x1267490cc   34c  54002d06       b.vs #+0x5a0 (addr 0x12674966c)
0x1267490d0   350  38531349       ldurb w9, [x26, #-207]
0x1267490d4   354  d2800024       movz x4, #0x1
0x1267490d8   358  35001f09       cbnz w9, #+0x3e0 (addr 0x1267494b8)
0x1267490dc   35c  f9000bee       str x14, [sp, #16]
0x1267490e0   360  f90007ec       str x12, [sp, #8]
0x1267490e4   364  aa0503eb       mov x11, x5
0x1267490e8   368  f9405fe5       ldr x5, [sp, #184]
0x1267490ec   36c  aa0a03e9       mov x9, x10
0x1267490f0   370  aa0703ea       mov x10, x7
0x1267490f4   374  f94063e7       ldr x7, [sp, #192]
0x1267490f8   378  aa0803ec       mov x12, x8
0x1267490fc   37c  aa0603e8       mov x8, x6
0x126749100   380  f9401fe6       ldr x6, [sp, #56]
0x126749104   384  aa0103ed       mov x13, x1
0x126749108   388  58002681       ldr x1, pc+1232 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x12674910c   38c  14000004       b #+0x10 (addr 0x12674911c)
0x126749110   390  f9000bf4       str x20, [sp, #16]
0x126749114   394  f90007f3       str x19, [sp, #8]
0x126749118   398  aa0403ed       mov x13, x4
0x12674911c   39c  9360fcae       asr x14, x5, #32
0x126749120   3a0  f9400bef       ldr x15, [sp, #16]
0x126749124   3a4  6b0e01ff       cmp w15, w14
0x126749128   3a8  5400178a       b.ge #+0x2f0 (addr 0x126749418)
0x12674912c   3ac  f84370ce       ldur x14, [x6, #55]
0x126749130   3b0  f843f0d3       ldur x19, [x6, #63]
0x126749134   3b4  eb01027f       cmp x19, x1
0x126749138   3b8  540029c1       b.ne #+0x538 (addr 0x126749670)
0x12674913c   3bc  f90017ee       str x14, [sp, #40]
0x126749140   3c0  f10000ff       cmp x7, #0x0 (0)
0x126749144   3c4  5400020c       b.gt #+0x40 (addr 0x126749184)
0x126749148   3c8  f85d0353       ldur x19, [x26, #-48]
0x12674914c   3cc  f85d8354       ldur x20, [x26, #-40]
0x126749150   3d0  9100a275       add x21, x19, #0x28 (40)
0x126749154   3d4  eb1402bf       cmp x21, x20
0x126749158   3d8  54001da2       b.hs #+0x3b4 (addr 0x12674950c)
0x12674915c   3dc  9100a274       add x20, x19, #0x28 (40)
0x126749160   3e0  f81d0354       stur x20, [x26, #-48]
0x126749164   3e4  91000673       add x19, x19, #0x1 (1)
0x126749168   3e8  f8007268       stur x8, [x19, #7]
0x12674916c   3ec  f800f268       stur x8, [x19, #15]
0x126749170   3f0  f8017269       stur x9, [x19, #23]
0x126749174   3f4  f81ff26a       stur x10, [x19, #-1]
0x126749178   3f8  f801f269       stur x9, [x19, #31]
0x12674917c   3fc  f9001bf3       str x19, [sp, #48]
0x126749180   400  14000050       b #+0x140 (addr 0x1267492c0)
0x126749184   404  9360fcf3       asr x19, x7, #32
0x126749188   408  71000673       subs w19, w19, #0x1 (1)
0x12674918c   40c  54002746       b.vs #+0x4e8 (addr 0x126749674)
0x126749190   410  f842703b       ldur cp, [x1, #39]
0x126749194   414  d3607e73       lsl x19, x19, #32
0x126749198   418  d10043ff       sub sp, sp, #0x10 (16)
0x12674919c   41c  a9004fe3       stp x3, x19, [sp]
0x1267491a0   420  f90023f3       str x19, [sp, #64]
0x1267491a4   424  d2800040       movz x0, #0x2
0x1267491a8   428  b8417024       ldur w4, [x1, #23]
0x1267491ac   42c  d2a1cd55       movz x21, #0xe6a0000
0x1267491b0   430  f2c00035       movk x21, #0x1, lsl #32
0x1267491b4   434  d348fc94       lsr x20, x4, #8
0x1267491b8   438  8b1412b5       add x21, x21, x20, lsl #4
0x1267491bc   43c  f94002a2       ldr x2, [x21]
0x1267491c0   440  794012b4       ldrh w20, [x21, #8]
0x1267491c4   444  f1000a9f       cmp x20, #0x2 (2)
0x1267491c8   448  5400004d       b.le #+0x8 (addr 0x1267491d0)
0x1267491cc   44c  d4200000       brk #0x0
0x1267491d0   450  d63f0040       blr x2
0x1267491d4   454  58002021       ldr x1, pc+1028 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267491d8   458  f842703b       ldur cp, [x1, #39]
0x1267491dc   45c  d10043ff       sub sp, sp, #0x10 (16)
0x1267491e0   460  f94023e4       ldr x4, [sp, #64]
0x1267491e4   464  f940d343       ldr x3, [x26, #416]
0x1267491e8   468  a90013e3       stp x3, x4, [sp]
0x1267491ec   46c  f90017e0       str x0, [sp, #40]
0x1267491f0   470  d2800040       movz x0, #0x2
0x1267491f4   474  b8417024       ldur w4, [x1, #23]
0x1267491f8   478  d2a1cd55       movz x21, #0xe6a0000
0x1267491fc   47c  f2c00035       movk x21, #0x1, lsl #32
0x126749200   480  d348fc94       lsr x20, x4, #8
0x126749204   484  8b1412b5       add x21, x21, x20, lsl #4
0x126749208   488  f94002a2       ldr x2, [x21]
0x12674920c   48c  794012b4       ldrh w20, [x21, #8]
0x126749210   490  f1000a9f       cmp x20, #0x2 (2)
0x126749214   494  5400004d       b.le #+0x8 (addr 0x12674921c)
0x126749218   498  d4200000       brk #0x0
0x12674921c   49c  d63f0040       blr x2
0x126749220   4a0  f85d0344       ldur x4, [x26, #-48]
0x126749224   4a4  f85d8345       ldur x5, [x26, #-40]
0x126749228   4a8  9100a086       add x6, x4, #0x28 (40)
0x12674922c   4ac  eb0500df       cmp x6, x5
0x126749230   4b0  54001922       b.hs #+0x324 (addr 0x126749554)
0x126749234   4b4  9100a085       add x5, x4, #0x28 (40)
0x126749238   4b8  f81d0345       stur x5, [x26, #-48]
0x12674923c   4bc  91000484       add x4, x4, #0x1 (1)
0x126749240   4c0  58001d85       ldr x5, pc+944 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126749244   4c4  f81ff085       stur x5, [x4, #-1]
0x126749248   4c8  f9413746       ldr x6, [x26, #616]
0x12674924c   4cc  f8007086       stur x6, [x4, #7]
0x126749250   4d0  f800f086       stur x6, [x4, #15]
0x126749254   4d4  f940d343       ldr x3, [x26, #416]
0x126749258   4d8  f8017083       stur x3, [x4, #23]
0x12674925c   4dc  f801f083       stur x3, [x4, #31]
0x126749260   4e0  f9400fe7       ldr x7, [sp, #24]
0x126749264   4e4  f24000ff       tst x7, #0x1
0x126749268   4e8  54002080       b.eq #+0x410 (addr 0x126749678)
0x12674926c   4ec  58001be8       ldr x8, pc+892 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126749270   4f0  f81ff088       stur x8, [x4, #-1]
0x126749274   4f4  f8017087       stur x7, [x4, #23]
0x126749278   4f8  f240001f       tst x0, #0x1
0x12674927c   4fc  54002000       b.eq #+0x400 (addr 0x12674967c)
0x126749280   500  58001b07       ldr x7, pc+864 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126749284   504  f81ff087       stur x7, [x4, #-1]
0x126749288   508  f801f080       stur x0, [x4, #31]
0x12674928c   50c  f9001be4       str x4, [sp, #48]
0x126749290   510  aa0503eb       mov x11, x5
0x126749294   514  f9405fe5       ldr x5, [sp, #184]
0x126749298   518  aa0703ea       mov x10, x7
0x12674929c   51c  f94063e7       ldr x7, [sp, #192]
0x1267492a0   520  aa0803ec       mov x12, x8
0x1267492a4   524  aa0603e8       mov x8, x6
0x1267492a8   528  f9401fe6       ldr x6, [sp, #56]
0x1267492ac   52c  f9400bef       ldr x15, [sp, #16]
0x1267492b0   530  58001a4d       ldr x13, pc+840 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267492b4   534  f940db49       ldr x9, [x26, #432]
0x1267492b8   538  f94017ee       ldr x14, [sp, #40]
0x1267492bc   53c  580018e1       ldr x1, pc+796 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267492c0   540  aa0d03e4       mov x4, x13
0x1267492c4   544  aa0e03ed       mov x13, x14
0x1267492c8   548  eb0401bf       cmp x13, x4
0x1267492cc   54c  54001da1       b.ne #+0x3b4 (addr 0x126749680)
0x1267492d0   550  f9401bf3       ldr x19, [sp, #48]
0x1267492d4   554  f841726d       ldur x13, [x19, #23]
0x1267492d8   558  eb0901bf       cmp x13, x9
0x1267492dc   55c  540008c0       b.eq #+0x118 (addr 0x1267493f4)
0x1267492e0   560  f841f26e       ldur x14, [x19, #31]
0x1267492e4   564  f90017ee       str x14, [sp, #40]
0x1267492e8   568  eb0901df       cmp x14, x9
0x1267492ec   56c  54000840       b.eq #+0x108 (addr 0x1267493f4)
0x1267492f0   570  f842709b       ldur cp, [x4, #39]
0x1267492f4   574  d10043ff       sub sp, sp, #0x10 (16)
0x1267492f8   578  a90037e3       stp x3, x13, [sp]
0x1267492fc   57c  aa0403e1       mov x1, x4
0x126749300   580  d2800040       movz x0, #0x2
0x126749304   584  b8417024       ldur w4, [x1, #23]
0x126749308   588  d2a1cd55       movz x21, #0xe6a0000
0x12674930c   58c  f2c00035       movk x21, #0x1, lsl #32
0x126749310   590  d348fc94       lsr x20, x4, #8
0x126749314   594  8b1412b5       add x21, x21, x20, lsl #4
0x126749318   598  f94002a2       ldr x2, [x21]
0x12674931c   59c  794012b4       ldrh w20, [x21, #8]
0x126749320   5a0  f1000a9f       cmp x20, #0x2 (2)
0x126749324   5a4  5400004d       b.le #+0x8 (addr 0x12674932c)
0x126749328   5a8  d4200000       brk #0x0
0x12674932c   5ac  d63f0040       blr x2
0x126749330   5b0  f240001f       tst x0, #0x1
0x126749334   5b4  54001b61       b.ne #+0x36c (addr 0x1267496a0)
0x126749338   5b8  9360fc04       asr x4, x0, #32
0x12674933c   5bc  31000484       adds w4, w4, #0x1 (1)
0x126749340   5c0  540017c6       b.vs #+0x2f8 (addr 0x126749638)
0x126749344   5c4  f9401bf3       ldr x19, [sp, #48]
0x126749348   5c8  f85ff265       ldur x5, [x19, #-1]
0x12674934c   5cc  580014a6       ldr x6, pc+660 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x126749350   5d0  eb0600bf       cmp x5, x6
0x126749354   5d4  54001a41       b.ne #+0x348 (addr 0x12674969c)
0x126749358   5d8  58001501       ldr x1, pc+672 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x12674935c   5dc  f842703b       ldur cp, [x1, #39]
0x126749360   5e0  d10043ff       sub sp, sp, #0x10 (16)
0x126749364   5e4  f9401fe5       ldr x5, [sp, #56]
0x126749368   5e8  f940d343       ldr x3, [x26, #416]
0x12674936c   5ec  a90017e3       stp x3, x5, [sp]
0x126749370   5f0  f9001be4       str x4, [sp, #48]
0x126749374   5f4  d2800040       movz x0, #0x2
0x126749378   5f8  b8417024       ldur w4, [x1, #23]
0x12674937c   5fc  d2a1cd55       movz x21, #0xe6a0000
0x126749380   600  f2c00035       movk x21, #0x1, lsl #32
0x126749384   604  d348fc94       lsr x20, x4, #8
0x126749388   608  8b1412b5       add x21, x21, x20, lsl #4
0x12674938c   60c  f94002a2       ldr x2, [x21]
0x126749390   610  794012b4       ldrh w20, [x21, #8]
0x126749394   614  f1000a9f       cmp x20, #0x2 (2)
0x126749398   618  5400004d       b.le #+0x8 (addr 0x1267493a0)
0x12674939c   61c  d4200000       brk #0x0
0x1267493a0   620  d63f0040       blr x2
0x1267493a4   624  f240001f       tst x0, #0x1
0x1267493a8   628  54001781       b.ne #+0x2f0 (addr 0x126749698)
0x1267493ac   62c  9360fc04       asr x4, x0, #32
0x1267493b0   630  f94013e5       ldr x5, [sp, #32]
0x1267493b4   634  2b0400a4       adds w4, w5, w4
0x1267493b8   638  540016e6       b.vs #+0x2dc (addr 0x126749694)
0x1267493bc   63c  aa0403ed       mov x13, x4
0x1267493c0   640  f9405fe5       ldr x5, [sp, #184]
0x1267493c4   644  f94063e7       ldr x7, [sp, #192]
0x1267493c8   648  f9401fe6       ldr x6, [sp, #56]
0x1267493cc   64c  58001061       ldr x1, pc+524 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267493d0   650  f9400bef       ldr x15, [sp, #16]
0x1267493d4   654  58001124       ldr x4, pc+548 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267493d8   658  f940d343       ldr x3, [x26, #416]
0x1267493dc   65c  5800102a       ldr x10, pc+516 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1267493e0   660  f940db49       ldr x9, [x26, #432]
0x1267493e4   664  5800102c       ldr x12, pc+516 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1267493e8   668  f9413748       ldr x8, [x26, #616]
0x1267493ec   66c  5800102b       ldr x11, pc+516 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1267493f0   670  14000002       b #+0x8 (addr 0x1267493f8)
0x1267493f4   674  d280002d       movz x13, #0x1
0x1267493f8   678  f94007ee       ldr x14, [sp, #8]
0x1267493fc   67c  2b0d01d3       adds w19, w14, w13
0x126749400   680  54001486       b.vs #+0x290 (addr 0x126749690)
0x126749404   684  310005f4       adds w20, w15, #0x1 (1)
0x126749408   688  54001426       b.vs #+0x284 (addr 0x12674968c)
0x12674940c   68c  3853134d       ldurb w13, [x26, #-207]
0x126749410   690  34ffe80d       cbz w13, #-0x300 (addr 0x126749110)
0x126749414   694  14000057       b #+0x15c (addr 0x126749570)
0x126749418   698  f94007ec       ldr x12, [sp, #8]
0x12674941c   69c  d3607d8b       lsl x11, x12, #32
0x126749420   6a0  f9001beb       str x11, [sp, #48]
0x126749424   6a4  f94a6742       ldr x2, [x26, #5320]
0x126749428   6a8  d2800200       movz x0, #0x10
0x12674942c   6ac  58000ebb       ldr cp, pc+468 (addr 0x0000000126749600)    ;; object: 0x234724400109 <NativeContext[302]>
0x126749430   6b0  58000f10       ldr x16, pc+480 (addr 0x0000000126749610)
0x126749434   6b4  d63f0200       blr x16
0x126749438   6b8  14000094       b #+0x250 (addr 0x126749688)
0x12674943c   6bc  d2c02104       movz x4, #0x10800000000
0x126749440   6c0  d10043ff       sub sp, sp, #0x10 (16)
0x126749444   6c4  f90007ff       str xzr, [sp, #8]
0x126749448   6c8  f90003e4       str x4, [sp]
0x12674944c   6cc  58000dbb       ldr cp, pc+436 (addr 0x0000000126749600)    ;; object: 0x234724400109 <NativeContext[302]>
0x126749450   6d0  d29d4f01       movz x1, #0xea78
0x126749454   6d4  f2a06081       movk x1, #0x304, lsl #16
0x126749458   6d8  f2c00021       movk x1, #0x1, lsl #32
0x12674945c   6dc  d2800020       movz x0, #0x1
0x126749460   6e0  58000dd0       ldr x16, pc+440 (addr 0x0000000126749618)
0x126749464   6e4  d63f0200       blr x16
0x126749468   6e8  17fffe55       b #-0x6ac (addr 0x126748dbc)
0x12674946c   6ec  d2800501       movz x1, #0x28
0x126749470   6f0  aa0103e9       mov x9, x1
0x126749474   6f4  58000cb0       ldr x16, pc+404 (addr 0x0000000126749608)
0x126749478   6f8  d63f0200       blr x16
0x12674947c   6fc  d1000409       sub x9, x0, #0x1 (1)
0x126749480   700  f9400fe7       ldr x7, [sp, #24]
0x126749484   704  f9405fe5       ldr x5, [sp, #184]
0x126749488   708  f94063e8       ldr x8, [sp, #192]
0x12674948c   70c  f9401fe6       ldr x6, [sp, #56]
0x126749490   710  58000a41       ldr x1, pc+328 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126749494   714  f94033e4       ldr x4, [sp, #96]
0x126749498   718  17fffe65       b #-0x66c (addr 0x126748e2c)
0x12674949c   71c  f90017e0       str x0, [sp, #40]
0x1267494a0   720  d2800501       movz x1, #0x28
0x1267494a4   724  58000b30       ldr x16, pc+356 (addr 0x0000000126749608)
0x1267494a8   728  d63f0200       blr x16
0x1267494ac   72c  d1000404       sub x4, x0, #0x1 (1)
0x1267494b0   730  f94017e0       ldr x0, [sp, #40]
0x1267494b4   734  17fffe9d       b #-0x58c (addr 0x126748f28)
0x1267494b8   738  58000a5b       ldr cp, pc+328 (addr 0x0000000126749600)    ;; object: 0x234724400109 <NativeContext[302]>
0x1267494bc   73c  d2800000       movz x0, #0x0
0x1267494c0   740  f9000bee       str x14, [sp, #16]
0x1267494c4   744  f90007ec       str x12, [sp, #8]
0x1267494c8   748  d29d1c81       movz x1, #0xe8e4
0x1267494cc   74c  f2a06081       movk x1, #0x304, lsl #16
0x1267494d0   750  f2c00021       movk x1, #0x1, lsl #32
0x1267494d4   754  aa0103e9       mov x9, x1
0x1267494d8   758  58000a10       ldr x16, pc+320 (addr 0x0000000126749618)
0x1267494dc   75c  d63f0200       blr x16
0x1267494e0   760  d2800024       movz x4, #0x1
0x1267494e4   764  580008a1       ldr x1, pc+276 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267494e8   768  f940d343       ldr x3, [x26, #416]
0x1267494ec   76c  580007a7       ldr x7, pc+244 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1267494f0   770  f940db4a       ldr x10, [x26, #432]
0x1267494f4   774  580007a8       ldr x8, pc+244 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1267494f8   778  f9413746       ldr x6, [x26, #616]
0x1267494fc   77c  580007a5       ldr x5, pc+244 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126749500   780  f9400bee       ldr x14, [sp, #16]
0x126749504   784  f94007ec       ldr x12, [sp, #8]
0x126749508   788  17fffef5       b #-0x42c (addr 0x1267490dc)
0x12674950c   78c  d2800501       movz x1, #0x28
0x126749510   790  580007d0       ldr x16, pc+248 (addr 0x0000000126749608)
0x126749514   794  d63f0200       blr x16
0x126749518   798  d1000413       sub x19, x0, #0x1 (1)
0x12674951c   79c  580005e1       ldr x1, pc+188 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x126749520   7a0  f9405fe5       ldr x5, [sp, #184]
0x126749524   7a4  f94063e7       ldr x7, [sp, #192]
0x126749528   7a8  f9401fe6       ldr x6, [sp, #56]
0x12674952c   7ac  f9400bef       ldr x15, [sp, #16]
0x126749530   7b0  5800064d       ldr x13, pc+200 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x126749534   7b4  f940d343       ldr x3, [x26, #416]
0x126749538   7b8  5800054a       ldr x10, pc+168 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x12674953c   7bc  f940db49       ldr x9, [x26, #432]
0x126749540   7c0  f94017ee       ldr x14, [sp, #40]
0x126749544   7c4  5800052c       ldr x12, pc+164 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x126749548   7c8  f9413748       ldr x8, [x26, #616]
0x12674954c   7cc  5800052b       ldr x11, pc+164 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x126749550   7d0  17ffff03       b #-0x3f4 (addr 0x12674915c)
0x126749554   7d4  f9001be0       str x0, [sp, #48]
0x126749558   7d8  d2800501       movz x1, #0x28
0x12674955c   7dc  58000570       ldr x16, pc+172 (addr 0x0000000126749608)
0x126749560   7e0  d63f0200       blr x16
0x126749564   7e4  d1000404       sub x4, x0, #0x1 (1)
0x126749568   7e8  f9401be0       ldr x0, [sp, #48]
0x12674956c   7ec  17ffff32       b #-0x338 (addr 0x126749234)
0x126749570   7f0  f9001bf4       str x20, [sp, #48]
0x126749574   7f4  f90017f3       str x19, [sp, #40]
0x126749578   7f8  d29d1c81       movz x1, #0xe8e4
0x12674957c   7fc  f2a06081       movk x1, #0x304, lsl #16
0x126749580   800  f2c00021       movk x1, #0x1, lsl #32
0x126749584   804  d2800000       movz x0, #0x0
0x126749588   808  580003db       ldr cp, pc+120 (addr 0x0000000126749600)    ;; object: 0x234724400109 <NativeContext[302]>
0x12674958c   80c  58000470       ldr x16, pc+140 (addr 0x0000000126749618)
0x126749590   810  d63f0200       blr x16
0x126749594   814  f9405fe5       ldr x5, [sp, #184]
0x126749598   818  f94063e7       ldr x7, [sp, #192]
0x12674959c   81c  f9401fe6       ldr x6, [sp, #56]
0x1267495a0   820  f9401bf4       ldr x20, [sp, #48]
0x1267495a4   824  f94017f3       ldr x19, [sp, #40]
0x1267495a8   828  58000284       ldr x4, pc+80 (addr 0x00000001267495f8)    ;; object: 0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>
0x1267495ac   82c  f940d343       ldr x3, [x26, #416]
0x1267495b0   830  5800018a       ldr x10, pc+48 (addr 0x00000001267495e0)    ;; object: 0x1dadb5f49259 <Map[40](HOLEY_ELEMENTS)>
0x1267495b4   834  f940db49       ldr x9, [x26, #432]
0x1267495b8   838  5800018c       ldr x12, pc+48 (addr 0x00000001267495e8)    ;; object: 0x1dadb5f49201 <Map[40](HOLEY_ELEMENTS)>
0x1267495bc   83c  f9413748       ldr x8, [x26, #616]
0x1267495c0   840  5800018b       ldr x11, pc+48 (addr 0x00000001267495f0)    ;; object: 0x1dadb5f49181 <Map[40](HOLEY_ELEMENTS)>
0x1267495c4   844  580000a1       ldr x1, pc+20 (addr 0x00000001267495d8)    ;; object: 0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>
0x1267495c8   848  17fffed2       b #-0x4b8 (addr 0x126749110)
0x1267495cc   84c  d503201f       nop
0x1267495d0   850  5800027f       constant pool begin (num_const = 19)    ;; constant pool
0x1267495d4   854  d63f03e0       constant
0x1267495d8   858  b5f4b821       constant
0x1267495dc   85c  00001dad       constant
0x1267495e0   860  b5f49259       constant
0x1267495e4   864  00001dad       constant
0x1267495e8   868  b5f49201       constant
0x1267495ec   86c  00001dad       constant
0x1267495f0   870  b5f49181       constant
0x1267495f4   874  00001dad       constant
0x1267495f8   878  b5f4b951       constant
0x1267495fc   87c  00001dad       constant
0x126749600   880  24400109       constant
0x126749604   884  00002347       constant
0x126749608   888  0360ace0       constant
0x12674960c   88c  00000001       constant
0x126749610   890  03665e60       constant
0x126749614   894  00000001       constant
0x126749618   898  036a61e0       constant
0x12674961c   89c  00000001       constant
0x126749620   8a0  f8558350       ldur x16, [x26, #-168]
0x126749624   8a4  d61f0200       br x16
0x126749628   8a8  f8560350       ldur x16, [x26, #-160]
0x12674962c   8ac  d61f0200       br x16
0x126749630   8b0  97fffffc       bl #-0x10 (addr 0x126749620)    ;; debug: deopt position, script offset '404'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 0
0x126749634   8b4  97fffffb       bl #-0x14 (addr 0x126749620)    ;; debug: deopt position, script offset '404'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 1
0x126749638   8b8  97fffffa       bl #-0x18 (addr 0x126749620)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 2
0x12674963c   8bc  97fffff9       bl #-0x1c (addr 0x126749620)    ;; debug: deopt position, script offset '5e5'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 3
0x126749640   8c0  97fffff8       bl #-0x20 (addr 0x126749620)    ;; debug: deopt position, script offset '613'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 4
0x126749644   8c4  97fffff7       bl #-0x24 (addr 0x126749620)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id '2'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 5
0x126749648   8c8  97fffff6       bl #-0x28 (addr 0x126749620)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id '2'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 6
0x12674964c   8cc  97fffff5       bl #-0x2c (addr 0x126749620)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 7
0x126749650   8d0  97fffff4       bl #-0x30 (addr 0x126749620)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 8
0x126749654   8d4  97fffff3       bl #-0x34 (addr 0x126749620)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 9
0x126749658   8d8  97fffff2       bl #-0x38 (addr 0x126749620)    ;; debug: deopt position, script offset '5ab'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index a
0x12674965c   8dc  97fffff1       bl #-0x3c (addr 0x126749620)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index b
0x126749660   8e0  97fffff0       bl #-0x40 (addr 0x126749620)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index c
0x126749664   8e4  97ffffef       bl #-0x44 (addr 0x126749620)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index d
0x126749668   8e8  97ffffee       bl #-0x48 (addr 0x126749620)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index e
0x12674966c   8ec  97ffffed       bl #-0x4c (addr 0x126749620)    ;; debug: deopt position, script offset '413'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index f
0x126749670   8f0  97ffffec       bl #-0x50 (addr 0x126749620)    ;; debug: deopt position, script offset '434'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 10
0x126749674   8f4  97ffffeb       bl #-0x54 (addr 0x126749620)    ;; debug: deopt position, script offset '613'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 11
0x126749678   8f8  97ffffea       bl #-0x58 (addr 0x126749620)    ;; debug: deopt position, script offset '4e2'
                                                             ;; debug: deopt position, inlining id '2'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 12
0x12674967c   8fc  97ffffe9       bl #-0x5c (addr 0x126749620)    ;; debug: deopt position, script offset '4fd'
                                                             ;; debug: deopt position, inlining id '2'
                                                             ;; debug: deopt reason 'Smi'
                                                             ;; debug: deopt index 13
0x126749680   900  97ffffe8       bl #-0x60 (addr 0x126749620)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 14
0x126749684   904  97ffffe7       bl #-0x64 (addr 0x126749620)    ;; debug: deopt position, script offset '434'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'wrong call target'
                                                             ;; debug: deopt index 15
0x126749688   908  97ffffe6       bl #-0x68 (addr 0x126749620)    ;; debug: deopt position, script offset '45c'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'Insufficient type feedback for generic named access'
                                                             ;; debug: deopt index 16
0x12674968c   90c  97ffffe5       bl #-0x6c (addr 0x126749620)    ;; debug: deopt position, script offset '413'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 17
0x126749690   910  97ffffe4       bl #-0x70 (addr 0x126749620)    ;; debug: deopt position, script offset '42a'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 18
0x126749694   914  97ffffe3       bl #-0x74 (addr 0x126749620)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'overflow'
                                                             ;; debug: deopt index 19
0x126749698   918  97ffffe2       bl #-0x78 (addr 0x126749620)    ;; debug: deopt position, script offset '59a'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 1a
0x12674969c   91c  97ffffe1       bl #-0x7c (addr 0x126749620)    ;; debug: deopt position, script offset '5ab'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'wrong map'
                                                             ;; debug: deopt index 1b
0x1267496a0   920  97ffffe0       bl #-0x80 (addr 0x126749620)    ;; debug: deopt position, script offset '583'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason 'not a Smi'
                                                             ;; debug: deopt index 1c
0x1267496a4   924  97ffffe1       bl #-0x7c (addr 0x126749628)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 1d
0x1267496a8   928  97ffffe0       bl #-0x80 (addr 0x126749628)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 1e
0x1267496ac   92c  97ffffdf       bl #-0x84 (addr 0x126749628)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 1f
0x1267496b0   930  97ffffde       bl #-0x88 (addr 0x126749628)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 20
0x1267496b4   934  97ffffdd       bl #-0x8c (addr 0x126749628)    ;; debug: deopt position, script offset '600'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 21
0x1267496b8   938  97ffffdc       bl #-0x90 (addr 0x126749628)    ;; debug: deopt position, script offset '619'
                                                             ;; debug: deopt position, inlining id '1'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 22
0x1267496bc   93c  97ffffdb       bl #-0x94 (addr 0x126749628)    ;; debug: deopt position, script offset '585'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 23
0x1267496c0   940  97ffffda       bl #-0x98 (addr 0x126749628)    ;; debug: deopt position, script offset '59c'
                                                             ;; debug: deopt position, inlining id '0'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 24
0x1267496c4   944  97ffffd9       bl #-0x9c (addr 0x126749628)    ;; debug: deopt position, script offset '454'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 25
0x1267496c8   948  97ffffd8       bl #-0xa0 (addr 0x126749628)    ;; debug: deopt position, script offset '3c5'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 26
0x1267496cc   94c  97ffffd7       bl #-0xa4 (addr 0x126749628)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 27
0x1267496d0   950  97ffffd6       bl #-0xa8 (addr 0x126749628)    ;; debug: deopt position, script offset '3f2'
                                                             ;; debug: deopt position, inlining id 'ffffffff'
                                                             ;; debug: deopt reason '(unknown)'
                                                             ;; debug: deopt index 28

Source positions:
 pc offset  position
        28       965
        3c      1028
        68      1057
        74      1076
        80      1509
        98      1596
        c4      1250
        cc      1277
        f4      1555
       100      1536
       148      1561
       194      1523
       1d4      1250
       1ec      1277
       204      1066
       214      1334
       228      1356
       238      1413
       274      1411
       288      1451
       29c      1436
       2e8      1434
       324      1382
       328      1066
       340      1043
       350      1010
       35c      1028
       390      1010
       39c      1028
       3ac      1057
       3b4      1076
       3bc      1509
       3c8      1596
       3f0      1250
       3f4      1277
       404      1555
       410      1536
       454      1561
       4a0      1523
       4e0      1250
       4f8      1277
       540      1066
       550      1334
       560      1356
       570      1413
       5b0      1411
       5c4      1451
       5d8      1436
       624      1434
       674      1382
       678      1066
       684      1043
       68c      1010
       698      1028
       6a4      1108
       6b8      1116
       6bc       965
       6ec      1596
       71c      1523
       738      1010
       78c      1596
       7d4      1523
       7f0      1010

Inlined functions (count = 3)
 0x1dadb5f42949 <SharedFunctionInfo itemCheck>
 0x1dadb5f42991 <SharedFunctionInfo bottomUpTree>
 0x1dadb5f429d9 <SharedFunctionInfo TreeNode>

Deoptimization Input Data (deopt points = 41)
 index  bytecode-offset    pc
     0                6    NA 
     1                6    NA 
     2               30    NA 
     3                1    NA 
     4                1    NA 
     5                2    NA 
     6                8    NA 
     7               22    NA 
     8               30    NA 
     9               30    NA 
    10               30    NA 
    11               46    NA 
    12               46    NA 
    13               26    NA 
    14               26    NA 
    15               26    NA 
    16                6    NA 
    17                1    NA 
    18                2    NA 
    19                8    NA 
    20               22    NA 
    21                6    NA 
    22               46    NA 
    23               26    NA 
    24               26    NA 
    25               46    NA 
    26               46    NA 
    27               30    NA 
    28               30    NA 
    29               20   148 
    30               34   194 
    31               26   274 
    32               42   2e8 
    33               20   454 
    34               34   4a0 
    35               26   5b0 
    36               42   624 
    37               42   6b8 
    38               38   6e8 
    39               38   760 
    40               38   814 

Safepoints (stack slots = 22, entries = 16, byte size = 124)
0x126748ec8    148  slots (sp->fp): 0001000100001100000000  deopt     29 trampoline:    924
0x126748f14    194  slots (sp->fp): 0001100100001100000000  deopt     30 trampoline:    928
0x126748ff4    274  slots (sp->fp): 0000101100001100000000  deopt     31 trampoline:    92c
0x126749068    2e8  slots (sp->fp): 0000001100001100000000  deopt     32 trampoline:    930
0x1267491d4    454  slots (sp->fp): 0000010100000000000000  deopt     33 trampoline:    934
0x126749220    4a0  slots (sp->fp): 0001010100000000000000  deopt     34 trampoline:    938
0x126749330    5b0  slots (sp->fp): 0000011100000000000000  deopt     35 trampoline:    93c
0x1267493a4    624  slots (sp->fp): 0000001100000000000000  deopt     36 trampoline:    940
0x126749438    6b8  slots (sp->fp): 0000001100000000000000  deopt     37 trampoline:    944
0x126749468    6e8  slots (sp->fp): 0000000100001100000000  deopt     38 trampoline:    948
0x12674947c    6fc  slots (sp->fp): 0001000100001100000000
0x1267494ac    72c  slots (sp->fp): 0001110100001100000000
0x1267494e0    760  slots (sp->fp): 0000000100000000000000  deopt     39 trampoline:    94c
0x126749518    798  slots (sp->fp): 0000010100000000000000
0x126749564    7e4  slots (sp->fp): 0001011100000000000000
0x126749594    814  slots (sp->fp): 0000000100000000000000  deopt     40 trampoline:    950

RelocInfo (size = 375)
0x126748df4  full embedded object  (0x1dadb5f4b821 <JSFunction bottomUpTree (sfi = 0x1dadb5f42991)>)
0x126748e4c  full embedded object  (0x1dadb5f49259 <Map[28](HOLEY_ELEMENTS)>)
0x126748e64  full embedded object  (0x1dadb5f49201 <Map[28](HOLEY_ELEMENTS)>)
0x126748e6c  full embedded object  (0x1dadb5f49181 <Map[28](HOLEY_ELEMENTS)>)
0x126748f84  full embedded object  (0x1dadb5f4b951 <JSFunction itemCheck (sfi = 0x1dadb5f42949)>)
0x12674942c  full embedded object  (0x234724400109 <NativeContext[12e]>)
0x1267495d0  constant pool (size 50)
0x126749630  deopt script offset  (404)
0x126749630  deopt inlining id  (ffffffffffffffff)
0x126749630  deopt reason  (not a Smi)
0x126749630  deopt index
0x126749634  deopt script offset  (404)
0x126749634  deopt inlining id  (ffffffffffffffff)
0x126749634  deopt reason  (not a Smi)
0x126749634  deopt index
0x126749638  deopt script offset  (583)
0x126749638  deopt inlining id  (0)
0x126749638  deopt reason  (overflow)
0x126749638  deopt index
0x12674963c  deopt script offset  (5e5)
0x12674963c  deopt inlining id  (1)
0x12674963c  deopt reason  (not a Smi)
0x12674963c  deopt index
0x126749640  deopt script offset  (613)
0x126749640  deopt inlining id  (1)
0x126749640  deopt reason  (overflow)
0x126749640  deopt index
0x126749644  deopt script offset  (4e2)
0x126749644  deopt inlining id  (2)
0x126749644  deopt reason  (Smi)
0x126749644  deopt index
0x126749648  deopt script offset  (4fd)
0x126749648  deopt inlining id  (2)
0x126749648  deopt reason  (Smi)
0x126749648  deopt index
0x12674964c  deopt script offset  (42a)
0x12674964c  deopt inlining id  (ffffffffffffffff)
0x12674964c  deopt reason  (wrong call target)
0x12674964c  deopt index
0x126749650  deopt script offset  (583)
0x126749650  deopt inlining id  (0)
0x126749650  deopt reason  (not a Smi)
0x126749650  deopt index
0x126749654  deopt script offset  (583)
0x126749654  deopt inlining id  (0)
0x126749654  deopt reason  (overflow)
0x126749654  deopt index
0x126749658  deopt script offset  (5ab)
0x126749658  deopt inlining id  (0)
0x126749658  deopt reason  (wrong map)
0x126749658  deopt index
0x12674965c  deopt script offset  (59a)
0x12674965c  deopt inlining id  (0)
0x12674965c  deopt reason  (not a Smi)
0x12674965c  deopt index
0x126749660  deopt script offset  (59a)
0x126749660  deopt inlining id  (0)
0x126749660  deopt reason  (overflow)
0x126749660  deopt index
0x126749664  deopt script offset  (42a)
0x126749664  deopt inlining id  (ffffffffffffffff)
0x126749664  deopt reason  (not a Smi)
0x126749664  deopt index
0x126749668  deopt script offset  (42a)
0x126749668  deopt inlining id  (ffffffffffffffff)
0x126749668  deopt reason  (overflow)
0x126749668  deopt index
0x12674966c  deopt script offset  (413)
0x12674966c  deopt inlining id  (ffffffffffffffff)
0x12674966c  deopt reason  (overflow)
0x12674966c  deopt index
0x126749670  deopt script offset  (434)
0x126749670  deopt inlining id  (ffffffffffffffff)
0x126749670  deopt reason  (wrong call target)
0x126749670  deopt index
0x126749674  deopt script offset  (613)
0x126749674  deopt inlining id  (1)
0x126749674  deopt reason  (overflow)
0x126749674  deopt index
0x126749678  deopt script offset  (4e2)
0x126749678  deopt inlining id  (2)
0x126749678  deopt reason  (Smi)
0x126749678  deopt index
0x12674967c  deopt script offset  (4fd)
0x12674967c  deopt inlining id  (2)
0x12674967c  deopt reason  (Smi)
0x12674967c  deopt index
0x126749680  deopt script offset  (42a)
0x126749680  deopt inlining id  (ffffffffffffffff)
0x126749680  deopt reason  (wrong call target)
0x126749680  deopt index
0x126749684  deopt script offset  (434)
0x126749684  deopt inlining id  (ffffffffffffffff)
0x126749684  deopt reason  (wrong call target)
0x126749684  deopt index
0x126749688  deopt script offset  (45c)
0x126749688  deopt inlining id  (ffffffffffffffff)
0x126749688  deopt reason  (Insufficient type feedback for generic named access)
0x126749688  deopt index
0x12674968c  deopt script offset  (413)
0x12674968c  deopt inlining id  (ffffffffffffffff)
0x12674968c  deopt reason  (overflow)
0x12674968c  deopt index
0x126749690  deopt script offset  (42a)
0x126749690  deopt inlining id  (ffffffffffffffff)
0x126749690  deopt reason  (overflow)
0x126749690  deopt index
0x126749694  deopt script offset  (59a)
0x126749694  deopt inlining id  (0)
0x126749694  deopt reason  (overflow)
0x126749694  deopt index
0x126749698  deopt script offset  (59a)
0x126749698  deopt inlining id  (0)
0x126749698  deopt reason  (not a Smi)
0x126749698  deopt index
0x12674969c  deopt script offset  (5ab)
0x12674969c  deopt inlining id  (0)
0x12674969c  deopt reason  (wrong map)
0x12674969c  deopt index
0x1267496a0  deopt script offset  (583)
0x1267496a0  deopt inlining id  (0)
0x1267496a0  deopt reason  (not a Smi)
0x1267496a0  deopt index
0x1267496a4  deopt script offset  (600)
0x1267496a4  deopt inlining id  (1)
0x1267496a4  deopt reason  ((unknown))
0x1267496a4  deopt index
0x1267496a8  deopt script offset  (619)
0x1267496a8  deopt inlining id  (1)
0x1267496a8  deopt reason  ((unknown))
0x1267496a8  deopt index
0x1267496ac  deopt script offset  (585)
0x1267496ac  deopt inlining id  (0)
0x1267496ac  deopt reason  ((unknown))
0x1267496ac  deopt index
0x1267496b0  deopt script offset  (59c)
0x1267496b0  deopt inlining id  (0)
0x1267496b0  deopt reason  ((unknown))
0x1267496b0  deopt index
0x1267496b4  deopt script offset  (600)
0x1267496b4  deopt inlining id  (1)
0x1267496b4  deopt reason  ((unknown))
0x1267496b4  deopt index
0x1267496b8  deopt script offset  (619)
0x1267496b8  deopt inlining id  (1)
0x1267496b8  deopt reason  ((unknown))
0x1267496b8  deopt index
0x1267496bc  deopt script offset  (585)
0x1267496bc  deopt inlining id  (0)
0x1267496bc  deopt reason  ((unknown))
0x1267496bc  deopt index
0x1267496c0  deopt script offset  (59c)
0x1267496c0  deopt inlining id  (0)
0x1267496c0  deopt reason  ((unknown))
0x1267496c0  deopt index
0x1267496c4  deopt script offset  (454)
0x1267496c4  deopt inlining id  (ffffffffffffffff)
0x1267496c4  deopt reason  ((unknown))
0x1267496c4  deopt index
0x1267496c8  deopt script offset  (3c5)
0x1267496c8  deopt inlining id  (ffffffffffffffff)
0x1267496c8  deopt reason  ((unknown))
0x1267496c8  deopt index
0x1267496cc  deopt script offset  (3f2)
0x1267496cc  deopt inlining id  (ffffffffffffffff)
0x1267496cc  deopt reason  ((unknown))
0x1267496cc  deopt index
0x1267496d0  deopt script offset  (3f2)
0x1267496d0  deopt inlining id  (ffffffffffffffff)
0x1267496d0  deopt reason  ((unknown))
0x1267496d0  deopt index

--- End code ---
[completed compiling 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> (target TURBOFAN_JS) OSR - took 0.000, 5.625, 1.667 ms]
[completed optimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)> (target TURBOFAN_JS) OSR]
[OSR - compilation finished. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: prepare for on stack replacement (OSR)): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e55b41 <Code MAGLEV>, opt id 8, bytecode offset 26, deopt exit 42, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x000126748c3c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x1ae954e56a11 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
[OSR - entry. function: work, osr offset: 38]
[bailout (kind: deopt-eager, reason: Insufficient type feedback for generic named access): begin. deoptimizing 0x1dadb5f5a139 <JSFunction work (sfi = 0x1dadb5f42901)>, 0x08403aad3b49 <Code TURBOFAN_JS>, opt id 9, bytecode offset 46, deopt exit 22, FP to SP delta 160, caller SP 0x00016d81e418, pc 0x00012674968c]
