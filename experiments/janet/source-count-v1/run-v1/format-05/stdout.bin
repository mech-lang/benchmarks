(def
 solar-mass
 (* 4 math/pi math/pi))
(def days-per-year 365.24)
(defn
 bodies
 []
 @[@[0 0 0 0 0 0 solar-mass]
   @[4.84143144246472
     -1.16032004402743
     -0.103622044471123
     (* 0.00166007664274404 days-per-year)
     (* 0.0076990111841974 days-per-year)
     (* -6.90460016972063e-05 days-per-year)
     (* 0.000954791938424327 solar-mass)]
   @[8.34336671824458
     4.1247985641243
     -0.403523417114321
     (* -0.00276742510726862 days-per-year)
     (* 0.00499852801234917 days-per-year)
     (* 2.30417297573764e-05 days-per-year)
     (* 0.000285885980666131 solar-mass)]
   @[12.8943695621391
     -15.1111514016986
     -0.223307578892656
     (* 0.00296460137564762 days-per-year)
     (* 0.00237847173959481 days-per-year)
     (* -2.96589568540238e-05 days-per-year)
     (* 4.36624404335156e-05 solar-mass)]
   @[15.3796971148509
     -25.919314609988
     0.179258772950371
     (* 0.00268067772490389 days-per-year)
     (* 0.00162824170038242 days-per-year)
     (* -9.51592254519716e-05 days-per-year)
     (* 5.15138902046611e-05 solar-mass)]])
(defn
 energy
 [system]
 (var total 0)
 (for
  i
  0
  5
  (def
   b
   (system i))
  (+=
   total
   (*
    0.5
    (b 6)
    (+
     (*
      (b 3)
      (b 3))
     (*
      (b 4)
      (b 4))
     (*
      (b 5)
      (b 5)))))
  (for
   j
   (inc i)
   5
   (def
    other
    (system j))
   (def
    dx
    (-
     (b 0)
     (other 0)))
   (def
    dy
    (-
     (b 1)
     (other 1)))
   (def
    dz
    (-
     (b 2)
     (other 2)))
   (-=
    total
    (/
     (*
      (b 6)
      (other 6))
     (math/sqrt
      (+
       (* dx dx)
       (* dy dy)
       (* dz dz)))))))
 total)
(defn
 advance
 [system dt]
 (for
  i
  0
  5
  (def
   a
   (system i))
  (for
   j
   (inc i)
   5
   (def
    b
    (system j))
   (def
    dx
    (-
     (a 0)
     (b 0)))
   (def
    dy
    (-
     (a 1)
     (b 1)))
   (def
    dz
    (-
     (a 2)
     (b 2)))
   (def
    squared
    (+
     (* dx dx)
     (* dy dy)
     (* dz dz)))
   (def
    magnitude
    (/
     dt
     (*
      squared
      (math/sqrt squared))))
   (def
    first
    (* (a 6) magnitude))
   (def
    second
    (* (b 6) magnitude))
   (put
    a
    3
    (-
     (a 3)
     (* dx second)))
   (put
    a
    4
    (-
     (a 4)
     (* dy second)))
   (put
    a
    5
    (-
     (a 5)
     (* dz second)))
   (put
    b
    3
    (+
     (b 3)
     (* dx first)))
   (put
    b
    4
    (+
     (b 4)
     (* dy first)))
   (put
    b
    5
    (+
     (b 5)
     (* dz first)))))
 (each
  b
  system
  (for
   axis
   0
   3
   (put
    b
    axis
    (+
     (b axis)
     (*
      dt
      (b
       (+ axis 3))))))))
(defn
 main
 [& args]
 (def
  n
  (scan-number
   (get args 1 "1000")))
 (def
  system
  (bodies))
 (for
  axis
  0
  3
  (var momentum 0)
  (each
   b
   system
   (+=
    momentum
    (*
     (b
      (+ axis 3))
     (b 6))))
  (put
   (system 0)
   (+ axis 3)
   (/ (- momentum) solar-mass)))
 (print
  (string/format
   "%.9f"
   (energy system)))
 (repeat
  n
  (advance system 0.01))
 (print
  (string/format
   "%.9f"
   (energy system))))
