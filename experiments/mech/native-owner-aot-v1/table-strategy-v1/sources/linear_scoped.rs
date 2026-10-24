// The Computer Language Benchmarks Game
// https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
//
// contributed by Alexander

extern crate futures;
extern crate tokio_threadpool;
extern crate itertools;
extern crate num;
extern crate hashbrown;

use futures::{Future, lazy};
use self::tokio_threadpool::ThreadPool;
use itertools::Itertools;
use num::{FromPrimitive, ToPrimitive};
use std::cmp::Ordering;
use std::sync::Arc;

mod diagnostic_packed_table;
type Map<T> = diagnostic_packed_table::Table<T>;

trait ShlXorMsk<T> {
    fn sh(a: T, x: u8, m: T) -> T;
    fn mask(len: usize) -> T;
}

impl ShlXorMsk<u8> for u8 {
    fn sh(a: u8, x: u8, m: u8) -> u8 {
        m & (a << 2) | x
    }
    fn mask(len: usize) -> u8 {
        ((1u16 << 2 * len) - 1) as u8
    }
}

impl ShlXorMsk<u16> for u16 {
    fn sh(a: u16, x: u8, m: u16) -> u16 {
        m & (a << 2) | (x as u16)
    }
    fn mask(len: usize) -> u16 {
        ((1u32 << 2 * len) - 1) as u16
    }
}

impl ShlXorMsk<u32> for u32 {
    fn sh(a: u32, x: u8, m: u32) -> u32 {
        m & (a << 2) | (x as u32)
    }
    fn mask(len: usize) -> u32 {
        ((1u64 << 2 * len) - 1) as u32
    }
}

impl ShlXorMsk<u64> for u64 {
    fn sh(a: u64, x: u8, m: u64) -> u64 {
        m & (a << 2) | (x as u64)
    }
    fn mask(len: usize) -> u64 {
        (1u64 << 2 * len) - 1
    }
}

fn match_key(k: u8) -> char {
    match k {
        0b00 => 'A',
        0b01 => 'C',
        0b10 => 'T',
        0b11 => 'G',
        _ => '_',
    }
}

fn print_stat(h: Map<u64>, seq_len: usize) {
    let total = h.values().sum::<u64>();

    h.into_iter()
        .sorted_by(|&(ref a, x), &(ref b, y)| {
            let ord1 = Ord::cmp(&y, &x);
            if ord1 == Ordering::Equal {
                Ord::cmp(&b, &a)
            } else {
                ord1
            }
        })
        .for_each(|(k, v)| {
            if seq_len == 1 {
                println!("{} {:.3}", match_key(k as u8), (100 * v) as f32 / total as f32);
            } else {
                println!(
                    "{}{} {:.3}",
                    match_key((k >> 2) as u8),
                    match_key((0b11 & k) as u8),
                    (100 * v) as f32 / total as f32
                );
            };
        });
    println!();
}

fn print<
    T: FromPrimitive + ToPrimitive + Default + std::hash::Hash + std::cmp::Eq + ShlXorMsk<T> + Copy,
>(
    h: Map<T>,
    seq: &str,
) {
    let mask = T::from_u64((1u64 << (2 * seq.len() as u32)) - 1).unwrap();
    let k = seq.to_ascii_lowercase()
        .as_bytes()
        .iter()
        .map(|x| 0b11u8 & x >> 1)
        .fold(T::default(), |acc, x| T::sh(acc, x, mask));
    println!("{}\t{}", h.get(&k).unwrap_or(&0), seq);
}

fn freq<
    T: FromPrimitive + ToPrimitive + Default + std::hash::Hash + std::cmp::Eq + ShlXorMsk<T> + Copy,
>(
    s_vec: &[u8],
    len: usize,
) -> Map<T> {
    let mut h = Map::default();
    let mask = T::mask(len);
    let mut it = s_vec.iter();
    let mut a = it.by_ref()
        .take(len - 1)
        .fold(T::default(), |acc, &x| T::sh(acc, 0b11 & x >> 1, mask));
    for &x in it {
        a = T::sh(a, 0b11 & x >> 1, mask);
        *h.entry(a).or_insert(0) += 1;
    }
    h
}

fn get_seq<R: std::io::BufRead>(mut r: R, key: &[u8]) -> Vec<u8> {
    let mut res = Vec::with_capacity(65536);
    let mut line = Vec::with_capacity(64);

    loop {
        match r.read_until(b'\n', &mut line) {
            Ok(b) if b > 0 => if line.starts_with(key) { break },
            _ => break,
        }
        line.clear();
    }

    loop {
        line.clear();
        match r.read_until(b'\n', &mut line) {
            Ok(b) if b > 0 => res.extend(line[..line.len()-1].iter().copied()),
            _ => break,
        }
    }

    res
}

pub fn calc<R: std::io::BufRead>(r: R) {
    let s_vec = get_seq(r, b">THREE");


    let arc_vec = Arc::new(s_vec);
    let s1 = arc_vec.clone();
    let s2 = arc_vec.clone();
    let s3 = arc_vec.clone();
    let s4 = arc_vec.clone();
    let s5 = arc_vec.clone();
    let s6 = arc_vec.clone();
    let s7 = arc_vec.clone();
    std::thread::scope(|scope| {
    let f1 = scope.spawn(move || freq(&s7, 1));
    let f2 = scope.spawn(move || freq(&s6, 2));
    let f3 = scope.spawn(move || freq(&s5, 3));
    let f4 = scope.spawn(move || freq(&s4, 4));
    let f5 = scope.spawn(move || freq(&s3, 6));
    let f6 = scope.spawn(move || freq(&s2, 12));
    let f7 = scope.spawn(move || freq(&s1, 18));
    print_stat(f1.join().unwrap(), 1);
    print_stat(f2.join().unwrap(), 2);
    print::<u64>(f3.join().unwrap(), "GGT");
    print::<u64>(f4.join().unwrap(), "GGTA");
    print::<u64>(f5.join().unwrap(), "GGTATT");
    print::<u64>(f6.join().unwrap(), "GGTATTTTAATT");
    print::<u64>(f7.join().unwrap(), "GGTATTTTAATTTATAGT");
    });
}

fn main() {
    let stdin = std::io::stdin();
    calc(stdin.lock());
}
