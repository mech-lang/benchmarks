(var draw-count 0)
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

(defn repeat-record [count]
  # The fixed ALU sequence and 60-column wrapping repeat after this many bases.
  (def period (* 60 (length alu)))
  (def tile @"")
  (var position 0)
  (for i 0 period
    (buffer/push-byte tile (get alu position))
    (set position (% (inc position) (length alu)))
    (when (zero? (% (inc i) 60)) (buffer/push-byte tile 10)))
  (repeat (math/floor (/ count period)) (file/write stdout tile))
  (def row @"")
  (set position 0)
  (for i 0 (% count period)
    (buffer/push-byte row (get alu position))
    (set position (% (inc position) (length alu)))
    (when (= (length row) 60)
      (file/write stdout row "\n")
      (buffer/clear row)))
  (when (> (length row) 0) (file/write stdout row "\n")))

(defn random-record [count distribution]
  (var cumulative 0)
  (def thresholds (map (fn [[_ probability]] (+= cumulative probability)) distribution))
  (def alphabet (map first distribution))
  (def limit (dec (length distribution)))
  (def block @"")
  (var column 0)
  (for i 0 count
    # Ordinary unscaled LCG arithmetic and floating division for every draw.
    (++ draw-count)
    (set seed (% (+ (* seed 3877) 29573) 139968))
    (def value (/ seed 139968))
    (var lower 0)
    (var upper limit)
    (while (< lower upper)
      (def middle (math/floor (/ (+ lower upper) 2)))
      (if (>= value (thresholds middle))
        (set lower (inc middle))
        (set upper middle)))
    (def rank lower)
    (buffer/push-byte block (alphabet rank))
    (++ column)
    (when (= column 60)
      (buffer/push-byte block 10)
      (set column 0)
      (when (>= (length block) 65536)
        (file/write stdout block)
        (buffer/clear block))))
  (when (> column 0) (buffer/push-byte block 10))
  (when (> (length block) 0) (file/write stdout block)))

(defn main [& args]
  (def n (scan-number (get args 1 "1000")))
  (print ">ONE Homo sapiens alu")
  (repeat-record (* 2 n))
  (print ">TWO IUB ambiguity codes")
  (random-record (* 3 n) iub)
  (print ">THREE Homo sapiens frequency")
  (random-record (* 5 n) homo)
  (file/write stderr (string/format "%d %d\n" draw-count seed)))
