:- module(prolog_spectral_state_probe, [main/0]).
:- use_module(library(http/json), [json_write_dict/2]).
:- use_module(library(thread), [concurrent/3]).
:- use_module(library(prolog_wrap), [wrap_predicate/4, unwrap_predicate/2]).

must(Goal, Label) :- (call(Goal) -> true ; throw(error(check_failed(Label), _))).
load_one(Path) :- load_files(Path, [imports([]), silent(true)]).
modules([clbg_spectralnorm,clbg_spectralnorm_serial,clbg_spectralnorm_blocks8]).
vector(N, Pattern, Vector) :-
    findall(Value, (between(1,N,I), input_value(Pattern,I,Value)), Values),
    Vector =.. [vector|Values].
input_value(positive,I,Value) :- Value is ((I*7) mod 13+1)/7.0.
input_value(signed,I,Value) :- Value is ((I*7) mod 13-6)/7.0.
representation(Value,Text) :- format(string(Text),'~17g',[Value]).
representations(Vector,Texts) :- Vector=..[_|Values],maplist(representation,Values,Texts).
compare_vector(N,Pattern,Operation,Candidate,Record) :-
    vector(N,Pattern,Input),
    Goal0=..[Operation,Input,N,Expected],call(clbg_spectralnorm:Goal0),
    Goal1=..[Operation,Input,N,Actual],call(Candidate:Goal1),
    must(Expected==Actual,vector_term_identity(N,Pattern,Operation,Candidate)),
    representations(Expected,ExpectedText),representations(Actual,ActualText),
    must(ExpectedText==ActualText,vector_roundtrip_identity(N,Pattern,Operation,Candidate)),
    Record=_{n:N,pattern:Pattern,operation:Operation,candidate:Candidate,
        strict_term_identity:true,decimal17_identity:true,components:ActualText}.

threads(Ids) :- findall(Id,thread_property(Id,status(_)),All),sort(All,Ids).
geometry(N,Record) :-
    vector(N,positive,Input),
    clbg_spectralnorm_blocks8:block_goals(0,N,row_block_forward,Input,Goals,Chunks),
    must(length(Goals,8),eight_goals(N)),must(length(Chunks,8),eight_results(N)),
    term_variables(Goals,Vars),must(length(Vars,8),distinct_result_variables(N)),
    must(maplist(var,Chunks),fresh_chunk_variables(N)),
    findall(_{block:B,first:First,end:End,rows:Rows},
      (nth0(B,Goals,Goal),Goal=..[Row,First,End,Size,GoalInput,_],
       must(Row==row_block_forward,orientation_specialized),must(Size==N,goal_size),
       must(ground(GoalInput),ground_input),must(GoalInput==Input,complete_input),
       F is (B*N) div 8,E is ((B+1)*N) div 8,
       must(First=:=F,first_boundary),must(End=:=E,end_boundary),Rows is End-First),Ranges),
    threads(Before),concurrent(8,clbg_spectralnorm_blocks8:Goals,[]),threads(After),
    must(Before==After,no_worker_leak(N)),
    findall(L,(member(Chunk,Chunks),length(Chunk,L)),Lengths),
    findall(R,(member(Range,Ranges),R=Range.rows),Lengths),
    append(Chunks,Values),must(length(Values,N),row_total(N)),
    clbg_spectralnorm:apply(Input,N,Expected),Expected=..[vector|ExpectedValues],
    must(Values==ExpectedValues,ordered_results(N)),
    Record=_{n:N,ranges:Ranges,result_lengths:Lengths,rows:N,workers_joined:true,
        exactly_eight_goals:true,ground_inputs:true,independent_results:true,ordered_results:true}.

counter(M,Name,Arity,Key) :-
    atomic_list_concat([M,Name],':',Key),flag(Key,_,0),functor(Head,Name,Arity),
    wrap_predicate(M:Head,spectral_work_count,Wrapped,(flag(Key,C,C+1),Wrapped)).
remove_counter(M,Name,Arity) :- PI=Name/Arity,unwrap_predicate(M:PI,spectral_work_count).
work(M,N,Record) :-
    counter(M,coefficient,3,KC),counter(M,apply,3,KA),
    counter(M,apply_transpose,3,KT),counter(M,apply_ata,3,KAA),
    vector(N,positive,Input),call(M:power(10,Input,Input,N,_,_)),
    flag(KC,C,C),flag(KA,A,A),flag(KT,T,T),flag(KAA,AA,AA),
    Expected is 40*N*N,
    must(C=:=Expected,coefficient_count(M,N)),must(A=:=20,forward_count(M,N)),
    must(T=:=20,transpose_count(M,N)),must(AA=:=20,ata_count(M,N)),
    remove_counter(M,coefficient,3),remove_counter(M,apply,3),
    remove_counter(M,apply_transpose,3),remove_counter(M,apply_ata,3),
    Record=_{module:M,n:N,coefficient_calls:C,forward_products:A,
        transpose_products:T,ata_applications:AA,library_wrapper:true,quantitative_benchmark:false}.

worker_outcomes(Record) :-
    threads(Before),
    must(\+concurrent(8,[true,fail,true],[]),worker_failure_propagated),
    catch(concurrent(8,[true,throw(spectral_probe_exception),true],[]),spectral_probe_exception,Caught=true),
    must(Caught==true,worker_exception_propagated),threads(After),
    must(Before==After,failure_exception_workers_joined),
    Record=_{failure_propagated:true,exception_propagated:true,workers_joined:true}.

checked :-
    current_prolog_flag(argv,Paths),must(length(Paths,3),three_sources),maplist(load_one,Paths),
    concurrent(8,[true,true,true,true,true,true,true,true],[]),
    findall(Record,(member(N,[1,2,3,5,7,8,9,10,15,16,17,31]),member(Pattern,[positive,signed]),
        member(Operation,[apply,apply_transpose,apply_ata]),
        member(Candidate,[clbg_spectralnorm_serial,clbg_spectralnorm_blocks8]),
        compare_vector(N,Pattern,Operation,Candidate,Record)),Vectors),
    findall(Record,(member(N,[1,2,3,5,7,8,9,10,15,16,17,31]),geometry(N,Record)),Geometry),
    worker_outcomes(Outcomes),modules(Modules),
    findall(Record,(member(M,Modules),member(N,[3,8]),work(M,N,Record)),Work),
    current_prolog_flag(version_data,swi(Major,Minor,Patch,_)),current_prolog_flag(gc,GC),
    current_prolog_flag(bounded,Bounded),current_prolog_flag(home,Home),current_prolog_flag(arch,Arch),
    json_write_dict(current_output,_{schema:'prolog-spectral-state-work-probe.v1',status:'PASSED',
       version:[Major,Minor,Patch],architecture:Arch,gc:GC,bounded:Bounded,home:Home,
       vectors:Vectors,geometry:Geometry,worker_outcomes:Outcomes,work:Work,
       numerical_rule:'strict term identity and identical17 significant digit representations; no tolerance',
       work_scope:'bounded native wrappers of unchanged compiled predicates, not full-size instrumentation'}),nl.
main :- catch(checked,Error,(print_message(error,Error),halt(1))),halt(0).
