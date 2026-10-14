:- module(knucleotide_map_inspection, [main/0]).
:- use_module(library(http/json), [json_write_dict/2]).
:- use_module(library(hashtable), [ht_pairs/2]).

% Diagnostic only: the candidate constructs every table; this helper serializes it.
pair_rows([], []).
pair_rows([Key-Count|Pairs], [[Key,Count]|Rows]) :- pair_rows(Pairs, Rows).
map_rows([], [], _, []).
map_rows([Width|Widths], [Table|Tables], Length, [Row|Rows]) :-
    ht_pairs(Table, Pairs), keysort(Pairs, Sorted), pair_rows(Sorted, Values),
    Windows is max(0, Length - Width + 1),
    Row = _{width:Width,windows:Windows,pairs:Values},
    map_rows(Widths, Tables, Length, Rows).
checked :-
    current_prolog_flag(argv, [Target]),
    load_files(Target, [silent(true),imports([])]),
    set_stream(user_input, encoding(octet)),
    clbg_knucleotide:find_third(Sequence), string_length(Sequence, Length),
    atom_string(SequenceAtom, Sequence), atom(SequenceAtom),
    Widths = [1,2,3,4,6,12,18],
    clbg_knucleotide:all_maps(Widths, SequenceAtom, Length, Tables),
    map_rows(Widths, Tables, Length, Rows),
    json_write_dict(current_output, _{length:Length,sequence_is_atom:true,widths:Widths,maps:Rows}), nl.
main :- catch(checked, Error, (print_message(error, Error), halt(1))), halt(0).
