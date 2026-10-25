//! Diagnostic branch only: read this thread's counters at owned boundaries.
//! No counter configuration, priority/affinity change, or worker-time logging.
//! Shared verbatim with the separately instrumented upstream Rust copy.
use std::cell::RefCell;
use std::io::Write;
use std::sync::OnceLock;

#[repr(C)]
#[derive(Clone, Copy, Default)]
struct Raw {
    instructions: u64,
    cycles: u64,
    user_mach: u64,
    system_mach: u64,
}
unsafe extern "C" {
    fn thread_selfcounts(kind: u32, destination: *mut std::ffi::c_void, size: usize) -> i32;
    fn clock_gettime_nsec_np(clock: i32) -> u64;
    fn pthread_threadid_np(thread: *mut std::ffi::c_void, id: *mut u64) -> i32;
}
const _: () = assert!(std::mem::size_of::<Raw>() == 32);

#[derive(Clone, Copy, Default)]
struct Stamp {
    wall_ns: u64,
    cpu_ns: u64,
    levels: [Raw; 2],
}
impl Stamp {
    fn read() -> Self {
        let mut value = Self::default();
        // The counter pilot verifies two levels (Performance, Efficiency) on
        // this runner. THSC_TIME_CPI_PER_PERF_LEVEL is read-only kind 4.
        unsafe {
            value.wall_ns = clock_gettime_nsec_np(6);
            value.cpu_ns = clock_gettime_nsec_np(16);
            assert_eq!(thread_selfcounts(4, value.levels.as_mut_ptr().cast(),
                std::mem::size_of_val(&value.levels)), 0);
        }
        value
    }
}
#[derive(Clone, Copy, Default)]
struct Mark {
    label: &'static str,
    stamp: Stamp,
}
struct Trace {
    slot: usize,
    region: u64,
    index: u64,
    width: u64,
    thread_id: u64,
    marks: [Mark; 16],
    used: usize,
}
thread_local! {
    static CURRENT: RefCell<Option<Trace>> = const { RefCell::new(None) };
}
static FINISHED: [OnceLock<Trace>; 32] = [const { OnceLock::new() }; 32];

pub fn begin(slot: usize, region: u64, index: u64) {
    assert!(slot < FINISHED.len());
    let stamp = Stamp::read();
    let mut thread_id = 0;
    assert_eq!(unsafe { pthread_threadid_np(std::ptr::null_mut(), &mut thread_id) }, 0);
    let mut marks = [Mark::default(); 16];
    marks[0] = Mark { label: if slot == 31 { "main_begin" } else { "worker_begin" }, stamp };
    CURRENT.with(|current| {
        let mut current = current.borrow_mut();
        assert!(current.is_none());
        *current = Some(Trace { slot, region, index, width: 0, thread_id, marks, used: 1 });
    });
}
pub fn width(width: u64) {
    CURRENT.with(|current| {
        if let Some(trace) = &mut *current.borrow_mut() {
            assert!(trace.width == 0 || trace.width == width);
            trace.width = width;
        }
    });
}
pub fn mark(label: &'static str) {
    CURRENT.with(|current| {
        if let Some(trace) = &mut *current.borrow_mut() {
            assert!(trace.used < trace.marks.len());
            trace.marks[trace.used] = Mark { label, stamp: Stamp::read() };
            trace.used += 1;
        }
    });
}
pub fn finish() {
    mark("body_complete");
    CURRENT.with(|current| {
        let trace = current.borrow_mut().take().expect("diagnostic trace missing");
        assert!(FINISHED[trace.slot].set(trace).is_ok());
    });
}

pub struct Root;
impl Root {
    pub fn new() -> Self {
        begin(31, u64::MAX, u64::MAX);
        Self
    }
}
impl Drop for Root {
    fn drop(&mut self) {
        finish();
        // Emit only after every source task has completed and the caller has
        // joined/consumed its results. Fixed diagnostic storage is outside the
        // guest graph; these builds are not primary benchmark executables.
        let mut output = std::io::stderr().lock();
        for slot in &FINISHED {
            if let Some(trace) = slot.get() {
                for mark in &trace.marks[..trace.used] {
                    let stamp = mark.stamp;
                    let p = stamp.levels[0];
                    let e = stamp.levels[1];
                    writeln!(output, "WCPU_TRACE_V1 {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}",
                        trace.slot, trace.region, trace.index, trace.width, trace.thread_id,
                        mark.label, stamp.wall_ns, stamp.cpu_ns,
                        p.instructions, p.cycles, p.user_mach, p.system_mach,
                        e.instructions, e.cycles, e.user_mach, e.system_mach).unwrap();
                }
            }
        }
    }
}
