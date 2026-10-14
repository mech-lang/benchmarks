:- module(m, []).
count_match(_, A, A).
p :- pcre:re_foldl(count_match, "a", "a", 0, _, []).
