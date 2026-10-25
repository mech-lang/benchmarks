//! Diagnostic-only main-thread phase clocks. No guest algorithm or prices change.
use std::cell::RefCell;

#[cfg(not(target_os = "macos"))]
compile_error!("preparation clock diagnostic requires the verified macOS runner");

unsafe extern "C" { fn clock_gettime_nsec_np(clock_id: u32) -> u64; }
#[derive(Clone, Copy, Default)]
struct Stamp { cpu: u64, wall: u64 }
fn now() -> Stamp {
    // Verified on the runner: THREAD_CPUTIME=16, MONOTONIC=6. Read-only clocks.
    unsafe { Stamp { cpu: clock_gettime_nsec_np(16), wall: clock_gettime_nsec_np(6) } }
}
#[derive(Clone, Copy)]
pub enum Phase { BorrowRows, Scanner, SelectedJoin, JoinCopy, MapPrepare, MapKernel, MapFinish,
    SourceLoan, JoinedTransform, ChunkReceipt }
impl Phase {
    fn name(self) -> &'static str { match self {
        Self::BorrowRows => "borrow_rows", Self::Scanner => "source_scan",
        Self::SelectedJoin => "selected_join", Self::JoinCopy => "join_copy",
        Self::MapPrepare => "map_prepare", Self::MapKernel => "map_kernel",
        Self::MapFinish => "map_finish", Self::SourceLoan => "source_loan",
        Self::JoinedTransform => "joined_transform", Self::ChunkReceipt => "chunk_receipt",
    } }
}
const PHASES: [Phase; 10] = [Phase::BorrowRows, Phase::Scanner, Phase::SelectedJoin,
    Phase::JoinCopy, Phase::MapPrepare, Phase::MapKernel, Phase::MapFinish,
    Phase::SourceLoan, Phase::JoinedTransform, Phase::ChunkReceipt];
#[derive(Clone, Copy, Default)]
struct Total { calls: u64, cpu: u64, wall: u64, maximum_cpu: u64 }
#[derive(Clone, Copy, Default)]
struct Mark { name: Option<&'static str>, at: Stamp }
struct State {
    active: bool, start: Stamp, totals: [Total; 10], open: [Option<Stamp>; 10],
    marks: [Mark; 16], mark_count: usize,
    direct_windows: u64, direct_rows: u64, cell_windows: u64, cell_rows: u64,
}
impl Default for State {
    fn default() -> Self { Self { active: false, start: Stamp::default(), totals: [Total::default(); 10],
        open: [None; 10], marks: [Mark::default(); 16], mark_count: 0,
        direct_windows: 0, direct_rows: 0, cell_windows: 0, cell_rows: 0 } }
}
thread_local! { static STATE: RefCell<State> = RefCell::new(State::default()); }
fn active() -> bool { STATE.with(|state| state.borrow().active) }
fn record(phase: Phase, start: Stamp, end: Stamp) {
    STATE.with(|state| { let mut state = state.borrow_mut(); let total = &mut state.totals[phase as usize];
        let cpu = end.cpu.checked_sub(start.cpu).expect("monotone thread clock");
        total.calls += 1; total.cpu += cpu; total.wall += end.wall.checked_sub(start.wall).expect("monotone wall clock");
        total.maximum_cpu = total.maximum_cpu.max(cpu);
    });
}
pub struct Scope { phase: Phase, start: Option<Stamp> }
impl Scope {
    pub fn new(phase: Phase) -> Self { Self { phase, start: active().then(now) } }
}
impl Drop for Scope {
    fn drop(&mut self) { if let Some(start) = self.start { record(self.phase, start, now()); } }
}
pub fn begin(phase: Phase) {
    if active() { let stamp=now(); STATE.with(|s| { let mut s=s.borrow_mut();
        assert!(s.open[phase as usize].replace(stamp).is_none(), "non-overlapping phase"); }); }
}
pub fn end(phase: Phase) {
    if active() { let stamp=now(); let start=STATE.with(|s| s.borrow_mut().open[phase as usize].take()).expect("phase began");
        record(phase,start,stamp); }
}
pub fn mark(name: &'static str) {
    if active() { let at=now(); STATE.with(|s| { let mut s=s.borrow_mut(); let index=s.mark_count;
        assert!(index<s.marks.len(), "bounded diagnostic marks"); s.marks[index]=Mark { name: Some(name), at }; s.mark_count+=1; }); }
}
pub fn window(window: &mech_engine::native_artifact::NativeTextLineWindow<'_>) {
    if active() { STATE.with(|s| { let mut s=s.borrow_mut();
        if window.rows().is_none() { s.direct_windows+=1; s.direct_rows+=window.row_count() as u64; }
        else { s.cell_windows+=1; s.cell_rows+=window.row_count() as u64; }
    }); }
}
pub struct Root;
impl Root {
    pub fn new() -> Self { let start=now(); STATE.with(|s| { let mut s=s.borrow_mut(); assert!(!s.active);
        *s=State { active: true, start, ..State::default() }; }); mark("main_begin"); Self }
}
impl Drop for Root {
    fn drop(&mut self) {
        mark("main_complete");
        STATE.with(|s| { let mut s=s.borrow_mut(); s.active=false;
            assert!(s.open.iter().all(Option::is_none));
            for phase in PHASES { let t=s.totals[phase as usize];
                eprintln!("PPHASE_V2 {} {} {} {} {}",phase.name(),t.calls,t.cpu,t.wall,t.maximum_cpu); }
            for mark in &s.marks[..s.mark_count] {
                eprintln!("PMARK_V1 {} {} {}",mark.name.unwrap(),mark.at.cpu-s.start.cpu,mark.at.wall-s.start.wall); }
            eprintln!("PROWS_V1 {} {} {} {}",s.direct_windows,s.direct_rows,s.cell_windows,s.cell_rows);
        });
    }
}
