Rebol [Title: "Owner-boundary fixture"]
context [
    values: [1 2
        3 4]
    f: func [x [integer!] /local y] [y: x + 1 y]
    while [chunk: read-chunk not none? chunk] [append values chunk]
    sort/compare values func [a b] [either a = b [false] [a < b]]
    case [
        empty? values []
        true [append values 5 clear values]
    ]
]
