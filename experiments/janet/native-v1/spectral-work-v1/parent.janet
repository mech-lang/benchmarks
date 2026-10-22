(var term-count 0)
(var product-count 0)
# SPDX-License-Identifier: Apache-2.0
# New Janet implementation of the Benchmarks Game spectral-norm requirement.
(defn coefficient [i j]
  (/ 1 (+ (/ (* (+ i j) (+ i j 1)) 2) i 1)))

(defn multiply [input transpose]
  (++ product-count)
  (def n (length input))
  (def result @[])
  (for i 0 n
    (var total 0)
    (for j 0 n
      (++ term-count)
      (+= total (* (input j) (if transpose (coefficient j i) (coefficient i j)))))
    (array/push result total))
  result)

(defn step [input]
  (multiply (multiply input false) true))

(defn main [& args]
  (def n (scan-number (get args 1 "100")))
  (var u (seq [i :range [0 n]] 1))
  (var v nil)
  (repeat 10
    (set v (step u))
    (set u (step v)))
  (var uv 0)
  (var vv 0)
  (for i 0 n
    (+= uv (* (u i) (v i)))
    (+= vv (* (v i) (v i))))
  (file/write stderr (string/format "%d %d\n" product-count term-count))
  (print (string/format "%.9f" (math/sqrt (/ uv vv)))))
