Rebol [Title: "General extension fixture assertions"]

fixture-support: get-env "MECH_REBOL_FIXTURE_SUPPORT"
if any [none? fixture-support empty? fixture-support (first fixture-support) <> #"/"] [
    do make error! "Absolute pinned fixture support directory required"
]
fixture-support: copy fixture-support
if (last fixture-support) <> #"/" [append fixture-support #"/"]
fixture-commands: do (join (to file! fixture-support) %clbg_primitives.reb)

context [
    commands: fixture-commands
    check: func [condition label [string!]] [
        unless condition [do make error! rejoin ["Fixture failed: " label]]
    ]
    equal: func [actual expected label [string!]] [
        unless actual = expected [do make error! rejoin ["Fixture mismatch: " label]]
    ]
    rejects: func [body [block!] message [string!] /local result] [
        result: try body
        unless error? result [do make error! rejoin ["Expected an error: " message]]
        ; Bind the retained C failure payload without inventing the runtime's
        ; surrounding error-object layout or top-level stderr serialization.
        unless find (mold result) message [
            do make error! rejoin ["Unexpected native error payload: " message]
        ]
    ]
    finish: func [label [string!]] [
        commands/write-stdout (to binary! rejoin ["ok " label "^/"])
        quit/return 0
    ]
]
