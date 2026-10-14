:- module(m, []).
run(G) :- call(G). main :- run(true).
