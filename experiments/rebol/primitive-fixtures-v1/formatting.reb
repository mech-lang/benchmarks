Rebol [Title: "Ordinary C fixed decimal formatting fixtures"]
fixture: do (join system/script/path %common.reb)
commands: fixture/commands

; Expected under LC_ALL=C and FE_TONEAREST. No runtime policy is changed here.
foreach [value digits expected] [
    0.0625 3 #{302E303632}
    0.1875 3 #{302E313838}
    -0.0625 3 #{2D302E303632}
    -0.1875 3 #{2D302E313838}
    2.675 2 #{322E3637}
    -2.675 2 #{2D322E3637}
    0.0 9 #{302E303030303030303030}
    -0.0 9 #{2D302E303030303030303030}
    1.23456789 9 #{312E323334353637383930}
    -0.169075164 9 #{2D302E313639303735313634}
    2.5 0 #{32}
    3.5 0 #{34}
    1.5 18 #{312E353030303030303030303030303030303030}
] [fixture/equal (commands/format-fixed value digits) expected "fixed decimal bytes"]
fixture/rejects [commands/format-fixed 1.0 -1] "Finite decimal and precision in0..18 required"
fixture/rejects [commands/format-fixed 1.0 19] "Finite decimal and precision in0..18 required"
fixture/equal (commands/format-fixed 1.0 0) #{31} "format after rejected precision"
fixture/finish "formatting"
