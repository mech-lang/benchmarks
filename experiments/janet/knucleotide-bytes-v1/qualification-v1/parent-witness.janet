# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# Janet adaptation of the retained rolling-number TypeScript candidate.
(def queries ["GGT" "GGTA" "GGTATT" "GGTATTTTAATT" "GGTATTTTAATTTATAGT"])
(def codes {65 0 67 1 71 2 84 3})

(defn sequence []
  (def raw (string/replace-all "\r" "\n"
              (string/replace-all "\r\n" "\n" (file/read stdin :all))))
  (var active false)
  (var finished false)
  (def selected @"")
  (each line (string/split "\n" raw)
    (cond
      (string/has-prefix? ";" line) nil
      active (if (string/has-prefix? ">" line)
               (do (set active false) (set finished true))
               (buffer/push-string selected line))
      (and (not finished)
           (or (= line ">THREE") (string/has-prefix? ">THREE " line)
               (string/has-prefix? ">THREE\t" line))) (set active true)))
  (map (fn [byte] (or (get codes byte) (error "Invalid nucleotide in THREE record")))
       (string/bytes (string/ascii-upper selected))))

(defn histogram [bases width]
  (def counts @{})
  (def modulus (math/pow 4 width))
  (var key 0)
  (for i 0 (length bases)
    (set key (% (+ (* key 4) (bases i)) modulus))
    (when (>= (inc i) width) (put counts key (inc (get counts key 0)))))
  (file/write stderr (string/format "H %d %d\n" width (length counts)))
  (def trace-entries (seq [[key count] :pairs counts] [key count]))
  (sort trace-entries (fn [[a _] [b _]] (< a b)))
  (each [key count] trace-entries
    (file/write stderr (string/format "%.0f %d\n" key count)))
  counts)

(defn decode [encoded width]
  (var key encoded)
  (def text @"")
  (repeat width
    (buffer/push-byte text (get "ACGT" (% key 4)))
    (set key (math/floor (/ key 4))))
  (string/reverse text))

(defn main [& args]
  (def bases (sequence))
  (each width [1 2]
    (def counts (histogram bases width))
    (def entries (seq [[key count] :pairs counts] [key count]))
    (sort entries (fn [[ka ca] [kb cb]] (or (> ca cb) (and (= ca cb) (< ka kb)))))
    (each [key count] entries
      (print (string/format "%s %.3f" (decode key width)
               (/ (* 100 count) (+ (length bases) 1 (- width))))))
    (print))
  (each query queries
    (var key 0)
    (each byte (string/bytes query) (set key (+ (* key 4) (get codes byte))))
    (print (string/format "%d\t%s" (get (histogram bases (length query)) key 0) query))))
