//! Diagnostic cost control, not a Mech implementation or benchmark submission.
//! Serial String/U64 storage uses Mech's pinned hashbrown representation and
//! separate native storage calls. Every source window updates its width's map.
use hashbrown::HashMap;
use std::io::{self, Read, Write};

type Map = HashMap<Box<str>, u64>;

#[inline(never)]
fn lookup(map: &Map, key: &str) -> Option<u64> {
    map.get(key).copied()
}

#[inline(never)]
fn insert(map: &mut Map, key: &str, value: u64) {
    // The retained binding checks freshness before storage insertion. Keep
    // that separate lookup even though a normal native implementation could
    // use one entry operation instead of this source/API sequence.
    let fresh = lookup(map, key).is_none();
    if let Some(current) = map.get_mut(key) {
        assert!(!fresh);
        *current = value;
    } else {
        assert!(fresh);
        if map.len() == map.capacity() {
            let target = map.capacity().checked_mul(2).unwrap().max(4);
            map.try_reserve(target - map.len()).unwrap();
        }
        map.insert(key.into(), value);
    }
}

fn count(text: &str, width: usize) -> (Map, u64) {
    let mut map = Map::default();
    let mut updates = 0;
    for key in text.as_bytes().windows(width) {
        let key = std::str::from_utf8(key).unwrap();
        let previous = if lookup(&map, key).is_some() { lookup(&map, key).unwrap() } else { 0 };
        insert(&mut map, key, previous + 1);
        updates += 1;
    }
    assert_eq!(map.values().sum::<u64>(), updates);
    (map, updates)
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut text = String::new();
    let mut found = false;
    for line in input.lines() {
        if !found {
            if line == ">THREE" || line.starts_with(">THREE ") || line.starts_with(">THREE\t") {
                found = true;
            }
        } else if line.starts_with('>') {
            break;
        } else {
            text.push_str(line);
        }
    }
    text.make_ascii_uppercase();
    assert!(found && text.bytes().all(|b| matches!(b, b'A' | b'C' | b'G' | b'T')));
    let mut output = String::new();
    let mut updates = 0;
    for width in [1, 2] {
        let (map, count) = count(&text, width);
        updates += count;
        let mut pairs: Vec<_> = map.iter().collect();
        pairs.sort_unstable_by(|a, b| b.1.cmp(a.1).then_with(|| a.0.cmp(b.0)));
        for (key, value) in pairs {
            output.push_str(&format!("{} {:.3}\n", key, 100.0 * *value as f64 / count as f64));
        }
        output.push('\n');
    }
    for query in ["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"] {
        let (map, count) = count(&text, query.len());
        updates += count;
        output.push_str(&format!("{}\t{}\n", lookup(&map, query).unwrap_or(0), query));
    }
    io::stdout().write_all(output.as_bytes()).unwrap();
    eprintln!("{{\"tables\":7,\"updates\":{updates},\"bases\":{}}}", text.len());
}
