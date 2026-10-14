Rebol [Title: "Retained primitive results across default automatic GC"]
fixture: do (join system/script/path %common.reb)
commands: fixture/commands
arguments: system/options/args
fixture/check (all [block? arguments 1 = length? arguments]) "one observation file argument"
observation: to file! first arguments

operand: to binary! "123456789012345678901234567890"
operand-before: copy operand
sum-result: commands/gmp-add operand #{31}
match-result: commands/pcre-find #{00FF} #{6100FF62} 1
format-result: commands/format-fixed 0.0625 3
fresh-sum: commands/gmp-add operand #{31}
fixture/check (not same? sum-result fresh-sum) "separate live arithmetic results"
before: stats/profile
before-count: before/recycles
repeat index 65536 [
    discarded: make binary! 1024
    ; Exercise ordinary rejection cleanup repeatedly without changing GC policy.
    if (remainder index 256) = 0 [
        fixture/rejects [commands/gmp-floor-divide #{31} #{30}] "Invalid decimal value or zero divisor"
        fixture/rejects [commands/pcre-find #{5B} #{61} 1] "PCRE2 pattern compilation failed"
        discarded-result: commands/gmp-multiply #{3132333435} #{36373839}
        discarded-match: commands/pcre-find #{61} #{616261} 2
    ]
]
discarded: none
discarded-result: none
discarded-match: none
after: stats/profile
after-count: after/recycles
fixture/equal operand operand-before "live operand survived GC"
fixture/equal sum-result (to binary! "123456789012345678901234567891") "live arithmetic result survived GC"
fixture/equal fresh-sum sum-result "independent arithmetic result survived GC"
fixture/equal match-result [2 4] "live match result survived GC"
fixture/equal format-result #{302E303632} "live formatting result survived GC"
save observation reduce ['schema "rebol-primitive-gc-observation-v1"
    'before before-count 'after after-count 'discarded-buffer-count 65536
    'discarded-buffer-capacity 1024 'manual-gc false 'policy-changed false]
fixture/check (after-count > before-count) "automatic collector actually ran"
fixture/finish "gc-ownership"
