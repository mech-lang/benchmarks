module main

import os
import strconv
import math
const solar_mass = 4.0 * math.pi * math.pi
const days_per_year = 365.24
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}
fn arr_bodies() [][]f64 {
	return [
		[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, solar_mass],
		[4.84143144246472090e+00, -1.16032004402742839e+00, -1.03622044471123109e-01, 1.66007664274403694e-03 * days_per_year, 7.69901118419740425e-03 * days_per_year, -6.90460016972063023e-05 * days_per_year, 9.54791938424326609e-04 * solar_mass],
		[8.34336671824457987e+00, 4.12479856412430479e+00, -4.03523417114321381e-01, -2.76742510726862411e-03 * days_per_year, 4.99852801234917238e-03 * days_per_year, 2.30417297573763929e-05 * days_per_year, 2.85885980666130812e-04 * solar_mass],
		[1.28943695621391310e+01, -1.51111514016986312e+01, -2.23307578892655734e-01, 2.96460137564761618e-03 * days_per_year, 2.37847173959480950e-03 * days_per_year, -2.96589568540237556e-05 * days_per_year, 4.36624404335156298e-05 * solar_mass],
		[1.53796971148509165e+01, -2.59193146099879641e+01, 1.79258772950371181e-01, 2.68067772490389322e-03 * days_per_year, 1.62824170038242295e-03 * days_per_year, -9.51592254519715870e-05 * days_per_year, 5.15138902046611451e-05 * solar_mass],
	]
}


fn energy(b [][]f64) f64 {
    mut e := 0.0
    for i in 0 .. b.len {
        e += 0.5 * b[i][6] * (b[i][3] * b[i][3] + b[i][4] * b[i][4] + b[i][5] * b[i][5])
        for j in i + 1 .. b.len {
            dx := b[i][0] - b[j][0]
            dy := b[i][1] - b[j][1]
            dz := b[i][2] - b[j][2]
            e -= b[i][6] * b[j][6] / math.sqrt(dx * dx + dy * dy + dz * dz)
        }
    }
    return e
}
fn main() {
    n := size(1000)
    mut b := arr_bodies()
    for coordinate in 3 .. 6 {
        mut momentum := 0.0
        for body in b {
            momentum += body[coordinate] * body[6]
        }
        b[0][coordinate] = -momentum / solar_mass
    }
    println('${energy(b):.9f}')
    for _ in 0 .. n {
        for i in 0 .. b.len {
            for j in i + 1 .. b.len {
                dx := b[i][0] - b[j][0]
                dy := b[i][1] - b[j][1]
                dz := b[i][2] - b[j][2]
                squared := dx * dx + dy * dy + dz * dz
                magnitude := 0.01 / (squared * math.sqrt(squared))
                displacement := [dx, dy, dz]!
                for coordinate in 0 .. 3 {
                    b[i][coordinate + 3] -= displacement[coordinate] * b[j][6] * magnitude
                    b[j][coordinate + 3] += displacement[coordinate] * b[i][6] * magnitude
                }
            }
        }
        for i in 0 .. b.len {
            for coordinate in 0 .. 3 {
                b[i][coordinate] += 0.01 * b[i][coordinate + 3]
            }
        }
    }
    println('${energy(b):.9f}')
}
