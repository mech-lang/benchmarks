(defn main [& args]
  (for depth 6 22
    (for workers 1 8
      (loop [d :range [4 (inc depth) 2]]
        (def count (math/pow 2 (+ 4 depth (- d))))
        (for id 0 workers
          (def start (math/floor (/ (* count id) workers)))
          (def end (math/floor (/ (* count (inc id)) workers)))
          (print (string/format "%d %d %d %d %d %d" depth workers d id start end)))))))
