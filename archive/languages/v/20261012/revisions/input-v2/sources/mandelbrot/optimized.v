module main

import os
import strconv
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}
fn emit(data []u8) {
    mut output := os.stdout()
    output.write_string(data.bytestr()) or { panic(err) }
    output.flush()
}

struct PixelBlock {
    data []u8
}
@[direct_array_access]
fn pixel_byte(cr [8]f64, ci f64, lanes int) u8 {
    mut zr := [8]f64{}
    mut zi := [8]f64{}
    mut tr := [8]f64{}
    mut ti := [8]f64{}
    for _ in 0 .. 10 {
        for _ in 0 .. 5 {
            for lane in 0 .. 8 {
                zi[lane] = (zr[lane] + zr[lane]) * zi[lane] + ci
                zr[lane] = tr[lane] - ti[lane] + cr[lane]
                tr[lane] = zr[lane] * zr[lane]
                ti[lane] = zi[lane] * zi[lane]
            }
        }
        mut survivors := 0
        for lane in 0 .. lanes {
            if tr[lane] + ti[lane] <= 4.0 {
                survivors++
            }
        }
        if survivors == 0 {
            return 0
        }
    }
    mut bits := u8(0)
    for lane in 0 .. lanes {
        if tr[lane] + ti[lane] <= 4.0 {
            bits |= u8(0x80 >> lane)
        }
    }
    return bits
}
@[direct_array_access]
fn render(n int, first int, last int, x []f64) PixelBlock {
    stride := (n + 7) / 8
    scale := 2.0 / f64(n)
    mut pixels := []u8{len: (last - first) * stride}
    for y in first .. last {
        ci := f64(y) * scale - 1.0
        for block in 0 .. stride {
            lanes := if n - block * 8 < 8 { n - block * 8 } else { 8 }
            mut cr := [8]f64{}
            for lane in 0 .. lanes {
                cr[lane] = x[block * 8 + lane]
            }
            pixels[(y - first) * stride + block] = pixel_byte(cr, ci, lanes)
        }
    }
    return PixelBlock{data: pixels}
}
fn main() {
    n := size(200)
    scale := 2.0 / f64(n)
    mut x := []f64{len: n}
    for i in 0 .. n {
        x[i] = f64(i) * scale - 1.5
    }
    mut jobs := []thread PixelBlock{}
    for worker in 0 .. 8 {
        jobs << spawn render(n, n * worker / 8, n * (worker + 1) / 8, x)
    }
    print('P4\n${n} ${n}\n')
    for job in jobs {
        emit(job.wait().data)
    }
}
