:- module(m, []).
p(X) :- catch((X=1,true), Error, throw(Error)).
