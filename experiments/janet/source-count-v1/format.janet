# Native reader/pretty-printer projection. It never evaluates application forms.
(defn render [forms]
  (def output @"")
  (each form forms
    (buffer/push-string output (string/format "%80m" form) "\n"))
  (string output))

(defn main [& args]
  (def forms (parse-all (slurp (args 1))))
  (def output (render forms))
  (def reparsed (parse-all output))
  # %n preserves all values and tuple bracket flags without truncation or color.
  (assert (= (string/format "%n" forms) (string/format "%n" reparsed))
    "Reader tree changed after formatting")
  (assert (= output (render reparsed)) "Formatting is not idempotent")
  (file/write stdout output))
