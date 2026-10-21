# SPDX-License-Identifier: Apache-2.0
# New Janet implementation using the unmodified published Spork regex library.
(import spork/regex)
(def patterns
  ["agggtaaa|tttaccct" "[cgt]gggtaaa|tttaccc[acg]" "a[act]ggtaaa|tttacc[agt]t"
   "ag[act]gtaaa|tttac[agt]ct" "agg[act]taaa|ttta[agt]cct" "aggg[acg]aaa|ttt[cgt]ccct"
   "agggt[cgt]aa|tt[acg]accct" "agggta[cgt]a|t[acg]taccct" "agggtaa[cgt]|[acg]ttaccct"])
(def replacements
  [["tHa[Nt]" "<4>"] ["aND|caN|Ha[DS]|WaS" "<3>"] ["a[NSt]|BY" "<2>"]
   ["<[^>]*>" "|"] ["\\|[^|][^|]*\\|" "-"]])

(defn main [& args]
  (def raw (or (file/read stdin :all) ""))
  (def bases (regex/replace-all (regex/compile ">[^\n]*\n|\n") "" raw))
  (each pattern patterns
    (print pattern " " (length (regex/find-all (regex/compile pattern) bases))))
  (var changed bases)
  (each [pattern replacement] replacements
    (set changed (regex/replace-all (regex/compile pattern) replacement changed)))
  (print)
  (print (length raw))
  (print (length bases))
  (print (length changed)))
