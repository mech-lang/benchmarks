# Unscored admission observer, loaded before the unchanged retained runner.
# It never compiles an application module and writes no benchmark stdout.
spec = System.fetch_env!("CLBG_ELIXIR_BOUNDED_SPEC") |> File.read!() |> String.split("\n", trim: true)
[receipt, ebin, main_source, support_source, main_sha, support_sha, fd, inode] = spec
true = System.version() == "1.20.4"
true = :erlang.system_info(:otp_release) == ~c"29"
true = :erlang.system_info(:version) == ~c"17.1"
true = :erlang.system_info(:emu_flavor) == :jit
true = :erlang.system_info(:schedulers_online) == 8
true = :erlang.system_info(:wordsize) == 8
true = String.starts_with?(List.to_string(:erlang.system_info(:system_architecture)), "aarch64-apple-")
true = File.stat!("/dev/fd/" <> fd).inode == String.to_integer(inode)
false = :code.is_loaded(Clbg.Main)
false = :code.is_loaded(Clbg.Support)
for {module, source, wanted} <- [{Clbg.Main, main_source, main_sha}, {Clbg.Support, support_source, support_sha}] do
  beam = Path.join(ebin, Atom.to_string(module) <> ".beam")
  binary = File.read!(beam)
  true = Base.encode16(:crypto.hash(:sha256, binary), case: :lower) == wanted
  {:ok, {^module, chunks}} = :beam_lib.chunks(binary, [:compile_info, :debug_info])
  compiled_source = chunks |> Keyword.fetch!(:compile_info) |> Keyword.fetch!(:source) |> List.to_string() |> Path.expand()
  true = compiled_source == Path.expand(source)
  {:debug_info_v1, :elixir_erl, {:elixir_v1, %{module: ^module, file: debug_source, definitions: definitions}, _}} = Keyword.fetch!(chunks, :debug_info)
  true = Path.expand(debug_source) == Path.expand(source)
  true = is_list(definitions) and definitions != []
  {:module, ^module} = :code.load_binary(module, String.to_charlist(beam), binary)
  true = Path.expand(List.to_string(:code.which(module))) == Path.expand(beam)
end
File.write!(receipt, "elixir=1.20.4\notp=29\nerts=17.1\nexecution=beam-jit\nschedulers_online=8\nwordsize=8\narchitecture=aarch64-apple\ncommon_mutex_inherited=true\nsource_debug_bindings=2\nsubject_modules_recompiled=0\nmain_beam_sha256=" <> main_sha <> "\nsupport_beam_sha256=" <> support_sha <> "\n", [:exclusive])
