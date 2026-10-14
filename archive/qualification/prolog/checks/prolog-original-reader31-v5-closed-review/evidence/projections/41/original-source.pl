:- module(m, []).
count_match(_, A, A).
p :- re_foldl(count_match, "a", "a", 0, _, []).
