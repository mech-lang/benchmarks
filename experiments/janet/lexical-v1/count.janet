# Read the unmodified pinned Spork grammar; never evaluate application forms.
(def env (require "spork/fmt"))
(def make-tree (get-in env ['make-tree :value]))
(assert (function? make-tree) "Pinned source grammar binding unavailable")

(defn token-count [node]
  (if (= node "\n") 0
    (do
      (def [tag value] node)
      (case tag
        :comment 0
        :comment-last 0
        :span 1
        :string 1
        :buffer 1
        :rmform (+ 1 (token-count (value 2)))
        :top (sum (map token-count value))
        :array (+ 2 (sum (map token-count value)))
        :btuple (+ 2 (sum (map token-count value)))
        :ptuple (+ 2 (sum (map token-count value)))
        :struct (+ 2 (sum (map token-count value)))
        :table (+ 2 (sum (map token-count value)))
        (error (string "Unsupported lexical node " tag))))))

(defn main [& args]
  (def source (slurp (args 1)))
  # Native reader validation also rejects malformed/trailing source.
  (parse-all source)
  (print (token-count (make-tree source))))
