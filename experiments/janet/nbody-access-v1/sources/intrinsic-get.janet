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

(defn advance [system dt]
  (for i 0 5
    (def a (get system i))
    (for j (inc i) 5
      (def b (get system j))
      (def dx (- (get a 0) (get b 0)))
      (def dy (- (get a 1) (get b 1)))
      (def dz (- (get a 2) (get b 2)))
      (def squared (+ (* dx dx) (* dy dy) (* dz dz)))
      (def magnitude (/ dt (* squared (math/sqrt squared))))
      (def first (* (get a 6) magnitude))
      (def second (* (get b 6) magnitude))
      (put a 3 (- (get a 3) (* dx second)))
      (put a 4 (- (get a 4) (* dy second)))
      (put a 5 (- (get a 5) (* dz second)))
      (put b 3 (+ (get b 3) (* dx first)))
      (put b 4 (+ (get b 4) (* dy first)))
      (put b 5 (+ (get b 5) (* dz first)))))
  (each b system
    (for axis 0 3 (put b axis (+ (get b axis) (* dt (get b (+ axis 3))))))))

(defn main [& args]
  (def n (scan-number (get args 1 "1000")))
  (def system (bodies))
  (for axis 0 3
    (var momentum 0)
    (each b system (+= momentum (* (get b (+ axis 3)) (get b 6))))
    (put (get system 0) (+ axis 3) (/ (- momentum) solar-mass)))
  (print (string/format "%.9f" (energy system)))
  (repeat n (advance system 0.01))
  (print (string/format "%.9f" (energy system))))
