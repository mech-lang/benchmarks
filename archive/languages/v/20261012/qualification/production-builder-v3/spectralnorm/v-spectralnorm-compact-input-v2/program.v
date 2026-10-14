module main

import os
import strconv
import math
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}

fn apply(u []f64, transpose bool) []f64 {
    mut v := []f64{len: u.len}
    for i in 0 .. u.len {
        mut sum := 0.0
        for j in 0 .. u.len {
            denominator := (i + j) * (i + j + 1) / 2 + (if transpose { j } else { i }) + 1
            sum += u[j] / f64(denominator)
        }
        v[i] = sum
    }
    return v
}

fn main() {
    n := size(100)
    mut u := []f64{len: n, init: 1.0}
    mut v := []f64{len: n}
    for _ in 0 .. 10 {
        v = apply(apply(u, false), true)
        u = apply(apply(v, false), true)
    }
    mut uv := 0.0
    mut vv := 0.0
    for i in 0 .. n {
        uv += u[i] * v[i]
        vv += v[i] * v[i]
    }
    println('${math.sqrt(uv / vv):.9f}')
}
