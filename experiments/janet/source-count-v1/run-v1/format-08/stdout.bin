(def
 complements
 {65 84
  66 86
  67 71
  68 72
  71 67
  72 68
  75 77
  77 75
  78 78
  82 89
  83 83
  84 65
  85 65
  86 66
  87 87
  89 82})
(defn
 write-record
 [header bases]
 (when
  header
  (print header)
  (def row @"")
  (for
   i
   0
   (length bases)
   (def
    byte
    (get
     bases
     (- (length bases) i 1)))
   (buffer/push-byte
    row
    (or
     (get complements byte)
     (error "Invalid IUPAC nucleotide")))
   (when
    (= (length row) 60)
    (file/write stdout row "\n")
    (buffer/clear row)))
  (when
   (> (length row) 0)
   (file/write stdout row "\n"))))
(defn
 main
 [& args]
 (def
  raw
  (string/replace-all
   "\r"
   "\n"
   (string/replace-all
    "\r\n"
    "\n"
    (file/read stdin :all))))
 (var header nil)
 (def bases @"")
 (each
  line
  (string/split "\n" raw)
  (cond
   (string/has-prefix? ">" line)
   (do
    (write-record header bases)
    (set header line)
    (buffer/clear bases))
   (and
    header
    (not
     (string/has-prefix? ";" line)))
   (buffer/push-string
    bases
    (string/ascii-upper line))))
 (write-record header bases))
