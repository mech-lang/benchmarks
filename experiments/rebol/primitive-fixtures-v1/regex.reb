Rebol [Title: "PCRE2 byte matching and offset fixtures"]
fixture: do (join system/script/path %common.reb)
commands: fixture/commands

fixture/equal (commands/pcre-find #{6162} #{7A61626162} 1) [2 4] "first byte match"
fixture/equal (commands/pcre-find #{6162} #{7A61626162} 4) [4 6] "later start"
fixture/equal (commands/pcre-find #{6162} #{7A61626162} 6) none "end without match"
fixture/equal (commands/pcre-find #{6162} #{4142} 1) none "case sensitive"
fixture/equal (commands/pcre-find #{} #{6162} 1) [1 1] "empty match"
fixture/equal (commands/pcre-find #{} #{6162} 3) [3 3] "empty match at end"
fixture/equal (commands/pcre-find #{} #{} 1) [1 1] "empty subject"
fixture/equal (commands/pcre-find #{FF} #{0080FF00} 1) [3 4] "high byte offsets"
fixture/equal (commands/pcre-find #{00FF} #{6100FF62} 1) [2 4] "embedded NUL pattern and subject"
fixture/equal (commands/pcre-find #{2E} #{0D0A} 1) [1 2] "dot includes CR under LF policy"
fixture/equal (commands/pcre-find #{2E} #{0D0A} 2) none "dot excludes LF"
fixture/equal (commands/pcre-find (to binary! "(?m)^b") #{610D62} 1) none "CR is not LF newline"
fixture/equal (commands/pcre-find (to binary! "(?m)^b") #{610A62} 1) [3 4] "LF multiline boundary"
fixture/equal (commands/pcre-find (to binary! "(a)(b)") #{6162} 1) [1 3] "complete match rather than capture offsets"

pattern-backing: #{786162}
subject-backing: #{797A6162}
fixture/equal (commands/pcre-find (next pattern-backing) (next subject-backing) 1)
    [2 4] "pattern and subject series indices"
fixture/equal pattern-backing #{786162} "pattern unchanged"
fixture/equal subject-backing #{797A6162} "subject unchanged"
first-result: commands/pcre-find #{61} #{61} 1
second-result: commands/pcre-find #{61} #{61} 1
fixture/check (not same? first-result second-result) "fresh match block"
poke first-result 1 99
fixture/equal second-result [1 2] "match results do not alias"

fixture/rejects [commands/pcre-find #{5B} #{61} 1] "PCRE2 pattern compilation failed"
fixture/rejects [commands/pcre-find #{61} #{61} 0] "Match offset outside byte subject"
fixture/rejects [commands/pcre-find #{61} #{61} -1] "Match offset outside byte subject"
fixture/rejects [commands/pcre-find #{61} #{61} 3] "Match offset outside byte subject"
; A pattern-local zero match limit forces a match-time failure in the ordinary
; byte interpreter. Disable start optimizations so they cannot bypass matching.
fixture/rejects [commands/pcre-find
    (to binary! "(*NO_START_OPT)(*LIMIT_MATCH=0)a") #{61} 1] "PCRE2 matching failed"
fixture/equal (commands/pcre-find #{61} #{61} 1) [1 2] "valid match after rejected calls"
fixture/finish "regex"
