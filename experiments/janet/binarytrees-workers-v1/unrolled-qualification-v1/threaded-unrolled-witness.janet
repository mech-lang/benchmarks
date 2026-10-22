# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# New Janet adaptation of the retained TypeScript binary-trees implementation.
# Original contributors and source lineage are retained in source-manifest-v1.json.
(var allocations 0)
(var checks 0)
(var seen @{})
(defn tree [depth]
  (++ allocations)
  (def node (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))
  (assert (not (get seen node)) "Shared mutable tree node")
  (put seen node true)
  node)

(defn check [node]
  (++ checks)
  (def left (get node 0))
  (if left
    (do
      (def right (get node 1))
      (++ checks)
      (def left-left (get left 0))
      (def left-total (if left-left
        (+ 1 (check left-left) (check (get left 1))) 1))
      (++ checks)
      (def right-left (get right 0))
      (def right-total (if right-left
        (+ 1 (check right-left) (check (get right 1))) 1))
      (+ 1 left-total right-total))
    1))

(defn work [task]
  (set allocations 0)
  (set checks 0)
  (set seen @{})
  (def [depth workers id] task)
  (def rows @[])
  (loop [d :range [4 (inc depth) 2]]
    (def count (math/pow 2 (+ 4 depth (- d))))
    (def start (math/floor (/ (* count id) workers)))
    (def end (math/floor (/ (* count (inc id)) workers)))
    (var total 0)
    (for i start end (+= total (check (tree d))))
    (array/push rows [d (- end start) total]))
  [rows allocations checks (length seen)])

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
      (def row (get (get worker-results 0) row-index))
      (assert (= d (get row 0)) "Unexpected tree depth")
      (+= finished (get row 1))
      (+= total (get row 2)))
    (assert (= finished count) "Incomplete tree work")
    (print (string/format "%d\t trees of depth %d\t check: %d" count d total))
    (++ row-index))
  (print (string/format "long lived tree of depth %d\t check: %d"
           depth (check retained)))
  (file/write stderr (string/format "M %.0f %.0f %.0f\n" allocations checks (length seen)))
  (for id 0 workers
    (def result (get results id))
    (file/write stderr (string/format "W %.0f %.0f %.0f %.0f\n" id (get result 1) (get result 2) (get result 3)))))
