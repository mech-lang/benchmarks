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
    path := os.getenv('MECH_V_WORK_TRACE')
    if path.len == 0 {
        panic('An isolated work trace path is required')
    }
    mut audit_trace := os.create(path) or { panic(err) }
    audit_trace.writeln('TRACE_V1|pidigits|compact|${n}') or { panic(err) }
    defer {
        audit_trace.writeln('END_V1') or { panic(err) }
        audit_trace.close()
    }
    mut audit_candidate := 0
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
        audit_candidate++
        audit_trace.writeln('DIV|${audit_candidate}|lower|${numerator3.str()}|${t.str()}|${digit3.str()}') or { panic(err) }
        audit_trace.writeln('DIV|${audit_candidate}|upper|${numerator4.str()}|${t.str()}|${digit4.str()}') or { panic(err) }
        if digit3 == digit4 {
            audit_trace.writeln('ACCEPT|${audit_candidate}|${digit3.str()}|${printed + 1}') or { panic(err) }
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
