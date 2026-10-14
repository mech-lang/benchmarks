:- module(m, []).
:- use_module(library(pcre), [re_foldl/6]).
count_match(_, A, A).
p :- re_foldl(count_match, "a", "a", 0, _, []).
