# Unscored observations of the retained compiled helper; no benchmark main runs.
[ebin, vectors, summary] = System.argv()
false = :code.is_loaded(Clbg.Main)
{:module, Clbg.Support} = Code.ensure_loaded(Clbg.Support)
true = Path.expand(List.to_string(:code.which(Clbg.Support))) ==
  Path.expand(Path.join(ebin, "Elixir.Clbg.Support.beam"))
alias Clbg.Support, as: S

true = System.version() == "1.20.4"
true = :erlang.system_info(:otp_release) == ~c"29"
true = :erlang.system_info(:version) == ~c"17.1"
true = :erlang.system_info(:emu_flavor) == :jit
true = :erlang.system_info(:schedulers_online) == 8

0 = S.size(["0"], 99)
23 = S.size(["23"], 99)
99 = S.size([], 99)
for arguments <- [["-1"], ["1", "2"], ["invalid"]] do
  raised = try do
    S.size(arguments, 99)
    false
  rescue
    ArgumentError -> true
  end
  true = raised
end
[] = Enum.to_list(S.indices(0))
[0] = Enum.to_list(S.indices(1))
[0, 1, 2, 3] = Enum.to_list(S.indices(4))
[""] = S.lines("")
["a", "b", "c", "d", ""] = S.lines("a\r\nb\rc\nd\n")
[<<0, 255>>, <<27>>] = S.lines(<<0, 255, 13, 10, 27>>)

count = vectors |> File.stream!() |> Enum.reduce(0, fn line, count ->
  [bits, digits, expected] = line |> String.trim_trailing("\n") |> String.split("\t")
  <<value::float-64>> = Base.decode16!(bits, case: :lower)
  ^expected = S.fixed(value, String.to_integer(digits))
  count + 1
end)
true = count > 1000

# Round-trip nonempty input through the exact same helper as the scored programs.
bytes = S.input()
true = byte_size(bytes) > 2 * 65_536
<<>> = S.input()
<<first::binary-size(1), second::binary-size(65_535), rest::binary>> = bytes
:ok = S.write([first, [second, rest]])
false = :code.is_loaded(Clbg.Main)
File.write!(summary,
  "format_vectors=#{count}\ninput_bytes=#{byte_size(bytes)}\n" <>
  "nonempty_input=true\nrepeated_eof=true\nmain_loaded=false\n", [:exclusive])
