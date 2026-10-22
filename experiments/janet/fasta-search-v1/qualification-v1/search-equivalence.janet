# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# Janet adaptation of Ian Osgood's retained FASTA algorithm and constants.
(def alu
  (string "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG"
          "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA"
          "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT"
          "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA"
          "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG"
          "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC"
          "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA"))
(def iub
  [[97 0.27] [99 0.12] [103 0.12] [116 0.27] [66 0.02] [68 0.02]
   [72 0.02] [75 0.02] [77 0.02] [78 0.02] [82 0.02] [83 0.02]
   [86 0.02] [87 0.02] [89 0.02]])
(def homo [[97 0.3029549426680] [99 0.1979883004921]
           [103 0.1975473066391] [116 0.3015094502008]])
(var seed 42)

(defn rank-linear [value thresholds limit]
    (var rank 0)
    (while (and (< rank limit) (>= value (thresholds rank))) (++ rank))
  rank)

(defn rank-binary [value thresholds limit]
    (var lower 0)
    (var upper limit)
    (while (< lower upper)
      (def middle (math/floor (/ (+ lower upper) 2)))
      (if (>= value (thresholds middle))
        (set lower (inc middle))
        (set upper middle)))
    (def rank lower)
  rank)

(defn main [& args]
  (var checks 0)
  (each distribution [iub homo]
    (var cumulative 0)
    (def thresholds (map (fn [[_ probability]] (+= cumulative probability)) distribution))
    (def limit (dec (length thresholds)))
    (for state 0 139968
      (def value (/ state 139968))
      (assert (= (rank-linear value thresholds limit) (rank-binary value thresholds limit)))
      (++ checks)))
  (each thresholds [[0 0.5 1] [0.5 0.5 1] [0 0 1]]
    (each value [0 0.49999999999999994 0.5 0.5000000000000001 0.9999999999999999]
      (assert (= (rank-linear value thresholds 2) (rank-binary value thresholds 2)))
      (++ checks)))
  (print checks))
