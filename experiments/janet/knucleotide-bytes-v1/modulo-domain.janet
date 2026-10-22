# Diagnostic only: exercise the exact positive, power-of-four key domain.
(defn main [& args]
  (var modulus 1)
  (var checks 0)
  (for width 1 19
    (set modulus (* modulus 4))
    (assert (= modulus (math/pow 4 width)))
    (defn check [key]
      (for base 0 4
        (def value (+ (* key 4) base))
        (assert (< value 274877906944))
        (assert (= (% value modulus) (mod value modulus)))
        (++ checks)))
    (each key [0 1 (/ modulus 2) (- modulus 2) (dec modulus)] (check key))
    (var key (dec modulus))
    (repeat 1000
      (set key (% (+ (* key 3) 7) modulus))
      (check key)))
  (print checks))
