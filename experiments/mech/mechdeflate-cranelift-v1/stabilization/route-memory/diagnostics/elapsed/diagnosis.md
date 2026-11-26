# B elapsed-time diagnosis

B passed the peak RSS gates against both controls. Against O its ordinary elapsed estimate was +0.0485%, with a simultaneous 95% interval of +0.0062% to +0.0909% and calibrated resolution of +0.0525%. The interval leaves the elapsed nonregression gate unresolved.

In the 36 ordinary paired blocks, B averaged 1.047 ms longer overall than O. Its native stage averaged 2.227 ms longer. Parsing averaged 1.752 ms shorter, the frontend averaged 0.626 ms longer, and the time outside the driver averaged 0.038 ms shorter. The native-stage difference was positive in each of the six session means. B retired about 20.1 million fewer instructions per block on average. The outer process timer does not explain the difference.

The separate host-report diagnostic used one warmup per actor and all six permutations of O, A and B. Each output matched the pinned artifacts. B's lowering and definition stage took a paired median 5.692 ms longer than O, with all six differences positive. A's paired median difference in the same stage was 4.001 ms. The two-worker route schedule retained 72 analysis requests, 44 CFG and dominance builds, 28 graph reuses, 10 loop-edge rewrites and 261 identity-edge rewrites for every actor. The host-report measurements are diagnostic observations.
