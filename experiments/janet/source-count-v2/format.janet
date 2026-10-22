(import spork/fmt)
# Native reader/pretty-printer projection. It never evaluates application forms.
(defn render [forms source]
  (string (fmt/format source)))

(defn main [& args]
  (def raw (slurp (args 1)))
  (def forms (parse-all raw))
  (def output (render forms raw))
  (def reparsed (parse-all output))
  # %n preserves all values and tuple bracket flags without truncation or color.
  (assert (= (string/format "%n" forms) (string/format "%n" reparsed))
    "Reader tree changed after formatting")
  (assert (= output (render reparsed output)) "Formatting is not idempotent")
  (file/write stdout output))
