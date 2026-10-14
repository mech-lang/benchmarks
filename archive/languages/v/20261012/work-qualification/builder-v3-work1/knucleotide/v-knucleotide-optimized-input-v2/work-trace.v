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

struct CountResult {
    k int
    counts map[u64]u64
}
fn code(b u8) u64 {
    return match b {
        `A` { u64(0) }
        `C` { u64(1) }
        `G` { u64(2) }
        `T` { u64(3) }
        else {
            panic('Invalid nucleotide')
        }
    }
}
@[direct_array_access]
fn packed(sequence []u8, k int) CountResult {
    mask := (u64(1) << (2 * k)) - 1
    mut key := u64(0)
    mut result := map[u64]u64{}
    for i, b in sequence {
        key = ((key << 2) | code(b)) & mask
        if i + 1 >= k {
            result[key] = result[key] + 1
        }
    }
    return CountResult{k: k, counts: result}
}
fn decode(key u64, k int) string {
    symbols := 'ACGT'.bytes()
    mut remaining := key
    mut word := []u8{len: k}
    for i := k - 1; i >= 0; i-- {
        word[i] = symbols[int(remaining & 3)]
        remaining >>= 2
    }
    return word.bytestr()
}
fn main() {
    sequence := third_record()
    mut jobs := []thread CountResult{}
    for k in lengths {
        jobs << spawn packed(sequence, k)
    }
    mut tables := []CountResult{}
    for job in jobs {
        tables << job.wait()
    }
    audit_trace_maps(tables, sequence.len)
    for index in 0 .. 2 {
        mut rows := []Entry{}
        for key, count in tables[index].counts {
            rows << Entry{word: decode(key, lengths[index]), count: count}
        }
        frequencies(mut rows, sequence.len - lengths[index] + 1)
    }
    for index, word in queries {
        mut key := u64(0)
        for b in word.bytes() {
            key = (key << 2) | code(b)
        }
        println('${tables[index + 2].counts[key]}\t${word}')
    }
}

// Unscored audit copy only; maps are dumped by the parent after every join.
fn audit_trace_maps(tables []CountResult, sequence_length int) {
    path := os.getenv('MECH_V_WORK_TRACE')
    if path.len == 0 {
        panic('An isolated work trace path is required')
    }
    mut audit := os.create(path) or { panic(err) }
    defer {
        audit.close()
    }
    audit.writeln('TRACE_V1|knucleotide|optimized|${tables.len}|${sequence_length}') or { panic(err) }
    for table in tables {
        mut total := u64(0)
        for key, value in table.counts {
            audit.writeln('MAP|${table.k}|${key}|${value}') or { panic(err) }
            total += value
        }
        audit.writeln('TABLE|${table.k}|${table.counts.len}|${total}') or { panic(err) }
    }
    audit.writeln('END_V1') or { panic(err) }
}
