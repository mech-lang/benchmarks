:- module(m, []).
p(X) :- ((X=1 ; X=2) -> true ; X=3 -> fail ; true).
