Rebol [Title: "Bounded Pi facade-call observation at N27"]
io: do (join system/script/path %../../../archive/languages/rebol/20261013/drafts/private-v1/support/clbg_io.reb)
big: do (join system/script/path %../../../archive/languages/rebol/20261013/drafts/private-v1/support/clbg_big.reb)

unless (io/size) = 27 [io/fail "Pi observation requires size 27"]
pi-sidecar-name: get-env "MECH_REBOL_PI_OBSERVATION"
unless all [string? pi-sidecar-name not empty? pi-sidecar-name (first pi-sidecar-name) = #"/"] [
    io/fail "Absolute Pi observation path required"
]
pi-sidecar: to file! pi-sidecar-name
if exists? pi-sidecar [io/fail "Pi observation path already exists"]
pi-original-floor-divide: get in big 'floor-divide
pi-call-count: 0
pi-records: make block! 256
big/floor-divide: func [a [binary!] b [binary!] /local record result] [
    pi-call-count: pi-call-count + 1
    record: reduce [((pi-call-count + 1) // 2)
        (either (remainder pi-call-count 2) = 1 [15] [16])
        (copy q) (copy r) (copy t) k emitted (copy a) (copy b)]
    result: pi-original-floor-divide a b
    append/only record (copy result)
    append/only pi-records record
    result
]

n: io/size
q: big/from-int 1
r: big/from-int 0
t: big/from-int 1
k: 1
emitted: 0
column: 0
output: make binary! 1024
while [emitted < n] [
    numerator3: big/add (big/multiply q (big/from-int 3)) r
    numerator4: big/add (big/multiply q (big/from-int 4)) r
    quotient3: big/floor-divide numerator3 t
    quotient4: big/floor-divide numerator4 t
    either (big/compare quotient3 quotient4) = 0 [
        digit: big/to-int quotient3
        if any [digit < 0 digit > 9] [io/fail "Invalid spigot digit"]
        append output (48 + digit)
        emitted: emitted + 1
        column: column + 1
        if column = 10 [
            append output io/ascii rejoin ["^-:" emitted "^/"]
            column: 0
        ]
        next-q: big/multiply q (big/from-int 10)
        next-r: big/multiply (big/subtract r (big/multiply (big/from-int digit) t)) (big/from-int 10)
        q: next-q
        r: next-r
    ] [
        factor: big/from-int ((2 * k) + 1)
        next-q: big/multiply q (big/from-int k)
        next-r: big/multiply (big/add (big/multiply (big/from-int 2) q) r) factor
        next-t: big/multiply t factor
        q: next-q
        r: next-r
        t: next-t
        k: k + 1
    ]
]
if column > 0 [
    loop (10 - column) [append output 32]
    append output io/ascii rejoin ["^-:" emitted "^/"]
]
io/write-output output

if any [pi-call-count = 0 (remainder pi-call-count 2) <> 0] [io/fail "Incomplete Pi call pairs"]
pi-log: to binary! rejoin ["rebol-pi-floor-observation-v1^-27^/"
    "pair^-source-line^-q^-r^-t^-k^-emitted^-numerator^-denominator^-quotient^/"]
foreach pi-record pi-records [
    repeat pi-index length? pi-record [
        if pi-index > 1 [append pi-log 9]
        pi-field: pick pi-record pi-index
        append pi-log either binary? pi-field [pi-field] [to binary! form pi-field]
    ]
    append pi-log 10
]
write pi-sidecar pi-log
