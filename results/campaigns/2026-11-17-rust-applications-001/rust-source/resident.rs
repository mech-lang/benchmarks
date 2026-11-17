//! Independent task controls. No Mech compiler, runtime, or oracle is linked.
use serde_json::{json, Value};
use std::alloc::{GlobalAlloc, Layout, System};
use std::hint::black_box;
use std::io::{self, Read};
use std::sync::{atomic::{AtomicU64, Ordering::Relaxed}, Arc, Weak};
use std::time::Instant;
use unicode_segmentation::UnicodeSegmentation;

struct Counting;
static ALLOCS: AtomicU64 = AtomicU64::new(0);
static BYTES: AtomicU64 = AtomicU64::new(0);
unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed); BYTES.fetch_add(l.size() as u64, Relaxed);
        System.alloc(l)
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) { System.dealloc(p, l) }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed); BYTES.fetch_add(n as u64, Relaxed);
        System.realloc(p, l, n)
    }
}
#[global_allocator] static ALLOCATOR: Counting = Counting;

#[derive(Clone, PartialEq)]
enum Input { Numbers(Vec<f64>), Text(String) }
impl Input {
    fn numbers(&self) -> &[f64] { match self { Self::Numbers(v) => v, _ => panic!("numeric frame required") } }
    fn text(&self) -> &str { match self { Self::Text(s) => s, _ => panic!("string frame required") } }
}
#[derive(Clone)]
enum Output {
    Unpublished, Number(f64), Bool(bool),
    Matrix([usize; 2], Arc<Vec<f64>>), Set(Arc<Vec<f64>>),
    Table(bool, Arc<Vec<Vec<Option<f64>>>>),
}
impl Output {
    fn json(&self) -> Value {
        match self {
            Self::Unpublished => json!({"kind":"unpublished"}),
            Self::Number(v) => json!({"kind":"scalar","value":v}),
            Self::Bool(v) => json!({"kind":"scalar","value":v}),
            Self::Matrix(shape,v) => json!({"kind":"matrix","shape":shape,"values":**v}),
            Self::Set(v) => json!({"kind":"set","values":**v}),
            Self::Table(two,v) => json!({"kind":"table","columns":if *two {vec!["key","left"]} else {vec!["key","left","right"]},"rows":**v}),
        }
    }
}

#[derive(Clone, Copy, PartialEq)]
enum Task { Scalar, Pipeline, Matrix, Map, Branch, Recursion, Record, State, Oscillator, Wide, Chain, Filter, Collection, Strings, Graphemes, Fsm, Graph, Join(u8), Ekf }
impl Task {
    fn parse(s: &str) -> Self {
        match s {
            "scalar"=>Self::Scalar,"pipeline"=>Self::Pipeline,"matrix"=>Self::Matrix,
            "map"=>Self::Map,"branch"=>Self::Branch,"recursion"=>Self::Recursion,
            "record"=>Self::Record,"state"=>Self::State,"oscillator"=>Self::Oscillator,
            "wide"=>Self::Wide,"chain"=>Self::Chain,"filter"=>Self::Filter,
            "collection"=>Self::Collection,"strings"=>Self::Strings,"graphemes"=>Self::Graphemes,
            "fsm"=>Self::Fsm,"graph"=>Self::Graph,"ekf"=>Self::Ekf,
            "table-join"=>Self::Join(0),"table-left-outer-join"=>Self::Join(1),
            "table-right-outer-join"=>Self::Join(2),"table-full-outer-join"=>Self::Join(3),
            "table-left-semi-join"=>Self::Join(4),"table-left-anti-join"=>Self::Join(5),
            _=>panic!("unimplemented Rust task {s}"),
        }
    }
    fn stateful(self) -> bool { matches!(self,Self::State|Self::Oscillator|Self::Fsm|Self::Ekf) }
    fn validate(self, input: &Input) -> bool {
        match input {
            Input::Text(_)=>matches!(self,Self::Strings|Self::Graphemes|Self::Fsm),
            Input::Numbers(v)=>v.iter().all(|x|x.is_finite()) && match self {
                Self::Strings|Self::Graphemes|Self::Fsm=>false,
                Self::Filter=>true, Self::State|Self::Oscillator=>v.is_empty(),
                Self::Ekf=>v.len()==4, _=>v.len()==1,
            }
        }
    }
}

struct Instance {
    task: Task, previous: Option<Input>, published: Output, turns: usize,
    position: f64, velocity: f64, captured: Option<String>, ekf: Ekf,
}
impl Instance {
    fn new(task: Task) -> Self { Self {task,previous:None,published:Output::Unpublished,turns:0,position:1.,velocity:0.,captured:None,ekf:Ekf::new()} }
    fn prepare<'a>(&self, input: &'a Input) -> Result<&'a Input, ()> { if self.task.validate(input) { Ok(input) } else { Err(()) } }
    fn turn(&mut self, input: &Input) {
        let input = self.prepare(input).expect("rejected valid frame");
        self.turns += 1;
        if !self.task.stateful() && self.previous.as_ref()==Some(input) { return; }
        let x = match input {Input::Numbers(v)=>v.first().copied().unwrap_or(0.),_=>0.};
        self.published = match self.task {
            Task::Scalar=>Output::Number(x*x+1.),
            Task::Pipeline=>Output::Number((x*x+1.).sqrt()+x.sin()),
            Task::Matrix=>{
                let a=[[x,2.],[3.,4.]];let b=[[2.,0.],[1.,3.]];let mut c=[[0.;2];2];
                for i in 0..2 {for j in 0..2 {for k in 0..2 {c[i][j]+=a[i][k]*b[k][j];}}}
                Output::Number(c[0][0]+c[1][1])
            },
            Task::Map=>Output::Number([(1.,10.),(2.,20.),(3.,30.)].iter().find(|(k,_)|*k==x).expect("missing map key").1+1.),
            Task::Branch=>Output::Number(if x==0. {100.} else {x*x+1.}),
            Task::Recursion=>{let mut sum=0.;for i in 1..=x as u64 {sum+=i as f64;} Output::Number(sum)},
            Task::Record=>{struct Record{square:f64,value:f64} let r=Record{square:x*x,value:x};Output::Number(r.square+r.value+1.)},
            Task::State=>{let n=self.turns as f64;Output::Number(n*n+1.)},
            Task::Oscillator=>{self.velocity-=self.position*0.01;self.position+=self.velocity*0.01;Output::Number(self.position)},
            Task::Wide=>{let mut sum=0.;for i in 0..32 {sum+=x*(i+1) as f64+i as f64;}Output::Number(sum)},
            Task::Chain=>{let mut v=x;for _ in 0..128 {v=v*1.0001+0.01;}Output::Number(v)},
            Task::Filter=>{let v:Vec<_>=input.numbers().iter().filter(|v|**v>0.).map(|v|v*v).collect();Output::Matrix([1,v.len()],Arc::new(v))},
            Task::Collection=>{let mut v=vec![x,2.,3.];v.sort_by(f64::total_cmp);v.dedup();Output::Set(Arc::new(v))},
            Task::Strings=>Output::Number(match input.text() {""=>0.,"é"=>1.,"é"=>2.,"👩🏽‍💻"=>3.,"\r\n"=>4.,_=>9.}),
            Task::Graphemes=>{let line=input.text().lines().next().unwrap_or("");Output::Number(match line.graphemes(true).nth(1) {Some("é")=>1.,Some("é")=>2.,_=>3.})},
            Task::Fsm=>if self.turns==1 {self.captured=Some(input.text().to_owned());Output::Unpublished} else {Output::Bool(self.captured.as_deref()==Some("é"))},
            Task::Join(op)=>join(op,x),
            Task::Graph=>{
                let mut v=[0.;8];v[0]=1.;
                for _ in 0..7 {let mut n=v;n[1]+=v[0]*2.;for(a,b)in[(1,2),(2,3),(3,1),(4,5),(5,6),(6,7)]{n[b]+=v[a];}n[4]+=v[3]*x;v=n;}
                Output::Matrix([8,1],Arc::new(v.to_vec()))
            },
            Task::Ekf=>Output::Matrix([1,12],Arc::new(self.ekf.step(input.numbers()).to_vec())),
        };
        // Input admission keeps an owned copy; callers can change their next frame without publishing a result.
        self.previous=Some(input.clone());
    }
}

fn join(op:u8,key:f64)->Output {
    let left=[(key,10.),(key,11.),(2.,12.),(3.,13.)];let right=[(1.,20.),(1.,21.),(2.,22.),(4.,23.)];
    let mut rows=Vec::new();let mut matched=[false;4];
    for (k,l) in left {
        let mut any=false;
        for (i,(rk,r)) in right.iter().enumerate() {if k==*rk {any=true;matched[i]=true;if op<4 {rows.push(vec![Some(k),Some(l),Some(*r)]);}}}
        if (op==4 && any)||(op==5 && !any) {rows.push(vec![Some(k),Some(l)]);}
        if !any && (op==1||op==3) {rows.push(vec![Some(k),Some(l),None]);}
    }
    if op==2||op==3 {for (i,(k,r)) in right.iter().enumerate() {if !matched[i] {rows.push(vec![Some(*k),None,Some(*r)]);}}}
    Output::Table(op>=4,Arc::new(rows))
}

fn mul<const R:usize,const K:usize,const C:usize>(a:[[f64;K];R],b:[[f64;C];K])->[[f64;C];R] {
    let mut out=[[0.;C];R];for i in 0..R {for j in 0..C {for k in 0..K {out[i][j]+=a[i][k]*b[k][j];}}}out
}
fn transpose<const R:usize,const C:usize>(a:[[f64;C];R])->[[f64;R];C] {let mut out=[[0.;R];C];for i in 0..R {for j in 0..C {out[j][i]=a[i][j];}}out}
fn add<const R:usize,const C:usize>(a:[[f64;C];R],b:[[f64;C];R])->[[f64;C];R] {let mut out=a;for i in 0..R {for j in 0..C {out[i][j]+=b[i][j];}}out}
struct Ekf { state:[f64;3], covariance:[[f64;3];3] }
impl Ekf {
    fn new()->Self {Self{state:[2.,1.,0.15],covariance:[[1.,0.,0.],[0.,1.,0.],[0.,0.,0.05]]}}
    fn step(&mut self,v:&[f64])->[f64;12] {
        let [speed,yaw,distance,bearing]:[f64;4]=v.try_into().unwrap();let dt=0.05;
        let (si,co)=(self.state[2].sin(),self.state[2].cos());
        let f=[[1.,0.,-speed*si*dt],[0.,1.,speed*co*dt],[0.,0.,1.]];
        let g=[[co*dt,0.],[si*dt,0.],[0.,dt]];
        let predicted=[self.state[0]+speed*co*dt,self.state[1]+speed*si*dt,self.state[2]+yaw*dt];
        let p=add(mul(mul(f,self.covariance),transpose(f)),mul(mul(g,[[0.04,0.],[0.,0.0025]]),transpose(g)));
        let (dx,dy)=(25.-predicted[0],-10.-predicted[1]);let q=dx*dx+dy*dy;let r=q.sqrt();
        let h=[[-dx/r,-dy/r,0.],[dy/q,-dx/q,-1.]];let noise=[[0.25,0.],[0.,0.0009]];
        let innovation=[[distance-r],[bearing-(dy.atan2(dx)-predicted[2])]];
        let s=add(mul(mul(h,p),transpose(h)),noise);let d=s[0][0]*s[1][1]-s[0][1]*s[1][0];
        let inv=[[s[1][1]/d,-s[0][1]/d],[-s[1][0]/d,s[0][0]/d]];
        let gain=mul(mul(p,transpose(h)),inv);let correction=mul(gain,innovation);
        for i in 0..3 {self.state[i]=predicted[i]+correction[i][0];}
        let kh=mul(gain,h);let mut a=[[0.;3];3];for i in 0..3 {for j in 0..3 {a[i][j]=if i==j {1.} else {0.};a[i][j]-=kh[i][j];}}
        let joseph=add(mul(mul(a,p),transpose(a)),mul(mul(gain,noise),transpose(gain)));
        for i in 0..3 {for j in 0..3 {self.covariance[i][j]=0.5*(joseph[i][j]+joseph[j][i]);}}
        let mut out=[0.;12];out[..3].copy_from_slice(&self.state);for i in 0..3 {for j in 0..3 {out[3+i*3+j]=self.covariance[i][j];}}out
    }
}

enum Probe { Numbers(Weak<Vec<f64>>), Rows(Weak<Vec<Vec<Option<f64>>>>) }
fn probe(v:&Output)->Option<Probe> {match v {Output::Matrix(_,v)|Output::Set(v)=>Some(Probe::Numbers(Arc::downgrade(v))),Output::Table(_,v)=>Some(Probe::Rows(Arc::downgrade(v))),_=>None}}
fn run(request:Value)->Value {
    assert_eq!(request["protocol"],1);let task=Task::parse(request["oracle"].as_str().unwrap());
    let text=request["input_kind"]=="string";
    let frames:Vec<Input>=request["schedule"].as_array().unwrap().iter().map(|frame| {
        let f=frame.as_array().unwrap();if text {assert_eq!(f.len(),1);Input::Text(f[0].as_str().unwrap().to_owned())}
        else {Input::Numbers(f.iter().map(|x|x.as_f64().unwrap()).collect())}
    }).collect();assert!(!frames.is_empty());assert!(frames.iter().all(|f|task.validate(f)));
    let count=request["iterations"].as_u64().unwrap() as usize;assert!(count>0);
    let warm=request["warmup"].as_u64().unwrap_or(0) as usize;
    {let mut w=Instance::new(task);for i in 0..warm {w.turn(black_box(&frames[i%frames.len()]));black_box(&w.published);}}
    let verify=request["action"]=="verify";let retain=request["retain_snapshots"]==true;
    let abort=request["abort_before_accept"]==true;let reject=request["reject_before_accept"]==true;
    let mut instance=Instance::new(task);let mut outputs=Vec::new();let mut before=Vec::new();let mut retained=Vec::new();
    // Probes are outside the measured loop. Snapshots themselves are retained inside it.
    let mut probes=Vec::new();let invalid=Input::Numbers(vec![0.,1.]);
    let (alloc0,bytes0)=(ALLOCS.load(Relaxed),BYTES.load(Relaxed));let start=Instant::now();
    for i in 0..count {
        let frame=black_box(&frames[i%frames.len()]);
        if verify && i>0 {before.push(instance.published.json());}
        if abort {let prepared=instance.prepare(frame).unwrap();black_box(prepared);}
        if reject {assert!(instance.prepare(black_box(&invalid)).is_err());}
        instance.turn(frame);black_box(&instance.published);
        if retain {retained.push(instance.published.clone());}
        if verify {outputs.push(instance.published.json());}
    }
    let seconds=start.elapsed().as_secs_f64();let (allocs,bytes)=(ALLOCS.load(Relaxed)-alloc0,BYTES.load(Relaxed)-bytes0);
    let final_output=instance.published.json();let retained_outputs:Vec<_>=if verify {retained.iter().map(Output::json).collect()} else {vec![]};
    if let Some(p)=probe(&instance.published) {probes.push(p);}
    for v in &retained {if let Some(p)=probe(v) {probes.push(p);}}
    let teardown=Instant::now();drop(retained);drop(instance);let teardown_seconds=teardown.elapsed().as_secs_f64();
    let released=probes.iter().all(|p|match p {Probe::Numbers(p)=>p.upgrade().is_none(),Probe::Rows(p)=>p.upgrade().is_none()});assert!(released);
    json!({"protocol":1,"outcome":"ok","iterations":count,"output_name":request["output"],
        "outputs":outputs,"before_execution":before,"retained_outputs":retained_outputs,"final_output":final_output,
        "owned_outputs_released":released,"metrics":{"resident_turn_seconds":seconds/count as f64,
        "rust_call_seconds":seconds/count as f64,"execution_block_seconds":seconds,"execution_allocations":allocs,
        "execution_requested_bytes":bytes,"teardown_seconds":teardown_seconds}})
}
fn main() {let mut input=String::new();io::stdin().read_to_string(&mut input).unwrap();let response=run(serde_json::from_str(&input).unwrap());println!("{response}");}
