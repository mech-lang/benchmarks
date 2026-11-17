# Paired Rust task controls

Same inputs, accepted turns, warmup and output/retention obligations, paired on the same machine. Rust is an independent AOT task implementation with typed input validation, change detection and owned publication. Rust uses native ownership; Mech additionally performs its runtime admission, dependency scheduling, budget accounting and turn summary. This measures the cost of completing the task through each path, not a language-wide speed claim. Compilation is outside the resident timer. Rust preparation is not presented as a Mech artifact or JIT metric.

| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |
| --- | ---: | ---: | ---: |
| capacity-growth / source | 0.000496867709 | 6.98570312e-08 | 7112.637 |
| capacity-growth / bytecode | 0.000497427767 | 6.98570312e-08 | 7120.654 |
| capacity-growth-7 / source | 0.000652063248 | 1.41080469e-07 | 4621.924 |
| capacity-growth-7 / bytecode | 0.000668571745 | 1.41080469e-07 | 4738.939 |
| capacity-growth-8 / source | 0.000590739551 | 1.550125e-07 | 3810.916 |
| capacity-growth-8 / bytecode | 0.00058812041 | 1.550125e-07 | 3794.019 |
| capacity-growth-9 / source | 0.000604631934 | 1.67513281e-07 | 3609.457 |
| capacity-growth-9 / bytecode | 0.00060475332 | 1.67513281e-07 | 3610.181 |
| capacity-growth-15 / source | 0.000677010254 | 1.76725781e-07 | 3830.852 |
| capacity-growth-15 / bytecode | 0.000673641862 | 1.76725781e-07 | 3811.792 |
| capacity-growth-16 / source | 0.000682833984 | 1.85514062e-07 | 3680.767 |
| capacity-growth-16 / bytecode | 0.000681119824 | 1.85514062e-07 | 3671.527 |
| capacity-growth-17 / source | 0.000695390755 | 1.97070312e-07 | 3528.643 |
| capacity-growth-17 / bytecode | 0.000695279948 | 1.97070312e-07 | 3528.081 |
| capacity-growth-31 / source | 0.000861517676 | 2.1188125e-07 | 4066.040 |
| capacity-growth-31 / bytecode | 0.000863161621 | 2.1188125e-07 | 4073.799 |
| capacity-growth-32 / source | 0.000889529102 | 2.35578906e-07 | 3775.928 |
| capacity-growth-32 / bytecode | 0.000895822591 | 2.35578906e-07 | 3802.643 |
| capacity-growth-33 / source | 0.000900842708 | 2.42415625e-07 | 3716.108 |
| capacity-growth-33 / bytecode | 0.00090771097 | 2.42415625e-07 | 3744.441 |
| capacity-growth-63 / source | 0.00126337933 | 2.64973437e-07 | 4767.947 |
| capacity-growth-63 / bytecode | 0.00126443835 | 2.64973437e-07 | 4771.944 |
| capacity-growth-64 / source | 0.00128779385 | 2.75814062e-07 | 4669.065 |
| capacity-growth-64 / bytecode | 0.00127057054 | 2.75814062e-07 | 4606.620 |
| capacity-growth-65 / source | 0.00128041048 | 1.67545313e-07 | 7642.174 |
| capacity-growth-65 / bytecode | 0.00128216038 | 1.67545313e-07 | 7652.619 |
