(* SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
 * The Computer Language Benchmarks Game, k-nucleotide adaptation.
 * Original algorithms contributed by Troestler Christophe, modified by
 * Mauricio Fernandez, optimized by Fabrice Le Fessant, and modified by
 * Roman Kashitsyn; see program/knucleotide-ocaml-3.html.
 * The retained knucleotide-ocaml-1.html source, fixed by glacialthinker,
 * also informed mutable counts.
 *)
module Counts = Hashtbl.Make(struct
  type t = int
  let equal (a : int) b = a = b
  let hash value = value
end)

let codes = Array.make 256 0
let () = String.iteri (fun code byte ->
  codes.(Char.code byte) <- code;
  codes.(Char.code (Char.lowercase_ascii byte)) <- code) "ATCG"

type selection = Seeking | Reading | Finished

let read_three table =
  let dna = Buffer.create 65536 in
  let consume state line =
    let length = String.length line in
    if length = 0 || line.[0] = ';' then state
    else match state, line.[0] with
    | Reading, '>' -> Finished
    | Seeking, '>' when length >= 6 && String.sub line 0 6 = ">THREE" &&
        (length = 6 || line.[6] = ' ' || line.[6] = '\t') -> Reading
    | Reading, _ -> String.iter (fun byte ->
        Buffer.add_char dna (Char.unsafe_chr table.(Char.code byte))) line; Reading
    | _ -> state
  in
  In_channel.input_all stdin |> String.map (function '\r' -> '\n' | byte -> byte)
  |> String.split_on_char '\n' |> List.fold_left consume Seeking |> ignore;
  Buffer.contents dna

let histogram width dna =
  let counts = Counts.create 16 and key = ref 0 in
  let mask = (1 lsl (2 * width)) - 1 in
  String.iteri (fun i byte ->
    key := ((!key lsl 2) lor Char.code byte) land mask;
    if i + 1 >= width then
      try incr (Counts.find counts !key)
      with Not_found -> Counts.add counts !key (ref 1)) dna;
  counts

let decode width key =
  String.init width (fun i -> "ATCG".[(key lsr (2 * (width - i - 1))) land 3])

let encode query =
  String.fold_left (fun key byte -> (key lsl 2) lor codes.(Char.code byte)) 0 query

let frequencies width dna =
  let counts = histogram width dna in
  let total = Counts.fold (fun _ count sum -> !count + sum) counts 0 in
  let entries = Counts.fold (fun key count rows -> (decode width key, !count) :: rows) counts [] in
  let order (a, x) (b, y) = let by_count = compare y x in
    if by_count = 0 then String.compare a b else by_count in
  List.iter (fun (key, count) -> Printf.printf "%s %.3f\n" key
    (100. *. float count /. float total)) (List.sort order entries);
  print_newline ()

let lookup query dna =
  let counts = histogram (String.length query) dna in
  let count = try !(Counts.find counts (encode query)) with Not_found -> 0 in
  Printf.printf "%d\t%s\n" count query

let () =
  if Sys.word_size <> 64 then invalid_arg "36-bit keys require 64-bit OCaml";
  let dna = read_three codes in
  List.iter (fun width -> frequencies width dna) [1; 2];
  List.iter (fun query -> lookup query dna)
    ["GGT"; "GGTA"; "GGTATT"; "GGTATTTTAATT"; "GGTATTTTAATTTATAGT"]
