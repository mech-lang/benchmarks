:- module(knucleotide_loc_targets, [main/0]).
:- use_module(library(http/json), [json_write_dict/2]).
truth(Goal, Value) :- (call(Goal) -> Value = true ; Value = false).
checked :-
    current_prolog_flag(argv, []),
    current_prolog_flag(version_data, swi(Major, Minor, Patch, Extra)),
    term_string(swi(Major, Minor, Patch, Extra), Version, [quoted(true),ignore_ops(true)]),
    current_prolog_flag(arch, Architecture), current_prolog_flag(home, Home),
    truth(predicate_property(system:atom_string(_,_), built_in), BuiltIn),
    truth(predicate_property(system:atom_string(_,_), foreign), Foreign),
    truth(predicate_property(system:atom_string(_,_), defined), Defined),
    truth(predicate_property(system:atom_string(_,_), meta_predicate(_)), Meta),
    json_write_dict(current_output, _{schema:"prolog-knucleotide-loc-builtin-metadata-v1",
        version:[Major,Minor,Patch],version_data:Version,architecture:Architecture,home:Home,
        selected_target:_{module:"system",name:"atom_string",arity:2,
                          built_in:BuiltIn,foreign:Foreign,defined:Defined,meta_predicate:Meta}}), nl.
main :- catch(checked, Error, (print_message(error, Error), halt(1))), halt(0).
