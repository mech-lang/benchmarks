module main
import os
fn emit(data []u8) {
    mut output := os.stdout()
    output.write_string(data.bytestr()) or { panic(err) }
    output.flush()
}

fn record(header []u8, mut sequence []u8, table [256]u8) {
    if header.len == 0 {
        return
    }
    emit(header)
    mut left := 0
    mut right := sequence.len - 1
    for left <= right {
        a := table[sequence[left]]
        b := table[sequence[right]]
        if a == 0 || b == 0 {
            panic('Invalid IUPAC base')
        }
        sequence[left] = b
        sequence[right] = a
        left++
        right--
    }
    mut output := []u8{cap: sequence.len + sequence.len / 60 + 1}
    for start := 0; start < sequence.len; start += 60 {
        end := if start + 60 < sequence.len { start + 60 } else { sequence.len }
        output << sequence[start .. end]
        output << `\n`
    }
    emit(output)
}
fn main() {
    symbols := 'ACGTUMRWSYKVHDBN'.bytes()
    values := 'TGCAAKYWSRMBDHVN'.bytes()
    mut table := [256]u8{}
    for i, symbol in symbols {
        table[symbol] = values[i]
        table[symbol + 32] = values[i]
    }
    data := os.get_raw_stdin()
    mut header := []u8{}
    mut sequence := []u8{}
    mut at_line_start := true
    mut position := 0
    for position < data.len {
        b := data[position]
        if at_line_start && b == `;` {
            for position < data.len && data[position] != `\n` {
                position++
            }
            if position < data.len {
                position++
            }
            at_line_start = true
            continue
        } else if at_line_start && b == `>` {
            record(header, mut sequence, table)
            sequence.clear()
            header.clear()
            for position < data.len && data[position] != `\n` {
                if data[position] != `\r` {
                    header << data[position]
                }
                position++
            }
            header << `\n`
            if position < data.len {
                position++
            }
            at_line_start = true
            continue
        } else if b != `\n` && b != `\r` {
            sequence << b
        }
        at_line_start = b == `\n`
        position++
    }
    record(header, mut sequence, table)
}
