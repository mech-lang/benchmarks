# Untimed source/BEAM binding and actual instruction capture. No workload call.
[output, main_source, support_source, lock_fd, lock_inode] = System.argv()
true = File.stat!("/dev/fd/" <> lock_fd).inode == String.to_integer(lock_inode)
true = System.version() == "1.20.4"
true = :erlang.system_info(:otp_release) == ~c"29"
true = :erlang.system_info(:version) == ~c"17.1"
true = :erlang.system_info(:emu_flavor) == :jit
true = :erlang.system_info(:schedulers_online) == 8
true = :erlang.system_info(:dirty_cpu_schedulers_online) == 1
true = :erlang.system_info(:dirty_io_schedulers) == 1
true = :erlang.system_info(:thread_pool_size) == 1
true = :erlang.system_info(:wordsize) == 8
for {module, source, name} <- [{Clbg.Main, main_source, "main"}, {Clbg.Support, support_source, "support"}] do
  {:module, ^module} = Code.ensure_loaded(module)
  path = :code.which(module)
  bytes = File.read!(List.to_string(path))
  {:ok, {^module, chunks}} = :beam_lib.chunks(bytes, [:compile_info, :debug_info, :exports, :imports, ~c"Code"])
  true = Path.expand(List.to_string(chunks[:compile_info][:source])) == Path.expand(source)
  {:debug_info_v1, :elixir_erl, {:elixir_v1, %{module: ^module, file: file}, _}} = chunks[:debug_info]
  true = Path.expand(file) == Path.expand(source)
  {:beam_file, ^module, _, _, _, _} = disassembly = :beam_disasm.file(bytes)
  for {stem, term} <- [{"chunks", chunks}, {"disassembly", disassembly}] do
    File.write!(Path.join(output, name <> "-" <> stem <> ".etf"), :erlang.term_to_binary(term), [:exclusive])
    File.write!(Path.join(output, name <> "-" <> stem <> ".txt"), inspect(term, pretty: true, width: 120, limit: :infinity, printable_limit: :infinity) <> "\n", [:exclusive])
  end
end
IO.puts("ELIXIR=" <> System.version())
for field <- [:otp_release, :version, :system_architecture, :emu_flavor, :schedulers_online,
              :dirty_cpu_schedulers_online, :dirty_io_schedulers, :thread_pool_size, :wordsize,
              :garbage_collection] do
  IO.puts(Atom.to_string(field) <> "=" <> inspect(:erlang.system_info(field)))
end
IO.puts("NO_WORKLOAD_CALLS=true")
