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
const alu = 'GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA'.bytes()

fn cumulative(probabilities []f64) []f64 {
    mut result := []f64{cap: probabilities.len}
    mut sum := 0.0
    for probability in probabilities {
        sum += probability
        result << sum
    }
    return result
}

fn repeat_sequence(n int) {
    mut data := []u8{cap: n + n / 60 + 1}
    for i in 0 .. n {
        data << alu[i % alu.len]
        if (i + 1) % 60 == 0 || i + 1 == n {
            data << `\n`
        }
    }
    emit(data)
}
fn random_sequence(n int, symbols []u8, cdf []f64, seed int) int {
    mut state := seed
    mut data := []u8{cap: n + n / 60 + 1}
    for i in 0 .. n {
        state = (state * 3877 + 29573) % 139968
        random := f64(state) / 139968.0
        mut index := 0
        for cdf[index] <= random {
            index++
        }
        data << symbols[index]
        if (i + 1) % 60 == 0 || i + 1 == n {
            data << `\n`
        }
    }
    emit(data)
    return state
}

fn main() {
    n := size(1000)
    iub_symbols := 'acgtBDHKMNRSVWY'.bytes()
    iub_cdf := cumulative([0.27,0.12,0.12,0.27,0.02,0.02,0.02,0.02,0.02,0.02,0.02,0.02,0.02,0.02,0.02])
    human_symbols := 'acgt'.bytes()
    human_cdf := cumulative([0.3029549426680,0.1979883004921,0.1975473066391,0.3015094502008])
    println('>ONE Homo sapiens alu')
    repeat_sequence(2 * n)
    println('>TWO IUB ambiguity codes')
    seed := random_sequence(3 * n, iub_symbols, iub_cdf, 42)
    println('>THREE Homo sapiens frequency')
    _ = random_sequence(5 * n, human_symbols, human_cdf, seed)
}
