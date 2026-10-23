// Diagnostic retained separately: this exceeds the default resident work policy.
#![cfg(all(feature = "full_compiler", not(feature = "no_std")))]
use mech_core::ValueData;
mod support;
use support::evaluate_with_source_catalog as evaluate;

const COUNT: &str = r#"
+> map
increment(h<{string:u64}>, key<string>) => (out<{string:u64}>) :=
  keys := {k | k <- h_keys}
  previous := (key ∈ keys)? | true => h{key} | false => 0u64.
  out := map/insert(h, key, previous + 1u64).
#Count(s<string>, width<u64>, n<u64>, initial<{string:u64}>) => <{string:u64}>
  | :Next(index<u64>, counts<{string:u64}>)
  | :Done(counts<{string:u64}>).
#Count(s, width, n, initial) -> :Next(0u64, initial)
  :Next(index, counts)
    | width == 0u64 -> :Done(counts)
    | index >= n -> :Done(counts)
    | width > n - index -> :Done(counts)
    | * -> :Next(index + 1u64, increment(counts, s[(index + 1u64)..=(index + width)]))
  :Done(counts) => counts.
empty<{string:u64}> := map/new()
"#;

#[test]
fn source_state_machine_counts_all_keys_at_every_nucleotide_width() {
    let text = "ACGTACGTNACGTTACGTACGTACGT";
    for width in [1, 2, 3, 4, 6, 12, 18] {
        let source = format!(
            "{COUNT}\n#Count(\"{text}\", {width}u64, {}u64, empty)\n",
            text.len()
        );
        let output = evaluate(&source).unwrap_or_else(|error| panic!("{source}: {error:?}"));
        let ValueData::Map(actual) = output.data() else {
            panic!("expected map")
        };
        let mut expected = std::collections::BTreeMap::<String, u64>::new();
        for key in text.as_bytes().windows(width) {
            *expected
                .entry(std::str::from_utf8(key).unwrap().to_owned())
                .or_default() += 1;
        }
        assert_eq!(actual.entries().len(), expected.len(), "width {width}");
        let mut total = 0;
        for (entry, (key, count)) in actual.entries().iter().zip(expected) {
            assert!(
                matches!(entry.key().data(), ValueData::String(actual) if actual.as_ref() == key)
            );
            assert!(matches!(entry.value(), ValueData::U64(actual) if *actual == count));
            total += count;
        }
        assert_eq!(total, (text.len() - width + 1) as u64);
    }
}
