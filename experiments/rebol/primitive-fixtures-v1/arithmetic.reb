Rebol [Title: "Signed unbounded decimal primitive fixtures"]
fixture: do (join system/script/path %common.reb)
commands: fixture/commands

fixture/equal (commands/gmp-add #{2D30303030} #{303030}) #{30} "canonical zero"
fixture/equal (commands/gmp-add #{2D3231} #{32}) #{2D3139} "signed add"
fixture/equal (commands/gmp-subtract #{32} #{3231}) #{2D3139} "signed subtract"
fixture/equal (commands/gmp-multiply #{2D313233} #{343536}) #{2D3536303838} "signed multiply"
fixture/equal (commands/gmp-multiply
    (to binary! "12345678901234567890")
    (to binary! "98765432109876543210"))
    (to binary! "1219326311370217952237463801111263526900") "product beyond u64"
fixture/equal (commands/gmp-floor-divide
    (to binary! "123456789012345678901234567890123456789") #{3130})
    (to binary! "12345678901234567890123456789012345678") "quotient beyond u64"
fixture/equal (commands/gmp-floor-divide
    (to binary! "-123456789012345678901234567890123456789") #{3130})
    (to binary! "-12345678901234567890123456789012345679") "negative unbounded floor"
foreach [a b expected] [
    #{37} #{33} #{32}
    #{2D37} #{33} #{2D33}
    #{37} #{2D33} #{2D33}
    #{2D37} #{2D33} #{32}
    #{2D36} #{33} #{2D32}
    #{30} #{2D33} #{30}
] [fixture/equal (commands/gmp-floor-divide a b) expected "floor signs and exact division"]
fixture/equal (commands/gmp-compare #{2D3130} #{2D39}) -1 "negative order"
fixture/equal (commands/gmp-compare #{30303032} #{32}) 0 "numeric equality"
fixture/equal (commands/gmp-compare
    (to binary! "18446744073709551616")
    (to binary! "18446744073709551615")) 1 "unbounded comparison"

backing: to binary! "x-0021"
saved-backing: copy backing
fixture/equal (commands/gmp-add (next backing) #{32}) #{2D3139} "nonzero input series index"
fixture/equal backing saved-backing "operand bytes unchanged"
first-result: commands/gmp-add #{31} #{32}
second-result: commands/gmp-add #{31} #{32}
fixture/check (not same? first-result second-result) "fresh result series"
poke first-result 1 57
fixture/equal second-result #{33} "result mutation does not alias"

foreach invalid [#{} #{2D} #{2B31} #{2031} #{3120} #{3100} #{312E30} #{FF}] [
    fixture/rejects [commands/gmp-add invalid #{31}] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-add #{31} invalid] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-subtract invalid #{31}] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-subtract #{31} invalid] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-multiply invalid #{31}] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-multiply #{31} invalid] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-floor-divide invalid #{31}] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-floor-divide #{31} invalid] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-compare invalid #{31}] "Invalid signed decimal binary or native allocation failure"
    fixture/rejects [commands/gmp-compare #{31} invalid] "Invalid signed decimal binary or native allocation failure"
]
foreach zero [#{30} #{303030} #{2D30}] [
    fixture/rejects [commands/gmp-floor-divide #{31} zero] "Invalid decimal value or zero divisor"
]
fixture/rejects [commands/gmp-add (tail backing) #{31}] "Invalid signed decimal binary or native allocation failure"
fixture/equal (commands/gmp-add #{34} #{35}) #{39} "valid call after rejected calls"
fixture/finish "arithmetic"
