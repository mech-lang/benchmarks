:- module(clbg_pidigits, [main/0]).
:- use_module('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/prolog-comparison/20261013/work-qualification/prepared-work-v2-probes-v1/builds/prolog-pidigits-optimized/input/support/clbg_observer.pl', []).
:- use_module('../../support/clbg_io').
:- initialization(clbg_io:run(clbg_pidigits:main), main).

padding(0) :- !.
padding(N) :-
    put_code(32),
    Remaining is N - 1,
    padding(Remaining).

finish_line(Count, Column) :-
    (   Column > 0
    ->  Spaces is 10 - Column,
        padding(Spaces),
        format('\t:~d~n', [Count])
    ;   true
    ).

digits(N, N, Column, _, _, _, _) :-
    !,
    finish_line(N, Column).
digits(N, Count, Column, Q, R, T, K) :-
    Numerator3 is 3 * Q + R,
    Numerator4 is 4 * Q + R,
    Digit3 is Numerator3 div T,
    Digit4 is Numerator4 div T,
    clbg_observer:pi_candidate(Count, Q, R, T, K, Numerator3, Numerator4, Digit3, Digit4),
    (   Digit3 =:= Digit4
    ->  Code is 48 + Digit3,
        put_code(Code),
        NextCount is Count + 1,
        NextColumn0 is Column + 1,
        (   NextColumn0 =:= 10
        ->  format('\t:~d~n', [NextCount]),
            NextColumn = 0
        ;   NextColumn = NextColumn0
        ),
        NextQ is Q * 10,
        NextR is 10 * (R - Digit3 * T),
        digits(N, NextCount, NextColumn, NextQ, NextR, T, K)
    ;   Factor is 2 * K + 1,
        NextQ is Q * K,
        NextR is (2 * Q + R) * Factor,
        NextT is T * Factor,
        NextK is K + 1,
        digits(N, Count, Column, NextQ, NextR, NextT, NextK)
    ).

main :-
    size(N),
    current_prolog_flag(bounded, false),
    clbg_observer:pi_begin(N),
    digits(N, 0, 0, 1, 0, 1, 1),
    clbg_observer:pi_finished(N).
