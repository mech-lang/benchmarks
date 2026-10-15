Rebol [Title: "Unchanged knucleotide complete-map and final-capacity observation"]

context [
    check: func [condition message [string!]] [
        unless condition [do make error! rejoin ["Map observation failed: " message]]
    ]
    destination: get-env "MECH_REBOL_MAP_OBSERVATION"
    check (all [string? destination not empty? destination (first destination) = #"/"]) "absolute sidecar path"
    destination: to file! destination
    check (not exists? destination) "fresh sidecar path"
    main: join system/script/path %../../../archive/languages/rebol/20261013/drafts/private-v1/sources/knucleotide/main.reb
    do main
    user: system/contexts/user
    actual-widths: get in user 'widths
    actual-tables: get in user 'tables
    actual-sequence: get in user 'sequence
    check (actual-widths = [1 2 3 4 6 12 18]) "seven original widths"
    check (all [block? actual-tables (length? actual-tables) = 7 binary? actual-sequence]) "original map container and sequence"
    foreach actual-table actual-tables [check (map? actual-table) "actual map value"]

    ; This single generic runtime dump precedes every diagnostic pair copy.
    ; It writes the retained native format to stderr, not benchmark stdout.
    stats/dump-series -1

    observation: make binary! 65536
    append observation to binary! rejoin ["rebol-knucleotide-map-observation-v1^-7^-" length? actual-sequence "^/"]
    repeat index 7 [
        width: pick actual-widths index
        actual-table: pick actual-tables index
        entries: length? actual-table
        total: 0
        foreach [key count] actual-table [
            check (all [integer? key key >= 0 integer? count count > 0]) "integer key and positive count"
            total: total + count
        ]
        append observation to binary! rejoin ["map^-" width "^-" entries "^-" total "^/"]
        ; Preserve actual map iteration order for exact backing-series matching.
        foreach [key count] actual-table [
            append observation to binary! rejoin ["entry^-" width "^-" key "^-" count "^/"]
        ]
        append observation to binary! rejoin ["end^-" width "^/"]
    ]
    check ((length? observation) <= 1048576) "complete sidecar exceeds declared bound"
    write/binary destination observation
]
quit/return 0
