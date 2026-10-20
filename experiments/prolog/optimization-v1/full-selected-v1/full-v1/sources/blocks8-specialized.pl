:- module(clbg_spectralnorm_blocks8, [main/0]).
:- use_module('../../support/clbg_io').
:- use_module(library(thread), [concurrent/3]).
:- use_module(library(lists), [append/2]).
:- initialization(clbg_io:run(clbg_spectralnorm_blocks8:main), main).

coefficient(I, J, Value) :-
    Sum is I + J,
    Denominator is (Sum * (Sum + 1)) div 2 + I + 1,
    Value is 1.0 / Denominator.

fill(Index, N, Vector) :-
    (   Index =< N
    ->  arg(Index, Vector, 1.0),
        Next is Index + 1,
        fill(Next, N, Vector)
    ;   true
    ).

row_forward(J, N, _, _, Accumulator, Accumulator) :- J >= N, !.
row_forward(J, N, I, Input, Accumulator, Sum) :-
    coefficient(I, J, A),
    Position is J + 1,
    arg(Position, Input, Value),
    NextAccumulator is Accumulator + (A * Value),
    NextJ is J + 1,
    row_forward(NextJ, N, I, Input, NextAccumulator, Sum).

row_transpose(J, N, _, _, Accumulator, Accumulator) :- J >= N, !.
row_transpose(J, N, I, Input, Accumulator, Sum) :-
    coefficient(J, I, A),
    Position is J + 1,
    arg(Position, Input, Value),
    NextAccumulator is Accumulator + (A * Value),
    NextJ is J + 1,
    row_transpose(NextJ, N, I, Input, NextAccumulator, Sum).

row_block_forward(I, End, _, _, []) :- I >= End, !.
row_block_forward(I, End, N, Input, [Value|Values]) :-
    row_forward(0, N, I, Input, 0.0, Value),
    NextI is I + 1,
    row_block_forward(NextI, End, N, Input, Values).

row_block_transpose(I, End, _, _, []) :- I >= End, !.
row_block_transpose(I, End, N, Input, [Value|Values]) :-
    row_transpose(0, N, I, Input, 0.0, Value),
    NextI is I + 1,
    row_block_transpose(NextI, End, N, Input, Values).

block_goals(8, _, _, _, [], []) :- !.
block_goals(Block, N, Row, Input, [Goal|Goals], [Values|Chunks]) :-
    NextBlock is Block + 1,
    First is (Block * N) div 8,
    End is (NextBlock * N) div 8,
    Goal =.. [Row, First, End, N, Input, Values],
    block_goals(NextBlock, N, Row, Input, Goals, Chunks).

apply(Input, N, Output) :-
    block_goals(0, N, row_block_forward, Input, Goals, Chunks),
    concurrent(8, Goals, []),
    append(Chunks, Values),
    Output =.. [vector|Values].

apply_transpose(Input, N, Output) :-
    block_goals(0, N, row_block_transpose, Input, Goals, Chunks),
    concurrent(8, Goals, []),
    append(Chunks, Values),
    Output =.. [vector|Values].

apply_ata(Input, N, Output) :-
    apply(Input, N, Intermediate),
    apply_transpose(Intermediate, N, Output).

power(0, U, V, _, U, V) :- !.
power(Iterations, Input, _, N, U, V) :-
    apply_ata(Input, N, NextV),
    apply_ata(NextV, N, NextU),
    Remaining is Iterations - 1,
    power(Remaining, NextU, NextV, N, U, V).

dots(Index, N, _, _, UV, VV, UV, VV) :- Index > N, !.
dots(Index, N, U, V, UV0, VV0, UV, VV) :-
    arg(Index, U, UI),
    arg(Index, V, VI),
    UV1 is UV0 + UI * VI,
    VV1 is VV0 + VI * VI,
    Next is Index + 1,
    dots(Next, N, U, V, UV1, VV1, UV, VV).

main :-
    size(N),
    (   N =:= 0
    ->  format('0.000000000~n', [])
    ;   functor(Seed, vector, N),
        fill(1, N, Seed),
        power(10, Seed, Seed, N, U, V),
        dots(1, N, U, V, 0.0, 0.0, UV, VV),
        Norm is sqrt(UV / VV),
        format('~9f~n', [Norm])
    ).
