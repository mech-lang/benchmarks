//! Diagnostic reproduction of Mech's narrow payload/probing algorithm in Rust.
//! It deliberately has no Mech resource accounting or source-state machinery.
//! It is not linked into Mech or used as a benchmark implementation.
use num::{FromPrimitive, ToPrimitive};
use std::marker::PhantomData;

const GROUP: usize = 8;
const EMPTY: u8 = 0x80;
const FIRST: u64 = 0xbf58476d1ce4e5b9;
const SECOND: u64 = 0x94d049bb133111eb;

#[derive(Clone, Copy, Default)]
#[repr(C)]
struct Slot { key: u64, value: u64 }

pub struct Table<T> {
    slots: Vec<Slot>,
    controls: Vec<u8>,
    len: usize,
    key_type: PhantomData<T>,
}

impl<T> Default for Table<T> {
    fn default() -> Self {
        Self { slots: vec![Slot::default(); GROUP], controls: vec![EMPTY; 2 * GROUP - 1],
               len: 0, key_type: PhantomData }
    }
}

#[inline]
fn hash(key: u64) -> u64 {
    let product = u128::from(key ^ FIRST) * u128::from(SECOND);
    product as u64 ^ (product >> 64) as u64
}

#[inline]
fn group(controls: &[u8], index: usize, tag: u8) -> (u64, u64) {
    debug_assert!(index < controls.len() - GROUP + 1);
    #[cfg(target_arch = "aarch64")]
    let (raw, equal) = unsafe {
        // Every allocation includes the seven mirrored leading control bytes.
        // The index is masked below capacity and both loads read exactly eight.
        use std::arch::aarch64::*;
        let bytes = vld1_u8(controls.as_ptr().add(index));
        (vget_lane_u64(vreinterpret_u64_u8(bytes), 0),
         vget_lane_u64(vreinterpret_u64_u8(vceq_u8(bytes, vdup_n_u8(tag))), 0))
    };
    #[cfg(not(target_arch = "aarch64"))]
    let (raw, equal) = {
        let bytes = &controls[index..index + GROUP];
        let raw = u64::from_le_bytes(bytes.try_into().unwrap());
        let equal = bytes.iter().enumerate().fold(0, |mask, (lane, &byte)|
            mask | (u64::from(byte == tag) * 0xff << (lane * 8)));
        (raw, equal)
    };
    (equal & 0x0101010101010101, raw & 0x8080808080808080)
}

impl<T> Table<T> {
    #[inline]
    fn locate(&self, key: u64) -> Result<usize, usize> {
        let mixed = hash(key);
        let mask = self.slots.len() - 1;
        let mut index = mixed as usize & mask;
        let tag = (mixed >> 57) as u8;
        let mut inspected = 0;
        loop {
            let (mut matching, empty) = group(&self.controls, index, tag);
            while matching != 0 {
                let bucket = (index + (matching.trailing_zeros() as usize >> 3)) & mask;
                // Masking bounds the index below the positive private capacity.
                if unsafe { self.slots.get_unchecked(bucket).key } == key { return Ok(bucket); }
                matching &= matching - 1;
            }
            if empty != 0 {
                return Err((index + (empty.trailing_zeros() as usize >> 3)) & mask);
            }
            inspected += GROUP;
            assert!(inspected < self.slots.len(), "admitted table retains an empty slot");
            let step = if cfg!(quadratic_probe) { inspected } else { GROUP };
            index = (index + step) & mask;
        }
    }

    #[inline]
    fn set_control(&mut self, index: usize, byte: u8) {
        self.controls[index] = byte;
        if index < GROUP - 1 { self.controls[self.slots.len() + index] = byte; }
    }

    fn grow(&mut self) {
        let capacity = self.slots.len().checked_mul(2).unwrap();
        let slots = std::mem::replace(&mut self.slots, vec![Slot::default(); capacity]);
        let controls = std::mem::replace(&mut self.controls, vec![EMPTY; capacity + GROUP - 1]);
        for (old, slot) in slots.into_iter().enumerate() {
            if controls[old] == EMPTY { continue; }
            let index = self.locate(slot.key).unwrap_err();
            self.slots[index] = slot;
            self.set_control(index, (hash(slot.key) >> 57) as u8);
        }
    }

    pub fn values(&self) -> impl Iterator<Item = &u64> {
        self.slots.iter().enumerate().filter_map(|(index, slot)|
            (self.controls[index] != EMPTY).then_some(&slot.value))
    }
}

pub struct Entry<'a, T> {
    table: &'a mut Table<T>,
    key: u64,
    position: Result<usize, usize>,
}

impl<T: FromPrimitive + ToPrimitive + Copy> Table<T> {
    #[inline]
    pub fn entry(&mut self, key: T) -> Entry<'_, T> {
        let key = key.to_u64().unwrap();
        let position = self.locate(key);
        Entry { table: self, key, position }
    }

    pub fn get(&self, key: &T) -> Option<&u64> {
        self.locate(key.to_u64().unwrap()).ok().map(|index| &self.slots[index].value)
    }

    pub fn into_iter(self) -> impl Iterator<Item = (T, u64)> {
        self.slots.into_iter().zip(self.controls).filter_map(|(slot, control)|
            (control != EMPTY).then(|| (T::from_u64(slot.key).unwrap(), slot.value)))
    }
}

impl<'a, T> Entry<'a, T> {
    #[inline]
    pub fn or_insert(self, value: u64) -> &'a mut u64 {
        let index = match self.position {
            Ok(index) => index,
            Err(mut index) => {
                if self.table.len + 1 > self.table.slots.len() / 8 * 7 {
                    self.table.grow();
                    index = self.table.locate(self.key).unwrap_err();
                }
                self.table.slots[index] = Slot { key: self.key, value };
                self.table.set_control(index, (hash(self.key) >> 57) as u8);
                self.table.len += 1;
                index
            }
        };
        // Both locate outcomes are below capacity, and growth refreshes the
        // missing index before commit. No caller can construct an Entry.
        unsafe { &mut self.table.slots.get_unchecked_mut(index).value }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    #[test]
    fn complete_maps_preserve_growth_replacement_zero_and_maximum() {
        let mut table = Table::<u64>::default();
        let mut expected = BTreeMap::new();
        for round in 0..3 {
            for index in 0..4096u64 {
                let key = index.wrapping_mul(0x9e3779b97f4a7c15);
                let value = match round { 0 => index, 1 => 0, _ => u64::MAX - index };
                *table.entry(key).or_insert(123) = value;
                expected.insert(key, value);
            }
        }
        for (&key, value) in &expected { assert_eq!(table.get(&key), Some(value)); }
        assert!(table.get(&123456).is_none());
        assert_eq!(table.into_iter().collect::<BTreeMap<_, _>>(), expected);
    }

    #[test]
    fn colliding_fingerprints_wrap_and_retain_full_keys() {
        let keys = (0..1_000_000u64).filter(|&key| {
            let mixed = hash(key);
            mixed & 15 == 15 && mixed >> 57 == 7
        }).take(24).collect::<Vec<_>>();
        assert_eq!(keys.len(), 24);
        let mut table = Table::<u64>::default();
        for (index, &key) in keys.iter().enumerate() {
            assert_eq!(*table.entry(key).or_insert(index as u64), index as u64);
        }
        for (index, &key) in keys.iter().enumerate() { assert_eq!(table.get(&key), Some(&(index as u64))); }
        assert_eq!(table.into_iter().count(), 24);
    }

    #[test]
    fn exact_sixteen_byte_payload_and_eight_byte_groups() {
        assert_eq!(std::mem::size_of::<Slot>(), 16);
        let controls = [EMPTY, 3, 4, 3, EMPTY, 9, 3, 1, EMPTY, 3, 4, 3, EMPTY, 9, 3];
        assert_eq!(group(&controls, 0, 3), (0x0001000001000100, 0x0000008000000080));
        assert_eq!(group(&controls, 7, 3), (0x0100000100010000, 0x0000800000008000));
    }
}
