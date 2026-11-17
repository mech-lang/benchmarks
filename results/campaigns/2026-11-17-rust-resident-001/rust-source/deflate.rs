//! Maximum-level zlib-rs task control; fresh owned output and compressor per call.
use std::hint::black_box;
use std::sync::Arc;
use std::time::Instant;
fn compress(input:&[u8], prefix:&[u8])->Vec<u8> {
    let mut output=vec![0;prefix.len()+zlib_rs::compress_bound(input.len()).max(64)];
    output[..prefix.len()].copy_from_slice(prefix);
    let config=zlib_rs::DeflateConfig{level:9,window_bits:-15,..Default::default()};
    let (written,status)=zlib_rs::compress_slice(&mut output[prefix.len()..],input,config);
    assert_eq!(status,zlib_rs::ReturnCode::Ok);let n=written.len();output.truncate(prefix.len()+n);output
}
fn main() {
    let a:Vec<_>=std::env::args().collect();assert_eq!(a.len(),5);
    let input=Arc::new(std::fs::read(&a[1]).unwrap());let prefix=Arc::new(std::fs::read(&a[2]).unwrap());
    let held_input=input.clone();let held_prefix=prefix.clone();
    let warm:usize=a[3].parse().unwrap();let mut previous=None;
    for _ in 0..warm {previous=Some(compress(black_box(&input),black_box(&prefix)));}
    let start=Instant::now();let output=compress(black_box(&input),black_box(&prefix));
    let seconds=start.elapsed().as_secs_f64();black_box(&output);
    assert_eq!(input,held_input);assert_eq!(prefix,held_prefix);
    if let Some(prior)=previous {assert_eq!(prior,output);}
    assert!(output.as_ptr()!=input.as_ptr() && output.as_ptr()!=prefix.as_ptr());
    std::fs::write(&a[4],&output).unwrap();
    println!("{}",serde_json::json!({"protocol":1,"outcome":"ok","metrics":{"native_program_call_seconds":seconds,"input_bytes":input.len(),"output_bytes":output.len()},"aliases_preserved":true,"separately_owned_output":true}));
}
