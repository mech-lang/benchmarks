# New Janet adaptation of the retained TypeScript binary-trees implementation.
# Original contributors and source lineage are retained in source-manifest-v1.json.
(defn tree [depth]
  (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))

(defn check [node]
  (if (node 0) (+ 1 (check (node 0)) (check (node 1))) 1))

(defn main [& args]
  (def depth (max 6 (scan-number (get args 1 "6"))))
  (print (string/format "stretch tree of depth %d\t check: %d"
           (inc depth) (check (tree (inc depth)))))
  (def retained (tree depth))
  (loop [d :range [4 (inc depth) 2]]
    (def count (math/pow 2 (+ 4 depth (- d))))
    (var total 0)
    (for i 0 count (+= total (check (tree d))))
    (print (string/format "%d\t trees of depth %d\t check: %d" count d total)))
  (print (string/format "long lived tree of depth %d\t check: %d"
           depth (check retained))))
