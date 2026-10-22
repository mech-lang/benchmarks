# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
# Janet adaptation of Michael Ferguson / Isaac Gouy's retained n-body algorithm.
(def solar-mass (* 4 math/pi math/pi))
(def days-per-year 365.24)

(defn bodies []
  @[@[0 0 0 0 0 0 solar-mass]
    @[4.84143144246472090 -1.16032004402742839 -0.103622044471123109
      (* 0.00166007664274403694 days-per-year) (* 0.00769901118419740425 days-per-year)
      (* -0.0000690460016972063023 days-per-year) (* 0.000954791938424326609 solar-mass)]
    @[8.34336671824457987 4.12479856412430479 -0.403523417114321381
      (* -0.00276742510726862411 days-per-year) (* 0.00499852801234917238 days-per-year)
      (* 0.0000230417297573763929 days-per-year) (* 0.000285885980666130812 solar-mass)]
    @[12.8943695621391310 -15.1111514016986312 -0.223307578892655734
      (* 0.00296460137564761618 days-per-year) (* 0.00237847173959480950 days-per-year)
      (* -0.0000296589568540237556 days-per-year) (* 0.0000436624404335156298 solar-mass)]
    @[15.3796971148509165 -25.9193146099879641 0.179258772950371181
      (* 0.00268067772490389322 days-per-year) (* 0.00162824170038242295 days-per-year)
      (* -0.0000951592254519715870 days-per-year) (* 0.0000515138902046611451 solar-mass)]])

(defn energy [system]
  (var total 0)
  (for i 0 5
    (def b (get system i))
    (+= total (* 0.5 (get b 6) (+ (* (get b 3) (get b 3)) (* (get b 4) (get b 4)) (* (get b 5) (get b 5)))))
    (for j (inc i) 5
      (def other (get system j))
      (def dx (- (get b 0) (get other 0)))
      (def dy (- (get b 1) (get other 1)))
      (def dz (- (get b 2) (get other 2)))
      (-= total (/ (* (get b 6) (get other 6)) (math/sqrt (+ (* dx dx) (* dy dy) (* dz dz)))))))
  total)

# Expand the same five-body integration graph into VM scalar registers.
# Gensyms keep all generated state and temporary bindings private.
(defmacro integrate [system dt steps]
  (def sys (gensym))
  (def timestep (gensym))
  (def names @[])
  (repeat 5 (array/push names (seq [field :range [0 7]] (gensym))))
  (defn slot [i field] (get (get names i) field))
  (def declarations @[])
  (def interactions @[])
  (def moves @[])
  (def stores @[])
  (for i 0 5
    (for field 0 7
      (array/push declarations ~(var ,(slot i field) (get (get ,sys ,i) ,field)))
      (array/push stores ~(put (get ,sys ,i) ,field ,(slot i field))))
    (for j (inc i) 5
      (array/push interactions
        ~(do
          (def dx (- ,(slot i 0) ,(slot j 0)))
          (def dy (- ,(slot i 1) ,(slot j 1)))
          (def dz (- ,(slot i 2) ,(slot j 2)))
          (def squared (+ (* dx dx) (* dy dy) (* dz dz)))
          (def magnitude (/ ,timestep (* squared (math/sqrt squared))))
          (def first (* ,(slot i 6) magnitude))
          (def second (* ,(slot j 6) magnitude))
          (-= ,(slot i 3) (* dx second))
          (-= ,(slot i 4) (* dy second))
          (-= ,(slot i 5) (* dz second))
          (+= ,(slot j 3) (* dx first))
          (+= ,(slot j 4) (* dy first))
          (+= ,(slot j 5) (* dz first)))))
    (for axis 0 3
      (array/push moves ~(+= ,(slot i axis) (* ,timestep ,(slot i (+ axis 3)))))))
  ~(do
    (def ,sys ,system)
    (def ,timestep ,dt)
    ,;declarations
    (repeat ,steps ,;interactions ,;moves)
    ,;stores))

(defn advance-n [system dt steps] (integrate system dt steps))

(defn main [& args]
  (def seed (scan-number (get args 1)))
  (def n (scan-number (get args 2)))
  (def dt (scan-number (get args 3)))
  (def system (bodies))
  (for i 0 5
    (def b (get system i))
    (for axis 0 3
      (put b axis (+ (get b axis) (* seed 0.03 (inc i) (inc axis))))
      (put b (+ axis 3) (+ (get b (+ axis 3)) (* 0.001 seed (- i axis)))))
    (when (> i 0) (put b 6 (* (get b 6) (+ 1 (* 0.01 seed (inc i)))))))
  (for axis 0 3
    (var momentum 0)
    (each b system (+= momentum (* (get b (+ axis 3)) (get b 6))))
    (put (get system 0) (+ axis 3) (/ (- momentum) solar-mass)))
  (advance-n system dt n)
  (each b system (each value b (print (string/format "%.17g" value)))))
