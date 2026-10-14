module main

import os
import strconv
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}

struct Node {
    left &Node = unsafe { nil }
    right &Node = unsafe { nil }
}
fn create(depth int) &Node {
    if depth == 0 {
        return &Node{}
    }
    return &Node{left: create(depth - 1), right: create(depth - 1)}
}
fn check(tree &Node) int {
    if isnil(tree.left) {
        return 1
    }
    return 1 + check(tree.left) + check(tree.right)
}
fn stretch(depth int) {
    tree := create(depth)
    println('stretch tree of depth ${depth}\t check: ${check(tree)}')
}

struct TreeResult {
    depth int
    count int
    sum int
}
fn trees(depth int, maximum int) TreeResult {
    count := 1 << (maximum - depth + 4)
    mut sum := 0
    for _ in 0 .. count {
        tree := create(depth)
        sum += check(tree)
    }
    return TreeResult{depth: depth, count: count, sum: sum}
}
fn main() {
    n := size(10)
    maximum := if n < 6 { 6 } else { n }
    stretch(maximum + 1)
    long_lived := create(maximum)
    mut depth := 4
    for depth <= maximum {
        mut jobs := []thread TreeResult{}
        for _ in 0 .. 8 {
            if depth <= maximum {
                jobs << spawn trees(depth, maximum)
                depth += 2
            }
        }
        for job in jobs {
            result := job.wait()
            println('${result.count}\t trees of depth ${result.depth}\t check: ${result.sum}')
        }
    }
    println('long lived tree of depth ${maximum}\t check: ${check(long_lived)}')
}
