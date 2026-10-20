;; Untimed full-state comparison. Run as a script with only the pinned compiled
;; application/support classes and Clojure jars on the classpath.
(ns clbg.nbody.primitive-state-probe
  (:require [clbg.nbody.compact :as parent]
            [clbg.nbody.scalar-updates :as updates]
            [clbg.nbody.primitive-updates :as moves]))

(def implementations
  [{:name :parent :make parent/bodies :offset parent/offset-momentum
    :advance parent/advance :energy parent/energy}
   {:name :scalar-updates :make updates/bodies :offset updates/offset-momentum
    :advance updates/advance :energy updates/energy}
   {:name :primitive-updates :make moves/bodies :offset moves/offset-momentum
    :advance moves/advance :energy moves/energy}])

(defn raw-state [^objects system]
  (mapv (fn [i]
          (let [^doubles body (aget system (int i))]
            (mapv (fn [axis]
                    (Double/doubleToRawLongBits (aget body (int axis))))
                  (range 7))))
        (range 5)))

(defn check-equal [systems n step phase]
  (let [states (mapv (fn [[implementation system]]
                       {:name (:name implementation)
                        :state (raw-state system)
                        :energy (Double/doubleToRawLongBits
                                  (double ((:energy implementation) system)))})
                     systems)
        reference (first states)]
    (doseq [actual (rest states)]
      (when-not (= (:state reference) (:state actual))
        (throw (ex-info "N-body raw state differs"
                        {:n n :step step :phase phase :candidate (:name actual)
                         :reference (:state reference) :actual (:state actual)})))
      (when-not (= (:energy reference) (:energy actual))
        (throw (ex-info "N-body raw energy differs"
                        {:n n :step step :phase phase :candidate (:name actual)
                         :reference (:energy reference) :actual (:energy actual)}))))))

(defn check-case [n]
  (let [systems (mapv (fn [implementation]
                        [implementation ((:make implementation))])
                      implementations)]
    (check-equal systems n 0 :fresh-bodies)
    (doseq [[implementation system] systems]
      ((:offset implementation) system))
    (check-equal systems n 0 :after-momentum)
    (dotimes [step n]
      (doseq [[implementation system] systems]
        ((:advance implementation) system))
      (check-equal systems n (inc step) :after-advance))))

(defn -main [& arguments]
  (when (seq arguments)
    (throw (ex-info "This bounded probe takes no arguments" {})))
  (let [cases [0 1 2 3 10 100]]
    (doseq [n cases] (check-case n))
    (prn {:status :pass :qualification :untimed-raw-bit-state
          :cases cases :implementations 3 :state-slots-per-check 35
          :advance-function-invocations (* 3 (reduce + cases))
          :energy-checked-at-every-comparison true
          :inner-pair-store-counters :not-instrumented-source-proof-only})))

(apply -main *command-line-args*)
