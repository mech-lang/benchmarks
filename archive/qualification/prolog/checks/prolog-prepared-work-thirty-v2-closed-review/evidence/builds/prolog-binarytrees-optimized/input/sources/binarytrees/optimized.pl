:- module(clbg_binarytrees, [main/0]).
:- use_module('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/prolog-comparison/20261013/work-qualification/prepared-work-v2-probes-v1/builds/prolog-binarytrees-optimized/input/support/clbg_observer.pl', []).
:- use_module('../../support/clbg_io').
:- initialization(clbg_io:run(clbg_binarytrees:main), main).

make(Depth, Tree) :-
    functor(Tree, node, 2),
    arg(1, Tree, Left),
    arg(2, Tree, Right),
    (   Depth > 0
    ->  ChildDepth is Depth - 1,
        make(ChildDepth, Left),
        make(ChildDepth, Right)
    ;   Left = none,
        Right = none
    ).

check(Tree, Count) :-
    arg(1, Tree, Left),
    arg(2, Tree, Right),
    (   Left == none
    ->  Count = 1
    ;   check(Left, LeftCount),
        check(Right, RightCount),
        Count is LeftCount + RightCount + 1
    ).

checks(0, _, Total, Total) :- !.
checks(Iterations, Depth, Accumulator, Total) :-
    clbg_observer:temporary_begin(Iterations, Depth),
    make(Depth, Tree),
    check(Tree, Value),
    clbg_observer:temporary_checked(Iterations, Depth, Tree, Value),
    NextTotal is Accumulator + Value,
    Remaining is Iterations - 1,
    checks(Remaining, Depth, NextTotal, Total).

depths(Depth, Maximum) :-
    (   Depth =< Maximum
    ->  Iterations is 1 << (Maximum - Depth + 4),
        checks(Iterations, Depth, 0, Total),
        format('~d\t trees of depth ~d\t check: ~d~n', [Iterations, Depth, Total]),
        NextDepth is Depth + 2,
        depths(NextDepth, Maximum)
    ;   true
    ).

stretch(Depth) :-
    make(Depth, Tree),
    check(Tree, Count),
    clbg_observer:stretch_checked(Depth, Tree, Count),
    format('stretch tree of depth ~d\t check: ~d~n', [Depth, Count]).

main :-
    size(N),
    Maximum is max(6, N),
    StretchDepth is Maximum + 1,
    stretch(StretchDepth),
    make(Maximum, LongLived),
    clbg_observer:retain(Maximum, LongLived),
    depths(4, Maximum),
    check(LongLived, Count),
    clbg_observer:retained_checked(Maximum, LongLived, Count),
    format('long lived tree of depth ~d\t check: ~d~n', [Maximum, Count]).
