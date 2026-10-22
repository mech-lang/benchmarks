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
  (def tile (string alu alu))
  (loop [offset :range [0 count 60]]
    (def start (% offset (length alu)))
    (print (string/slice tile start (+ start (min 60 (- count offset)))))))

(defn random-record [count distribution]
  (var cumulative 0)
  (def thresholds (map (fn [[_ p]] (+= cumulative p)) distribution))
  (def alphabet (map first distribution))
  (defn draw []
    (++ draw-count)
    (set seed (% (+ (* seed 3877) 29573) 139968))
    (def value (/ seed 139968))
    (alphabet (find-index |(> $ value) thresholds)))
  (loop [offset :range [0 count 60]]
    (print (apply string/from-bytes
      (seq [i :range [0 (min 60 (- count offset))]] (draw))))))

(defn main [& args]
  (def n (scan-number (get args 1 "1000")))
  (print ">ONE Homo sapiens alu")
  (repeat-record (* 2 n))
  (print ">TWO IUB ambiguity codes")
  (random-record (* 3 n) iub)
  (print ">THREE Homo sapiens frequency")
  (random-record (* 5 n) homo)
  (file/write stderr (string/format "%d %d\n" draw-count seed)))
