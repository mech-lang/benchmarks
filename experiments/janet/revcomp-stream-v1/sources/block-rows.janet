# SPDX-License-Identifier: Apache-2.0
# Locally authored derivative of source-v3/revcomp.janet; all helpers included.
(def complements (buffer/new-filled 256))
(eachp [base complement]
  {65 84 67 71 66 86 68 72 71 67 72 68 75 77 77 75 78 78
   83 83 82 89 85 65 84 65 87 87 86 66 89 82}
  (put complements base complement)
  (put complements (+ base 32) complement))

(defn write-record [header bases]
  (when header
    (print header)
    (def row @"")
    (def output (buffer/new 1048636))
    (var offset (dec (length bases)))
    (while (>= offset 0)
      (repeat (min 60 (inc offset))
        (def byte (get bases offset))
        (def complement (get complements byte))
        (when (= complement 0)
          (file/write stdout output)
          (def normalized (if (<= 97 byte 122) (- byte 32) byte))
          (error (string/format "Invalid IUPAC nucleotide byte %d at record offset %d" normalized offset)))
        (buffer/push-byte row complement)
        (-- offset))
      (buffer/push-string output row "\n")
      (buffer/clear row)
      (when (>= (length output) 1048576)
        (file/write stdout output)
        (buffer/clear output)))
    (file/write stdout output)))

(defn main [& args]
  (var header nil)
  (def bases @"")
  (each raw-line (file/lines stdin)
    (each line (string/split "\n" (string/replace-all "\r" "\n" raw-line))
      (cond
        (string/has-prefix? ">" line)
          (do (write-record header bases) (set header line) (buffer/clear bases))
        (and header (not (string/has-prefix? ";" line)))
          (buffer/push-string bases line))))
  (write-record header bases))
