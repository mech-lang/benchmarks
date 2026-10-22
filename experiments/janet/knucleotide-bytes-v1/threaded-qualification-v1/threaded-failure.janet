# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# Janet adaptation of the retained rolling-number TypeScript candidate.
(def queries ["GGT" "GGTA" "GGTATT" "GGTATTTTAATT" "GGTATTTTAATTTATAGT"])
(def codes {65 0 67 1 71 2 84 3 97 0 99 1 103 2 116 3})

(defn sequence []
  (var active false)
  (var finished false)
  (def encoded @"")
  # Retain one LF-delimited input line, also accepting CR and CRLF records.
  (each rawline (file/lines stdin)
    (each line (string/split "\n" (string/replace-all "\r" "\n" rawline))
      (cond
        (string/has-prefix? ";" line) nil
        active (if (string/has-prefix? ">" line)
                 (do (set active false) (set finished true))
                 (for i 0 (length line)
                   (buffer/push-byte encoded
                     (or (get codes (get line i)) (error "Invalid nucleotide in THREE record")))))
        (and (not finished)
             (or (= line ">THREE") (string/has-prefix? ">THREE " line)
                 (string/has-prefix? ">THREE\t" line))) (set active true))))
  encoded)

(defn histogram [bases width]
  (when (= width 6) (error "owned-thread-probe"))
  (def counts @{})
  (def modulus (math/pow 4 width))
  (var key 0)
  (for i 0 (length bases)
    (set key (mod (+ (* key 4) (get bases i)) modulus))
    (when (>= (inc i) width) (put counts key (inc (get counts key 0)))))
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
  (def widths [1 2 3 4 6 12 18])
  (def completion (ev/thread-chan 7))
  (each width widths
    (ev/thread (fn [w] (histogram bases w)) width :nt completion))
  (def tables @{})
  (repeat 7
    (def [signal table width] (ev/take completion))
    (unless (= signal :ok) (error (string "Histogram worker failed: " table)))
    (assert (find-index |(= $ width) widths) "Unknown histogram worker")
    (assert (= nil (get tables width)) "Duplicate histogram worker")
    (put tables width table))
  (each width [1 2]
    (def counts (tables width))
    (def entries (seq [[key count] :pairs counts] [key count]))
    (sort entries (fn [[ka ca] [kb cb]] (or (> ca cb) (and (= ca cb) (< ka kb)))))
    (each [key count] entries
      (print (string/format "%s %.3f" (decode key width)
               (/ (* 100 count) (+ (length bases) 1 (- width))))))
    (print))
  (each query queries
    (var key 0)
    (each byte (string/bytes query) (set key (+ (* key 4) (get codes byte))))
    (print (string/format "%d\t%s" (get (tables (length query)) key 0) query))))
