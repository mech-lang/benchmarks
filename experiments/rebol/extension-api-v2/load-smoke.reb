Rebol [Title: "Nine-command general extension load observation"]
common-path: get-env "MECH_REBOL_FIXTURE_COMMON"
unless all [string? common-path not empty? common-path #"/" = first common-path] [
    do make error! "Absolute retained common fixture path required"
]
fixture: do (to file! common-path)
commands: fixture/commands
fixture/equal (commands/gmp-add #{2D3231} #{32}) #{2D3139} "add"
fixture/equal (commands/gmp-subtract #{32} #{3231}) #{2D3139} "subtract"
fixture/equal (commands/gmp-multiply #{2D313233} #{343536}) #{2D3536303838} "multiply"
fixture/equal (commands/gmp-floor-divide #{2D37} #{33}) #{2D33} "floor divide"
fixture/equal (commands/gmp-compare #{2D3130} #{2D39}) -1 "compare"
fixture/equal (commands/pcre-find #{FF} #{0080FF00} 1) [3 4] "byte match"
fixture/equal (commands/format-fixed 1.25 1) #{312E32} "half-even formatting smoke"
bytes: copy #{}
while [chunk: commands/read-stdin-chunk] [append bytes chunk]
fixture/equal bytes #{0080FF} "raw NUL and high bytes"
commands/write-stdout bytes
fixture/finish "extension-load-v2"
