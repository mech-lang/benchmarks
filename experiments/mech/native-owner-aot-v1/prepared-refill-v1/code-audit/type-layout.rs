#![allow(dead_code)]
mod probe {
    #[derive(Clone, Copy)]
    struct Price { compute: u64, comparison: u64 }
    #[derive(Debug)]
    enum Error { Overflow }
    const BATCH: u64 = 1024;
    fn add(a: u64, b: u64) -> Result<u64, Error> { a.checked_add(b).ok_or(Error::Overflow) }
    fn mul(a: u64, b: u64) -> Result<u64, Error> { a.checked_mul(b).ok_or(Error::Overflow) }
    #[path = "/private/tmp/mech-native-hashmap-performance/hosts/gpu/src/native_artifact/program_packed_fuel.rs"]
    mod actual_new_quote;
    struct FullRefill {
    threshold: Price,
    debit: Price,
    funded: u64,
}
struct RefillPlan {
    price: Price,
    funded: u64,
    full: Option<FullRefill>,
}
    pub fn sizes() -> [usize; 2] {
        [size_of::<actual_new_quote::Prepared>(), size_of::<RefillPlan>()]
    }
}
fn main() { let [new, old] = probe::sizes(); println!("{new} {old}"); }
