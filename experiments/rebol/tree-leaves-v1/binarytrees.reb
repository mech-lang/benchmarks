Rebol [Title: "Corrected N4 binarytrees identity and collection observation"]

context [
    check: func [condition message [string!]] [
        unless condition [do make error! rejoin ["Tree observation failed: " message]]
    ]
    arguments: system/options/args
    check (all [block? arguments 2 = length? arguments]) "N4 and observation-file arguments"
    check ((first arguments) = "4") "existing bounded N4 only"
    destination: second arguments
    check (all [string? destination not empty? destination (first destination) = #"/"]) "absolute sidecar path"
    destination: to file! destination
    check (not exists? destination) "fresh sidecar path"

    main: join system/script/path %main.reb
    ; DO loads the ordinary file into the user context. Keep options/args intact:
    ; its first element supplies N4 to the corrected main's io/size function.
    do main
    user: system/contexts/user
    make-node: get in user 'make-tree
    check-node: get in user 'check-tree
    root: get in user 'long-lived
    check ((get in user 'maximum-depth) = 6) "actual main maximum depth"
    check ((get in user 'n) = 4) "actual main input"

    seen: none
    nodes: 0
    leaves: 0
    internal: 0
    pairs: 0
    visit: func [node [block!] expected-depth [integer!] /local prior] [
        check ((length? node) = 2) "two fields per actual node"
        foreach prior seen [
            pairs: pairs + 1
            check (not same? prior node) "distinct actual node series"
        ]
        append/only seen node
        nodes: nodes + 1
        either expected-depth = 0 [
            check (all [none? first node none? second node]) "actual leaf fields"
            leaves: leaves + 1
        ] [
            check (all [block? first node block? second node]) "actual child blocks"
            internal: internal + 1
            visit (first node) (expected-depth - 1)
            visit (second node) (expected-depth - 1)
        ]
        none
    ]
    inspect: func [tree [block!] /local summary] [
        seen: make block! 127
        nodes: 0
        leaves: 0
        internal: 0
        pairs: 0
        visit tree 6
        summary: reduce [nodes leaves internal pairs]
        ; Keep only scalar observations. This list must not root children during
        ; the subsequent collector window; completed traversal frames are gone.
        seen: none
        summary
    ]
    before-tree: inspect root
    check (before-tree = [127 64 63 8001]) "complete distinct long-root graph"
    before-check: check-node root
    check (before-check = 127) "actual long-root checksum before churn"

    fresh-a: make-node 0
    fresh-b: make-node 0
    fresh-distinct: not same? fresh-a fresh-b
    check fresh-distinct "separate make-tree zero calls"
    check (all [(length? fresh-a) = 2 (length? fresh-b) = 2
        none? first fresh-a none? second fresh-a
        none? first fresh-b none? second fresh-b]) "fresh leaf shape"
    poke fresh-a 1 7
    isolated: all [(first fresh-a) = 7 none? second fresh-a
        none? first fresh-b none? second fresh-b (check-node root) = 127]
    check isolated "fresh leaf mutation isolation"
    fresh-a: none
    fresh-b: none

    before-stats: stats/profile
    before-recycles: before-stats/recycles
    repeat index 65536 [discarded: make binary! 1024]
    discarded: none
    after-stats: stats/profile
    after-recycles: after-stats/recycles
    check (after-recycles > before-recycles) "automatic collection actually observed"
    retained-root: same? root (get in user 'long-lived)
    check retained-root "actual global long-root identity retained"
    after-tree: inspect root
    check (after-tree = [127 64 63 8001]) "distinct graph survived collection"
    after-check: check-node root
    check (after-check = 127) "actual long-root checksum after churn"

    save destination reduce [
        'schema "rebol-binarytrees-work-observation-v1"
        'main-n 4 'main-maximum-depth 6
        'nodes-before first before-tree 'leaves-before second before-tree
        'internal-before third before-tree 'identity-pairs-before fourth before-tree
        'nodes-after first after-tree 'leaves-after second after-tree
        'internal-after third after-tree 'identity-pairs-after fourth after-tree
        'check-before before-check 'check-after after-check
        'fresh-leaf-calls 2 'fresh-leaves-distinct fresh-distinct
        'fresh-leaf-mutation-isolated isolated 'long-root-same retained-root
        'recycles-before before-recycles 'recycles-after after-recycles
        'discarded-buffer-count 65536 'discarded-buffer-capacity 1024
        'diagnostic-root-aliases 1 'diagnostic-node-lists-during-churn 0
        'manual-gc false 'gc-policy-changed false 'per-tree-frees-observed false
        'full-size-work-qualified false 'source-work-qualified false 'chart-admission false
    ]
]
quit/return 0
