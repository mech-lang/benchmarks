# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# New Janet adaptation of the retained TypeScript binary-trees implementation.
# Original contributors and source lineage are retained in source-manifest-v1.json.
(defn tree [depth]
  (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))

(defn check [node]
  (def left (get node 0))
  (if left (+ 1 (check left) (check (get node 1))) 1))

# This module-level worker captures no main-frame retained tree.
(defn work [task]
  (def [depth workers id] task)
  (def rows @[])
  (loop [d :range [4 (inc depth) 2]]
    (def count (math/pow 2 (+ 4 depth (- d))))
    (def start (math/floor (/ (* count id) workers)))
    (def end (math/floor (/ (* count (inc id)) workers)))
    (var total 0)
    (for i start end (+= total (check (tree d))))
    (array/push rows [d (- end start) total]))
  rows)

(defn main [& args]
  (def depth (max 6 (scan-number (get args 1 "6"))))
  (def workers (scan-number (get args 2 "7")))
  (assert (and (<= 1 workers 7) (= workers (math/floor workers))) "Expected 1..7 workers")
  (print (string/format "stretch tree of depth %d\t check: %d"
           (inc depth) (check (tree (inc depth)))))
  (def retained (tree depth))
  (def completion (ev/thread-chan workers))
  (for id 0 workers (ev/thread work [depth workers id] :nt completion))
  (def results (array/new-filled workers nil))
  (repeat workers
    (def [signal rows task] (ev/take completion))
    (unless (= signal :ok) (error (string "Tree worker failed: " rows)))
    (def [task-depth task-workers id] task)
    (assert (and (= depth task-depth) (= workers task-workers)
                 (<= 0 id) (< id workers) (= id (math/floor id))) "Unknown tree worker")
    (assert (= nil (get results id)) "Duplicate tree worker")
    (put results id rows))
  (var row-index 0)
  (loop [d :range [4 (inc depth) 2]]
    (def count (math/pow 2 (+ 4 depth (- d))))
    (var total 0)
    (var finished 0)
    (each worker-results results
      (def row (get worker-results row-index))
      (assert (= d (get row 0)) "Unexpected tree depth")
      (+= finished (get row 1))
      (+= total (get row 2)))
    (assert (= finished count) "Incomplete tree work")
    (print (string/format "%d\t trees of depth %d\t check: %d" count d total))
    (++ row-index))
  (print (string/format "long lived tree of depth %d\t check: %d"
           depth (check retained))))
