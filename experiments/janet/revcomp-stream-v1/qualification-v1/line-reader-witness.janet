# SPDX-License-Identifier: Apache-2.0
# New Janet implementation of the Benchmarks Game reverse-complement requirement.
(def complements
  {65 84 67 71 66 86 68 72 71 67 72 68 75 77 77 75 78 78
   83 83 82 89 85 65 84 65 87 87 86 66 89 82})

(defn write-record [header bases]
  (when header
    (print header)
    (def row @"")
    (var visits 0)
    (for i 0 (length bases)
      (++ visits)
      (def byte (get bases (- (length bases) i 1)))
      (buffer/push-byte row (or (get complements byte) (error (string/format "Invalid IUPAC nucleotide byte %d at record offset %d" byte (- (length bases) i 1)))))
      (when (= (length row) 60)
        (file/write stdout row "\n")
        (buffer/clear row)))
    (when (> (length row) 0) (file/write stdout row "\n"))
    (eprintf "W %d %d\n" (length bases) visits)))

(defn main [& args]
  (var header nil)
  (def bases @"")
  (each raw-line (file/lines stdin)
    (each line (string/split "\n" (string/replace-all "\r" "\n" raw-line))
      (cond
        (string/has-prefix? ">" line)
          (do (write-record header bases) (set header line) (buffer/clear bases))
        (and header (not (string/has-prefix? ";" line)))
          (buffer/push-string bases (string/ascii-upper line)))))
  (write-record header bases))
