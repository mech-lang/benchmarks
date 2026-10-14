module main

import os
import strconv
fn size(default_value int) int {
    if os.args.len > 1 {
        return strconv.atoi(os.args[1]) or { default_value }
    }
    return default_value
}

struct FannResult {
    checksum i64
    maximum int
}
@[direct_array_access]
fn chunk(n int, first i64, last i64, factorial []i64) FannResult {
    mut permutation := [32]int{}
    mut scratch := [32]int{}
    mut digits := [32]int{}
    for i in 0 .. n {
        permutation[i] = i
    }
    mut remaining := first
    for width := n; width > 1; width-- {
        digit := int(remaining / factorial[width - 1])
        remaining %= factorial[width - 1]
        digits[width - 1] = digit
        for _ in 0 .. digit {
            head := permutation[0]
            for i in 0 .. width - 1 {
                permutation[i] = permutation[i + 1]
            }
            permutation[width - 1] = head
        }
    }
    mut checksum := i64(0)
    mut maximum := 0
    for rank := first; rank < last; rank++ {
        for i in 0 .. n {
            scratch[i] = permutation[i]
        }
        mut flips := 0
        for scratch[0] != 0 {
            last_index := scratch[0]
            for i in 0 .. (last_index + 1) / 2 {
                saved := scratch[i]
                scratch[i] = scratch[last_index - i]
                scratch[last_index - i] = saved
            }
            flips++
        }
        if flips > maximum {
            maximum = flips
        }
        checksum += if rank % 2 == 0 { i64(flips) } else { -i64(flips) }
        if rank + 1 < last {
            for width in 2 .. n + 1 {
                head := permutation[0]
                for i in 0 .. width - 1 {
                    permutation[i] = permutation[i + 1]
                }
                permutation[width - 1] = head
                digits[width - 1]++
                if digits[width - 1] < width {
                    break
                }
                digits[width - 1] = 0
            }
        }
    }
    return FannResult{checksum: checksum, maximum: maximum}
}
fn main() {
    n := size(10)
    if n < 2 {
        println('0\nPfannkuchen(${n}) = 0')
        return
    }
    if n > 20 {
        panic('factorial rank must fit i64')
    }
    mut factorial := []i64{len: n + 1, init: 1}
    for i in 1 .. n + 1 {
        factorial[i] = factorial[i - 1] * i64(i)
    }
    total := factorial[n]
    mut jobs := []thread FannResult{}
    for worker in 0 .. 8 {
        first := total / 8 * i64(worker) + total % 8 * i64(worker) / 8
        last := total / 8 * i64(worker + 1) + total % 8 * i64(worker + 1) / 8
        jobs << spawn chunk(n, first, last, factorial)
    }
    mut checksum := i64(0)
    mut maximum := 0
    for job in jobs {
        result := job.wait()
        checksum += result.checksum
        if result.maximum > maximum {
            maximum = result.maximum
        }
    }
    println('${checksum}\nPfannkuchen(${n}) = ${maximum}')
}
