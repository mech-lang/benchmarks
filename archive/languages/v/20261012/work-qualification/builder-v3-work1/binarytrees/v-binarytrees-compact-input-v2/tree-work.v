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
    audit_tree(tree, 'stretch', depth, 0, 0)
    println('stretch tree of depth ${depth}\t check: ${check(tree)}')
}

fn main() {
    n := size(10)
    maximum := if n < 6 { 6 } else { n }
    stretch(maximum + 1)
    long_lived := create(maximum)
    audit_tree(long_lived, 'long-before', maximum, 0, 0)
    for depth := 4; depth <= maximum; depth += 2 {
        count := 1 << (maximum - depth + 4)
        mut sum := 0
        for audit_index in 0 .. count {
            tree := create(depth)
            sum += check(tree)
            audit_tree(tree, 'temporary', depth, audit_index, sum)
        }
        println('${count}\t trees of depth ${depth}\t check: ${sum}')
    }
    audit_tree(long_lived, 'long-after', maximum, 0, 0)
    println('long lived tree of depth ${maximum}\t check: ${check(long_lived)}')
}

// Unscored isolated observer only; absent from every measured source.
fn audit_tree_walk(tree &Node, level int, mut seen map[u64]bool, mut trace os.File) int {
    if isnil(tree) {
        panic('Missing actual node')
    }
    address := unsafe { u64(usize(tree)) }
    if address == 0 || address in seen {
        panic('Repeated actual node address within one tree')
    }
    seen[address] = true
    left := unsafe { u64(usize(tree.left)) }
    right := unsafe { u64(usize(tree.right)) }
    trace.writeln('NODE|${address}|${left}|${right}|${level}') or { panic(err) }
    if level == 0 {
        if !isnil(tree.left) || !isnil(tree.right) {
            panic('Actual leaf has a child')
        }
        return 1
    }
    if level < 0 || isnil(tree.left) || isnil(tree.right) {
        panic('Actual internal node lacks both children')
    }
    return 1 + audit_tree_walk(tree.left, level - 1, mut seen, mut trace) +
        audit_tree_walk(tree.right, level - 1, mut seen, mut trace)
}
fn audit_tree(tree &Node, kind string, depth int, index int, cumulative int) {
    directory := os.getenv('MECH_V_TREE_TRACE')
    if directory.len == 0 || !os.is_dir(directory) {
        panic('An existing isolated tree trace directory is required')
    }
    path := os.join_path(directory, '${kind}-${depth}-${index}.trace')
    if os.exists(path) {
        panic('Duplicate root trace; previous evidence must not be overwritten')
    }
    mut trace := os.create(path) or { panic(err) }
    defer {
        trace.close()
    }
    address := unsafe { u64(usize(tree)) }
    trace.writeln('TRACE_TREE_V1|${kind}|${depth}|${index}|${address}|${cumulative}') or { panic(err) }
    mut seen := map[u64]bool{}
    count := audit_tree_walk(tree, depth, mut seen, mut trace)
    trace.writeln('END_TREE_V1|${count}|${seen.len}') or { panic(err) }
}
