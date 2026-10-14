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

struct VectorBlock {
    data []f64
}
@[direct_array_access]
fn product(u []f64, transpose bool, first int, last int) VectorBlock {
    mut v := []f64{len: last - first}
    extra := if transpose { 1 } else { 0 }
    for i in first .. last {
        mut d := i * (i + 1) / 2 + (if transpose { 0 } else { i }) + 1
        mut a := 0.0
        mut b := 0.0
        mut c := 0.0
        mut e := 0.0
        mut j := 0
        for j + 3 < u.len {
            d1 := d + i + j + 1 + extra
            d2 := d1 + i + j + 2 + extra
            d3 := d2 + i + j + 3 + extra
            a += u[j] / f64(d)
            b += u[j + 1] / f64(d1)
            c += u[j + 2] / f64(d2)
            e += u[j + 3] / f64(d3)
            d = d3 + i + j + 4 + extra
            j += 4
        }
        mut sum := (a + b) + (c + e)
        for j < u.len {
            sum += u[j] / f64(d)
            d += i + j + 1 + extra
            j++
        }
        v[i - first] = sum
    }
    return VectorBlock{data: v}
}
fn apply(u []f64, transpose bool) []f64 {
    mut jobs := []thread VectorBlock{}
    for worker in 0 .. 8 {
        jobs << spawn product(u, transpose, u.len * worker / 8, u.len * (worker + 1) / 8)
    }
    mut v := []f64{cap: u.len}
    for job in jobs {
        v << job.wait().data
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
