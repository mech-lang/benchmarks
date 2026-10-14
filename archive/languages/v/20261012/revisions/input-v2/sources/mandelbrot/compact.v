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

fn main() {
    n := size(200)
    stride := (n + 7) / 8
    scale := 2.0 / f64(n)
    mut pixels := []u8{len: n * stride}
    for y in 0 .. n {
        ci := f64(y) * scale - 1.0
        for x in 0 .. n {
            cr := f64(x) * scale - 1.5
            mut zr := 0.0
            mut zi := 0.0
            mut inside := true
            for _ in 0 .. 50 {
                next_zr := zr * zr - zi * zi + cr
                zi = 2.0 * zr * zi + ci
                zr = next_zr
                if zr * zr + zi * zi > 4.0 {
                    inside = false
                    break
                }
            }
            if inside {
                pixels[y * stride + x / 8] |= u8(0x80 >> (x % 8))
            }
        }
    }
    print('P4\n${n} ${n}\n')
    emit(pixels)
}
