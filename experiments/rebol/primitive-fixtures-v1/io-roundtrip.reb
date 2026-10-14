Rebol [Title: "Exact byte primitive IO fixture"]
fixture: do (join system/script/path %common.reb)
commands: fixture/commands
arguments: system/options/args
fixture/check (all [block? arguments 3 = length? arguments]) "mode length observation arguments"
mode: first arguments
expected-length: to integer! second arguments
observation: to file! third arguments
fixture/check (not none? find ["collect" "stream" "indexed" "faults"] mode) "known IO mode"
fixture/check (all [expected-length >= 0 expected-length <= 131089]) "bounded fixture length"
if mode = "faults" [
    ; The diagnostic interposer arms on this explicit marker. The marker is
    ; still real stdout and is included in the expected output bytes.
    commands/write-stdout #{4D4543482D494F2D4641554C542D563100}
]
output: make binary! expected-length
chunks: make block! 16
position: 0
while [chunk: commands/read-stdin-chunk not none? chunk] [
    fixture/check (all [(length? chunk) > 0 (length? chunk) <= 32768]) "bounded nonempty read"
    append chunks length? chunk
    foreach byte chunk [
        fixture/check (byte = remainder position 256) "all byte values in exact order"
        position: position + 1
    ]
    fixture/check (position <= expected-length) "no extra input bytes"
    either mode = "stream" [commands/write-stdout chunk] [append output chunk]
]
fixture/equal position expected-length "complete input length"
fixture/equal commands/read-stdin-chunk none "stable EOF"
either mode = "indexed" [
    backing: make binary! (expected-length + 1)
    append backing 255
    append backing output
    commands/write-stdout (next backing)
] [if mode <> "stream" [commands/write-stdout output]]
commands/write-stdout #{}
save observation reduce ['schema "rebol-primitive-io-observation-v1"
    'mode mode 'bytes position 'chunks chunks 'eof true]
quit/return 0
