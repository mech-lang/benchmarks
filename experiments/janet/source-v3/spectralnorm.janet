# SPDX-License-Identifier: Apache-2.0
# Janet spectral norm: reusable vectors and exact coefficient-denominator recurrence.
(defn multiply! [input output transpose]
  (def n (length input))
  (for i 0 n
    (var denominator (+ (/ (* i (inc i)) 2) (if transpose 1 (inc i))))
    (var increment (+ i (if transpose 2 1)))
    (var total 0)
    (for j 0 n
      (+= total (* (input j) (/ 1 denominator)))
      (+= denominator increment)
      (++ increment))
    (put output i total)))

(defn step! [input output temporary]
  (multiply! input temporary false)
  (multiply! temporary output true))

(defn main [& args]
  (def n (scan-number (get args 1 "100")))
  (def u (array/new-filled n 1))
  (def v (array/new-filled n 0))
  (def temporary (array/new-filled n 0))
  (repeat 10
    (step! u v temporary)
    (step! v u temporary))
  (var uv 0)
  (var vv 0)
  (for i 0 n
    (+= uv (* (u i) (v i)))
    (+= vv (* (v i) (v i))))
  (print (string/format "%.9f" (math/sqrt (/ uv vv)))))
