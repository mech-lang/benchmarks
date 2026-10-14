:- module(m, []).
p(X) :- (X=1, X>0 -> true ; fail).
