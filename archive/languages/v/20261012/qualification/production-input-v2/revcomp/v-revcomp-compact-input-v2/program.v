module main
import os
import io
fn emit(data []u8) {
    mut output := os.stdout()
    output.write_string(data.bytestr()) or { panic(err) }
    output.flush()
}

fn complement(b u8) u8 {
    symbols := 'ACGTUMRWSYKVHDBN'.bytes()
    values := 'TGCAAKYWSRMBDHVN'.bytes()
    index := symbols.index(b & 0xdf)
    if index < 0 {
        panic('Invalid IUPAC base')
    }
    return values[index]
}

fn record(header string, sequence []u8) {
    if header.len == 0 {
        return
    }
    println(header)
    mut line := []u8{cap: 61}
    for i := sequence.len - 1; i >= 0; i-- {
        line << complement(sequence[i])
        if line.len == 60 || i == 0 {
            line << `\n`
            emit(line)
            line.clear()
        }
    }
}
fn main() {
    input_bytes := io.read_all(reader: os.stdin(), read_to_end_of_stream: true) or { panic(err) }
    data := input_bytes.bytestr()
    mut header := ''
    mut sequence := []u8{}
    for line in data.split_into_lines() {
        if line.starts_with(';') {
            continue
        } else if line.starts_with('>') {
            record(header, sequence)
            header = line
            sequence.clear()
        } else {
            sequence << line.bytes()
        }
    }
    record(header, sequence)
}
