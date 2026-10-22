# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# New Janet adaptation of the retained TypeScript binary-trees implementation.
# Original contributors and source lineage are retained in source-manifest-v1.json.
(defn tree [depth]
  (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))

(defn check [node]
  (def left (get node 0))
  (if left
    (do
      (def right (get node 1))
      (def left-left (get left 0))
      (def left-total (if left-left
        (+ 1 (check left-left) (check (get left 1))) 1))
      (def right-left (get right 0))
      (def right-total (if right-left
        (+ 1 (check right-left) (check (get right 1))) 1))
      (+ 1 left-total right-total))
    1))

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
