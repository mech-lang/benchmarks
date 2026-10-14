module main

import os
import strconv
import math.big
import strings
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}

fn main() {
    n := size(27)
    if n <= 0 {
        return
    }
    one := big.integer_from_int(1)
    three := big.integer_from_int(3)
    four := big.integer_from_int(4)
    ten := big.integer_from_int(10)
    mut q := one
    mut r := big.integer_from_int(0)
    mut t := one
    mut k := 1
    mut printed := 0
    mut line := strings.new_builder(32)
    for printed < n {
        numerator3 := q * three + r
        numerator4 := q * four + r
        digit3 := numerator3 / t
        digit4 := numerator4 / t
        if digit3 == digit4 {
            line.write_byte(u8(48 + digit3.int()))
            printed++
            if printed % 10 == 0 || printed == n {
                for _ in 0 .. (10 - printed % 10) % 10 {
                    line.write_byte(` `)
                }
                line.write_string('\t:${printed}\n')
                print(line.str())
                line.go_back_to(0)
            }
            r = (r - digit3 * t) * ten
            q = q * ten
        } else {
            factor := big.integer_from_int(2 * k + 1)
            r = (q * big.integer_from_int(2) + r) * factor
            q = q * big.integer_from_int(k)
            t = t * factor
            k++
        }
    }
}
