:- module(m, []).
p :- (catch(true, Error, throw(Error)) -> true ; fail).
