@codex review

Review `3d1b51a24040bd9aef7f8ac9850878c7e2e5a6f3` against `4657035c91bc255b1dc8ed2f6d4edd7eb548125c`.

The identity-route pass can resolve an integer comparison when both operands trace to the same SSA value on that route. It forwards the route to the existing store and continuation after private index admission. The existing effect and live-use checks still apply.

### Runtime and correctness

The complete 81-case run wins 77 of 81 against libdeflate and all 81 against the independent reference in both orders at 96 blocks per case per order. The matched mean positive slowdown over the fixed 18 cases fell from 3.165117% to 2.372963%, a reduction of 0.792154 percentage points.
The largest remaining paired deficit is 12.480657%. Averaging the worse order of each fixed case gives 2.479625%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 88.35 / 87.04 | 85.02 / 84.38 | 76.04 / 75.56 | +12.355% / +11.959% | +16.359% → +12.157% | 0.908830 → 0.675380 |
| `reymont-prefix-1024` | 65.83 / 66.04 | 65.25 / 65.46 | 59.00 / 59.08 | +10.927% / +14.056% | +14.196% → +12.481% | 0.788649 → 0.693370 |
| `prefix-random-8192` | 139.62 / 137.67 | 133.25 / 131.69 | 124.52 / 123.27 | +7.342% / +7.071% | +12.163% → +7.207% | 0.675697 → 0.400365 |
| `prefix-natural-1024` | 65.88 / 65.88 | 65.21 / 65.21 | 58.96 / 59.00 | +10.879% / +10.859% | +12.159% → +10.869% | 0.675481 → 0.603848 |
| `prefix-random-16384` | 243.54 / 240.08 | 233.42 / 230.10 | 235.88 / 236.79 | -1.033% / -2.296% | +2.096% → -1.667% | 0.116462 → 0.000000 |
| `16384-distribution-change` | 484.17 / 479.40 | 478.35 / 481.44 | 484.29 / 484.75 | -1.694% / -1.277% | -0.682% → -1.486% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 521.42 / 516.88 | 515.67 / 514.10 | 534.46 / 533.85 | -3.725% / -4.197% | -3.083% → -3.961% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 503.60 / 498.21 | 500.15 / 495.85 | 519.33 / 518.96 | -4.261% / -4.745% | -3.825% → -4.503% | 0.000000 → 0.000000 |
| `random-32769` | 513.94 / 512.02 | 505.75 / 509.69 | 528.21 / 529.27 | -4.458% / -3.755% | -3.089% → -4.107% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 514.17 / 509.37 | 508.27 / 506.08 | 528.71 / 529.00 | -4.432% / -4.914% | -3.539% → -4.673% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 506.77 / 497.29 | 502.02 / 494.06 | 521.33 / 519.69 | -4.492% / -4.903% | -4.016% → -4.698% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,107.56 / 1,104.69 | 1,110.19 / 1,104.44 | 1,149.92 / 1,150.23 | -3.745% / -4.408% | -3.926% → -4.077% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,111.33 / 1,111.12 | 1,107.50 / 1,108.00 | 1,161.44 / 1,162.71 | -5.175% / -5.052% | -4.723% → -5.113% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,121.77 / 1,121.00 | 1,120.44 / 1,113.77 | 1,171.50 / 1,170.44 | -4.695% / -5.001% | -4.321% → -4.848% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,110.29 / 1,110.52 | 1,109.42 / 1,108.56 | 1,162.46 / 1,163.77 | -4.792% / -4.779% | -4.190% → -4.785% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,304.56 / 2,303.50 | 2,301.65 / 2,294.23 | 2,471.88 / 2,476.90 | -7.147% / -7.507% | -7.040% → -7.327% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,703.00 / 4,702.65 | 4,704.81 / 4,700.10 | 5,058.46 / 5,057.35 | -6.987% / -7.132% | -7.051% → -7.060% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,567.46 / 18,571.90 | 18,576.04 / 18,564.33 | 20,342.96 / 20,319.44 | -8.635% / -8.542% | -8.644% → -8.588% | 0.000000 → 0.000000 |

The focused test verifies the signed and unsigned comparisons on a shared incoming word and checks that distinct words with the same range stay independent. The qualified artifact passed 162 exact success and alias checks, six named errors, 12 same-process recoveries, and 324 deployment smokes.
The phase’s diagnostic count for random 16 KiB fell from 132,220 to 107,900 instructions and from 42,444 to 30,284 branches. Production timings used the uninstrumented executable. The selected emission keeps every function extent and location and all other native function bytes.

An earlier complete run also won random 16 KiB in both orders. Its forward random 32 KiB ratios rose to 1.0474× for the existing build and 1.0861× for the candidate. The retained result of that earlier run is `575f6bd749d927640b0da5f603475d53a3e3c6bb6f9b9ee1aee44b4a44abf4cf`. The tables here use a fresh complete run on the same two executables.

The rebased source reproduced the timed candidate and control executables byte for byte.

### Artifact binding

- Encoder text is 65,464 B, lookup data 65,536 B, the whole const section 80,064 B, and the stripped executable 276,072 B. Peak stack is 4,864 B.
- Codec source SHA-256 is `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 is `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 is `dc477a188ab72bc560ee7ecaf4f57597a0b40381d9b0943bdcb18a55fcaff94e`.
- Bound worker SHA-256 is `ce6a368765c42dbae8cebda3f321e3b0f81ecb6b76c377b75128399f53954482`.
- Full timing result SHA-256 is `95fcd90d8405ac5556559f7c352c497013cc683043321238a517e4fec8b28df8`.
- Timing verification SHA-256 is `0023046e0ebede7b91991209586aa7c81f60a2adaf2f2e958ec399427de829cd`.
- The recipe appends `mech_compact_numeric_3956_vector` to `MECH_COMPACT_FORWARD_PHASE_ROUTES` and refreshes the phase allocation and layout profiles.

`MECH_COMPACT_PHASE_BLOCK_LAYOUT` target-profile SHA-256 is `0b7860049205a9e0470644bff6c4bbcdb2f1d20a30b5e0deecee345b6f7aaab4`.

```json
{
  "order": [
    0,
    204,
    168,
    176,
    192,
    68,
    160,
    152,
    40,
    76,
    84,
    64
  ],
  "literal_offset": null,
  "thread_jumps": true,
  "object_tail": {
    "code_bytes": 216,
    "reference_code_bytes": 272,
    "alignment": 64,
    "nop_fill": true
  }
}
```

`MECH_COMPACT_PHASE_REGISTER_WEIGHTS` target-profile SHA-256 is `0d2611666805fb6aee26a8787b8dc3fbe60075b5567919c6df41c144691efdbe`.

```json
{
  "expected_vcode": "VCode {\n  Entry block: 0\nBlock 0([]):\n    (original IR block: block0)\n    (successor: Block 1([VReg(vreg = 260, class = Int)]))\n  Inst 0: args %v193=x1 %v194=x2\n  Inst 1: ldr %v261, [%v193]\n  Inst 2: ldr %v260, [%v193, #8]\n  Inst 3: ldr %v259, [%v193, #16]\n  Inst 4: ldr %v258, [%v193, #24]\n  Inst 5: ldr %v257, [%v193, #32]\n  Inst 6: ldr %v256, [%v193, #40]\n  Inst 7: b label1\nBlock 1([VReg(vreg = 204, class = Int)]):\n    (original IR block: block6)\n    (successor: Block 2([]))\n  Inst 8: b label2\nBlock 2([]):\n    (original IR block: block14)\n    (successor: Block 3([]))\n  Inst 9: b label3\nBlock 3([]):\n    (original IR block: block15)\n    (successor: Block 4([]))\n  Inst 10: b label4\nBlock 4([]):\n    (original IR block: block16)\n    (successor: Block 5([]))\n  Inst 11: b label5\nBlock 5([]):\n    (original IR block: block17)\n    (successor: Block 6([]))\n  Inst 12: b label6\nBlock 6([]):\n    (original IR block: block18)\n    (successor: Block 7([]))\n    (successor: Block 8([]))\n  Inst 13: and %v255, %v204, #255\n  Inst 14: subs xzr, %v255, #0\n  Inst 15: cset %v254, ne\n  Inst 16: subs xzr, %v255, %v261\n  Inst 17: cset %v253, lo\n  Inst 18: and %v252, %v254, %v253\n  Inst 19: tbnz %v252, #0, label7 ; b label8\nBlock 7([]):\n    (successor: Block 9([VReg(vreg = 255, class = Int)]))\n  Inst 20: b label9\nBlock 8([]):\n    (successor: Block 13([]))\n  Inst 21: b label13\nBlock 9([VReg(vreg = 217, class = Int)]):\n    (original IR block: block24)\n    (successor: Block 10([]))\n  Inst 22: b label10\nBlock 10([]):\n    (original IR block: block33)\n    (successor: Block 11([]))\n  Inst 23: b label11\nBlock 11([]):\n    (original IR block: block34)\n    (successor: Block 19([]))\n    (successor: Block 12([]))\n  Inst 24: subs xzr, %v217, %v261\n  Inst 25: b.lo label19 ; b label12\nBlock 12([]):\n    (successor: Block 13([]))\n  Inst 26: b label13\nBlock 13([]):\n    (original IR block: block147)\n    (successor: Block 16([]))\n    (successor: Block 14([]))\n  Inst 27: subs xzr, %v255, #0\n  Inst 28: b.ne label16 ; b label14\nBlock 14([]):\n    (original IR block: block3)\n    (successor: Block 15([]))\n  Inst 29: str %v259, [%v194, #8]\n  Inst 30: str %v258, [%v194, #16]\n  Inst 31: str %v257, [%v194, #24]\n  Inst 32: str %v256, [%v194, #32]\n  Inst 33: str %v259, [%v194, #40]\n  Inst 34: str %v258, [%v194, #48]\n  Inst 35: ldr %v251, [%v193, #56]\n  Inst 36: str %v251, [%v194, #56]\n  Inst 37: str %v257, [%v194, #64]\n  Inst 38: str %v256, [%v194, #72]\n  Inst 39: ldr %v250, [%v193, #48]\n  Inst 40: str %v250, [%v194, #80]\n  Inst 41: b label15\nBlock 15([]):\n    (original IR block: block2)\n  Inst 42: movz %v249, #0\n  Inst 43: rets %v249=x0 %v249=x1\nBlock 16([]):\n    (original IR block: block151)\n    (successor: Block 17([]))\n  Inst 44: b label17\nBlock 17([]):\n    (original IR block: block153)\n    (successor: Block 18([]))\n  Inst 45: b label18\nBlock 18([]):\n    (original IR block: block7)\n    (successor: Block 1([VReg(vreg = 248, class = Int)]))\n  Inst 46: lsr %v248, %v204, #8\n  Inst 47: b label1\nBlock 19([]):\n    (original IR block: block45)\n    (successor: Block 20([]))\n  Inst 48: b label20\nBlock 20([]):\n    (original IR block: block46)\n    (successor: Block 21([]))\n  Inst 49: b label21\nBlock 21([]):\n    (original IR block: block50)\n    (successor: Block 22([]))\n  Inst 50: b label22\nBlock 22([]):\n    (original IR block: block51)\n    (successor: Block 23([]))\n  Inst 51: ldr %v247, [%v259, %v217, LSL #2]\n  Inst 52: b label23\nBlock 23([]):\n    (original IR block: block52)\n    (successor: Block 24([]))\n  Inst 53: b label24\nBlock 24([]):\n    (original IR block: block47)\n    (successor: Block 25([VReg(vreg = 217, class = Int)]))\n  Inst 54: b label25\nBlock 25([VReg(vreg = 225, class = Int)]):\n    (original IR block: block59)\n    (successor: Block 26([]))\n  Inst 55: b label26\nBlock 26([]):\n    (original IR block: block68)\n    (successor: Block 27([]))\n  Inst 56: b label27\nBlock 27([]):\n    (original IR block: block69)\n    (successor: Block 29([]))\n    (successor: Block 28([]))\n  Inst 57: subs xzr, %v225, %v255\n  Inst 58: b.hs label29 ; b label28\nBlock 28([]):\n    (successor: Block 43([]))\n  Inst 59: b label43\nBlock 29([]):\n    (original IR block: block73)\n    (successor: Block 30([]))\n  Inst 60: b label30\nBlock 30([]):\n    (original IR block: block226)\n    (successor: Block 31([]))\n  Inst 61: b label31\nBlock 31([]):\n    (original IR block: block74)\n    (successor: Block 32([]))\n  Inst 62: b label32\nBlock 32([]):\n    (original IR block: block70)\n    (successor: Block 33([]))\n  Inst 63: b label33\nBlock 33([]):\n    (original IR block: block78)\n    (successor: Block 34([]))\n  Inst 64: b label34\nBlock 34([]):\n    (original IR block: block89)\n    (successor: Block 35([]))\n  Inst 65: b label35\nBlock 35([]):\n    (original IR block: block90)\n    (successor: Block 36([]))\n  Inst 66: b label36\nBlock 36([]):\n    (original IR block: block94)\n    (successor: Block 37([]))\n  Inst 67: b label37\nBlock 37([]):\n    (original IR block: block95)\n    (successor: Block 38([]))\n  Inst 68: sub %v246, %v225, %v255\n  Inst 69: ldr %v245, [%v259, %v246, LSL #2]\n  Inst 70: b label38\nBlock 38([]):\n    (original IR block: block101)\n    (successor: Block 39([]))\n  Inst 71: b label39\nBlock 39([]):\n    (original IR block: block79)\n    (successor: Block 40([]))\n  Inst 72: b label40\nBlock 40([]):\n    (original IR block: block105)\n    (successor: Block 41([]))\n  Inst 73: b label41\nBlock 41([]):\n    (original IR block: block106)\n    (successor: Block 48([]))\n    (successor: Block 42([]))\n  Inst 74: subs xzr, %v245, %v247\n  Inst 75: b.hi label48 ; b label42\nBlock 42([]):\n    (successor: Block 43([]))\n  Inst 76: b label43\nBlock 43([]):\n    (original IR block: block113)\n    (successor: Block 44([]))\n  Inst 77: str %v247, [%v259, %v225, LSL #2]\n  Inst 78: b label44\nBlock 44([]):\n    (original IR block: block127)\n    (successor: Block 45([]))\n  Inst 79: b label45\nBlock 45([]):\n    (original IR block: block135)\n    (successor: Block 46([]))\n  Inst 80: b label46\nBlock 46([]):\n    (original IR block: block137)\n    (successor: Block 47([]))\n  Inst 81: b label47\nBlock 47([]):\n    (original IR block: block25)\n    (successor: Block 9([VReg(vreg = 244, class = Int)]))\n  Inst 82: add %v244, %v217, #1\n  Inst 83: b label9\nBlock 48([]):\n    (original IR block: block110)\n    (successor: Block 49([]))\n  Inst 84: str %v245, [%v259, %v225, LSL #2]\n  Inst 85: b label49\nBlock 49([]):\n    (original IR block: block121)\n    (successor: Block 50([]))\n  Inst 86: b label50\nBlock 50([]):\n    (original IR block: block60)\n    (successor: Block 25([VReg(vreg = 246, class = Int)]))\n  Inst 87: b label25\n}\n\nRegister operands: [Def: v193i fixed(p1i), Def: v194i fixed(p2i), Def: v261i reg, Use: v193i reg, Def: v260i reg, Use: v193i reg, Def: v259i reg, Use: v193i reg, Def: v258i reg, Use: v193i reg, Def: v257i reg, Use: v193i reg, Def: v256i reg, Use: v193i reg, Def: v255i reg, Use: v204i reg, Use: v255i reg, Def: v254i reg, Use: v255i reg, Use: v261i reg, Def: v253i reg, Def: v252i reg, Use: v254i reg, Use: v253i reg, Use: v252i reg, Use: v217i reg, Use: v261i reg, Use: v255i reg, Use: v259i reg, Use: v194i reg, Use: v258i reg, Use: v194i reg, Use: v257i reg, Use: v194i reg, Use: v256i reg, Use: v194i reg, Use: v259i reg, Use: v194i reg, Use: v258i reg, Use: v194i reg, Def: v251i reg, Use: v193i reg, Use: v251i reg, Use: v194i reg, Use: v257i reg, Use: v194i reg, Use: v256i reg, Use: v194i reg, Def: v250i reg, Use: v193i reg, Use: v250i reg, Use: v194i reg, Def: v249i reg, Use: v249i fixed(p0i), Use: v249i fixed(p1i), Def: v248i reg, Use: v204i reg, Def: v247i reg, Use: v259i reg, Use: v217i reg, Use: v225i reg, Use: v255i reg, Def: v246i reg, Use: v225i reg, Use: v255i reg, Def: v245i reg, Use: v259i reg, Use: v246i reg, Use: v245i reg, Use: v247i reg, Use: v247i reg, Use: v259i reg, Use: v225i reg, Def: v244i reg, Use: v217i reg, Use: v245i reg, Use: v259i reg, Use: v225i reg]\nRegister types: [types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::INVALID, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I8, types::I8, types::I8, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I8, types::I64, types::I64, types::I64, types::I64, types::I64, types::I8, types::I64, types::I64, types::I64, types::I64, types::I64, types::I8, types::I32, types::I64, types::I64, types::I64, types::I32, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64, types::I64]\nClobbers: []\n",
  "block_frequencies": [
    30,
    180,
    180,
    180,
    180,
    180,
    180,
    39,
    180,
    1846,
    1846,
    1846,
    180,
    180,
    30,
    30,
    150,
    150,
    150,
    1806,
    1806,
    1806,
    1806,
    1806,
    1806,
    4096,
    4096,
    4096,
    1806,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    3875,
    1806,
    1806,
    1806,
    1806,
    1806,
    1806,
    2290,
    2290,
    2290
  ],
  "scope": "Equal shares of all 22 named primary diagnostic cases. Absent visits map to zero before the frequency floor.",
  "power": 1.0,
  "maximum": 4096,
  "cases": [
    "320-overlap",
    "16384-distribution-change",
    "random-32769",
    "reymont-prefix-1024",
    "heldout-window-32767",
    "heldout-random-65537",
    "prefix-natural-1024",
    "prefix-natural-4096",
    "prefix-natural-8192",
    "prefix-random-4096",
    "prefix-random-8192",
    "prefix-random-16384",
    "prefix-random-32767",
    "prefix-random-32768",
    "prefix-random-32769",
    "prefix-random-33027",
    "prefix-random-65535",
    "prefix-random-65536",
    "prefix-random-65537",
    "prefix-random-131072",
    "prefix-random-262144",
    "prefix-random-1048576"
  ],
  "training_object_sha256": "089eaf7a425dd874288594fa2db7385fbfb4800dd560fc1fb2d6292d95c1112f",
  "training_vcode_sha256": "5a8507527b7019c7d2731374a73a4cf99fb1f7d97e6ddc591d353323c5bbc832",
  "block_counts_sha256": "c9a66fd9210d02fe8f1eee98d9ef1e892679d616dc674b91f4d6c8cd160426ac"
}
```

### Complete builds

The retained timer measures original source through final executable link with prebuilt compilers and fixed host support.
- Control source 2.172308 s link 0.035005 s source_through_link 2.210188 s strip 0.010815 s source_through_strip 2.221320 s.
- Candidate source 2.172916 s link 0.038617 s source_through_link 2.213127 s strip 0.010836 s source_through_strip 2.224269 s.
- libdeflate source 0.446879 s link 0.034677 s source_through_link 0.481813 s strip 0.010882 s source_through_strip 0.492892 s.
- Independent reference source 2.950389 s link 0.035104 s source_through_link 2.985823 s strip 0.010804 s source_through_strip 2.996746 s.
