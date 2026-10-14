% Draft source only: not compiled, executed, qualified, or measured.
:- module(clbg_revcomp_linear, [main/0, diagnostic/1]).
:- initialization(run, main).

run :-
    execute(main).

diagnostic(Capacity) :-
    execute(main_with_capacity(Capacity)).

execute(Goal) :-
    catch(run_checked(Goal), Error, report_error(Error)),
    halt(0).

run_checked(Goal) :-
    set_stream(user_input, encoding(octet)),
    set_stream(user_output, encoding(octet)),
    (   call(Goal)
    ->  flush_output(user_output)
    ;   throw(error(application_goal_failed, clbg_revcomp_linear:main/0))
    ).

report_error(Error) :-
    print_message(error, Error),
    halt(1).

block_capacity(65536).

main :-
    block_capacity(Capacity),
    main_with_capacity(Capacity).

main_with_capacity(Capacity) :-
    (   integer(Capacity), Capacity > 0
    ->  read_blocks(Capacity, state(start, none, [], [], 0))
    ;   throw(error(domain_error(positive_integer, Capacity), main_with_capacity/1))
    ).

% Sequence chunks and pending codes are stored in reverse arrival order.
% Header chunks are put in forward order when their line terminates.
read_blocks(Capacity, State0) :-
    read_string(user_input, Capacity, Block),
    (   Block == ""
    ->  finish_input(State0)
    ;   string_codes(Block, Codes),
        consume_codes(Codes, Capacity, State0, State),
        read_blocks(Capacity, State)
    ).

consume_codes([], _, State, State).
consume_codes([Code|Rest], Capacity, State0, State) :-
    consume_code(Code, Capacity, State0, State1),
    consume_codes(Rest, Capacity, State1, State).

consume_code(13, _, State0, State) :- !,
    end_line(State0, State).
consume_code(10, _, State0, State) :- !,
    end_line(State0, State).
consume_code(Code, Capacity, state(start, Header, Chunks, Pending, Count), State) :- !,
    (   Code =:= 62
    ->  emit_record(Header, Chunks, Pending),
        push_code(Code, Capacity, [], [], 0, HeaderChunks, HeaderPending, HeaderCount),
        State = state(header, building(HeaderChunks, HeaderPending, HeaderCount), [], [], 0)
    ;   Code =:= 59
    ->  State = state(ignore, Header, Chunks, Pending, Count)
    ;   Header == none
    ->  State = state(ignore, Header, Chunks, Pending, Count)
    ;   push_code(Code, Capacity, Chunks, Pending, Count, Chunks1, Pending1, Count1),
        State = state(sequence, Header, Chunks1, Pending1, Count1)
    ).
consume_code(Code, Capacity, state(header, building(Chunks0, Pending0, Count0), [], [], 0), State) :- !,
    push_code(Code, Capacity, Chunks0, Pending0, Count0, Chunks, Pending, Count),
    State = state(header, building(Chunks, Pending, Count), [], [], 0).
consume_code(_, _, state(ignore, Header, Chunks, Pending, Count), state(ignore, Header, Chunks, Pending, Count)) :- !.
consume_code(Code, Capacity, state(sequence, Header, Chunks0, Pending0, Count0), State) :-
    push_code(Code, Capacity, Chunks0, Pending0, Count0, Chunks, Pending, Count),
    State = state(sequence, Header, Chunks, Pending, Count).

push_code(Code, Capacity, Chunks0, Pending0, Count0, Chunks, Pending, Count) :-
    Added = [Code|Pending0],
    Count1 is Count0 + 1,
    (   Count1 =:= Capacity
    ->  reverse(Added, Forward),
        string_codes(Chunk, Forward),
        Chunks = [Chunk|Chunks0],
        Pending = [],
        Count = 0
    ;   Chunks = Chunks0,
        Pending = Added,
        Count = Count1
    ).

finish_chunk([], Chunks, Chunks) :- !.
finish_chunk(Pending, Chunks, [Chunk|Chunks]) :-
    reverse(Pending, Forward),
    string_codes(Chunk, Forward).

end_line(state(header, building(Chunks0, Pending, _), [], [], 0), State) :- !,
    finish_chunk(Pending, Chunks0, Reversed),
    reverse(Reversed, Forward),
    State = state(start, header(Forward), [], [], 0).
end_line(state(_, Header, Chunks, Pending, Count), state(start, Header, Chunks, Pending, Count)).

finish_input(state(header, Builder, [], [], 0)) :- !,
    end_line(state(header, Builder, [], [], 0), State),
    finish_input(State).
finish_input(state(_, Header, Chunks, Pending, _)) :-
    emit_record(Header, Chunks, Pending).

emit_record(none, _, _) :- !.
emit_record(header(HeaderChunks), Chunks0, Pending) :-
    emit_header(HeaderChunks),
    nl,
    finish_chunk(Pending, Chunks0, Chunks),
    emit_chunks(Chunks, [], 0, Tail),
    emit_tail(Tail).

emit_header([]).
emit_header([Chunk|Rest]) :-
    format('~s', [Chunk]),
    emit_header(Rest).

emit_chunks([], Line, _, Line).
emit_chunks([Chunk|Rest], Line0, Column0, Tail) :-
    string_codes(Chunk, Codes),
    reverse(Codes, Reversed),
    emit_codes(Reversed, Line0, Column0, Line, Column),
    emit_chunks(Rest, Line, Column, Tail).

emit_codes([], Line, Column, Line, Column).
emit_codes([Original|Rest], Line0, Column0, Line, Column) :-
    complement(Original, Code),
    Added = [Code|Line0],
    Column1 is Column0 + 1,
    (   Column1 =:= 60
    ->  reverse(Added, Forward),
        format('~s~n', [Forward]),
        emit_codes(Rest, [], 0, Line, Column)
    ;   emit_codes(Rest, Added, Column1, Line, Column)
    ).

emit_tail([]) :- !.
emit_tail(Reversed) :-
    reverse(Reversed, Forward),
    format('~s~n', [Forward]).

complement(Code, Complement) :-
    (   Code >= 97, Code =< 122
    ->  Upper is Code - 32
    ;   Upper = Code
    ),
    complement_upper(Upper, Code, Complement).

complement_upper(65, _, 84) :- !.
complement_upper(67, _, 71) :- !.
complement_upper(66, _, 86) :- !.
complement_upper(68, _, 72) :- !.
complement_upper(71, _, 67) :- !.
complement_upper(72, _, 68) :- !.
complement_upper(75, _, 77) :- !.
complement_upper(77, _, 75) :- !.
complement_upper(78, _, 78) :- !.
complement_upper(83, _, 83) :- !.
complement_upper(82, _, 89) :- !.
complement_upper(85, _, 65) :- !.
complement_upper(84, _, 65) :- !.
complement_upper(87, _, 87) :- !.
complement_upper(86, _, 66) :- !.
complement_upper(89, _, 82) :- !.
complement_upper(_, Code, _) :-
    throw(error(domain_error(iupac_nucleotide, Code), complement/2)).
