:- module(prolog_spectral_runtime_probe,[main/0]).
:- use_module(library(http/json),[json_write_dict/2]).
:- use_module(library(thread),[concurrent/3]).
:- use_module(library(lists),[append/2]).
:- use_module(library(prolog_wrap),[wrap_predicate/4]).
property(Module,Head,Record) :-
    functor(Head,Name,Arity),
    (predicate_property(Module:Head,meta_predicate(Meta))->term_string(Meta,MetaText);MetaText="none"),
    (predicate_property(Module:Head,file(File))->true;File="builtin"),
    Record=_{module:Module,name:Name,arity:Arity,meta_predicate:MetaText,file:File}.
main :-
    current_prolog_flag(version_data,swi(Major,Minor,Patch,_)),
    current_prolog_flag(home,Home),current_prolog_flag(arch,Arch),current_prolog_flag(gc,GC),
    current_prolog_flag(bounded,Bounded),current_prolog_flag(stack_limit,Limit),current_prolog_flag(threads,Threads),
    property(thread,concurrent(_,_,_),Concurrent),property(lists,append(_,_),Append),
    property(system,_=.._,Univ),
    findall(File,source_file(File),Files),
    json_write_dict(current_output,_{schema:'prolog-spectral-runtime-probe.v1',version:[Major,Minor,Patch],
       architecture:Arch,home:Home,gc:GC,bounded:Bounded,stack_limit:Limit,threads:Threads,
       concurrent:Concurrent,append:Append,univ:Univ,loaded_sources:Files}),nl,halt(0).
