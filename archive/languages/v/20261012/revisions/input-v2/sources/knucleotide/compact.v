module main
import os
import io

const lengths = [1,2,3,4,6,12,18]
const queries = ['GGT','GGTA','GGTATT','GGTATTTTAATT','GGTATTTTAATTTATAGT']
struct Entry {
    word string
    count u64
}
fn third_record() []u8 {
    input_bytes := io.read_all(reader: os.stdin(), read_to_end_of_stream: true) or { panic(err) }
    input := input_bytes.bytestr()
    mut selected := false
    mut sequence := []u8{}
    for line in input.split_into_lines() {
        if line.starts_with(';') {
            continue
        } else if line.starts_with('>') {
            if selected {
                break
            }
            selected = line.starts_with('>THREE ') || line.starts_with('>THREE\t') || line == '>THREE'
        } else if selected {
            sequence << line.to_upper().bytes()
        }
    }
    return sequence
}
fn compare_entries(a &Entry, b &Entry) int {
    if a.count == b.count {
        return if a.word < b.word { -1 } else if a.word > b.word { 1 } else { 0 }
    }
    return if a.count > b.count { -1 } else { 1 }
}
fn frequencies(mut rows []Entry, denominator int) {
    rows.sort_with_compare(compare_entries)
    for row in rows {
        println('${row.word} ${100.0 * f64(row.count) / f64(denominator):.3f}')
    }
    println('')
}

fn counts(sequence string, k int) map[string]u64 {
    mut result := map[string]u64{}
    if sequence.len >= k {
        for i in 0 .. sequence.len - k + 1 {
            word := sequence[i .. i + k]
            result[word] = result[word] + 1
        }
    }
    return result
}
fn main() {
    sequence := third_record().bytestr()
    mut tables := []map[string]u64{}
    for k in lengths {
        tables << counts(sequence, k)
    }
    for index in 0 .. 2 {
        mut rows := []Entry{}
        for word, count in tables[index] {
            rows << Entry{word: word, count: count}
        }
        frequencies(mut rows, sequence.len - lengths[index] + 1)
    }
    for index, word in queries {
        println('${tables[index + 2][word]}\t${word}')
    }
}
