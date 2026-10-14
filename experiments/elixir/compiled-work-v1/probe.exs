# DRAFT, UNEXECUTED. This diagnostic is never a timing sample or admission verdict.
# argv: one JSON spec, decoded by retained OTP 29's :json.decode/1.
# Required keys: artifact_dir, ebin, main_source, support_source,
# main_beam_sha256, support_beam_sha256, benchmark, arguments, lock_fd, lock_inode.
# The controller supplies the already qualified bounded stdin and compares raw stdout.
# Application modules are loaded from retained bytes; neither is compiled here.
defmodule CompiledWorkDraft do
  @arguments %{
    "nbody" => ["2"], "mandelbrot" => ["9"], "spectralnorm" => ["3"],
    "binarytrees" => ["4"], "fannkuchredux" => ["5"], "fasta" => ["31"],
    "pidigits" => ["27"], "knucleotide" => ["0"],
    "regexredux" => ["0"], "revcomp" => ["0"]
  }
  @functions %{
    "nbody" => [main: 1, planet: 7, steps: 2, advance: 1, energy: 1],
    "mandelbrot" => [main: 1, row: 6, inside: 5],
    "spectralnorm" => [main: 1, rounds: 3, ata: 1, multiply: 2, a: 2],
    "binarytrees" => [main: 1, tree: 1, check: 1, repeat: 3, depths: 4],
    "fannkuchredux" => [main: 1, visit: 7, ready: 2, carry: 4, rotate: 2, flips: 1, flip_work: 2],
    "fasta" => [main: 1, cumulative: 1, repeated: 5, random: 6, choose: 2, finish: 3],
    "pidigits" => [main: 1, emit: 8],
    "knucleotide" => [main: 1, header_name: 1, sequence: 3, count: 4],
    "regexredux" => [main: 1, count: 4, replace: 3, replace: 6],
    "revcomp" => [main: 1, collect: 4, record: 2, wrap: 3]
  }
  @returns %{
    "nbody" => [advance: 1, energy: 1], "binarytrees" => [tree: 1],
    "fannkuchredux" => [flips: 1], "regexredux" => [replace: 3],
    "revcomp" => [record: 2]
  }

  def require!(true, _message), do: :ok
  def require!(_, message), do: raise(ArgumentError, message)

  def artifact(directory, name, term) do
    File.write!(Path.join(directory, name <> ".etf"), :erlang.term_to_binary(term), [:exclusive])
    File.write!(Path.join(directory, name <> ".txt"),
      inspect(term, pretty: true, limit: :infinity, printable_limit: :infinity, width: 120) <> "\n", [:exclusive])
  end

  def count_trace_pattern() do
    # With the worker's :arity flag, only this extra message carries data.
    # Preserve small prefixes/terminal maps; middle calls carry two scalars.
    [{[ :"$1", :"$2", :"$3", :"$4"],
      [{:orelse, {:"=<", :"$3", 2}, {:>, {:+, :"$3", :"$2"}, {:byte_size, :"$1"}}}],
      [{:message, :"$_"}]},
     {[ :"$1", :"$2", :"$3", :"$4"], [],
      [{:message, {{:"$2", :"$3"}}}]}]
  end

  def sequence_trace_pattern() do
    # Repeated line-list/accumulator copies otherwise exceed the trace byte bound.
    [{[ :"$1", :"$2", :"$3"],
      [{:orelse, {:"=:=", :"$1", []}, {:"=:=", :"$3", []}}], [{:message, :"$_"}]},
     {[ :"$1", :"$2", :"$3"], [],
      [{:message, {{{:length, :"$1"}, :"$2", {:length, :"$3"}}}}]}]
  end

  def run(spec) do
    output = Map.fetch!(spec, "artifact_dir")
    benchmark = Map.fetch!(spec, "benchmark")
    arguments = Map.fetch!(spec, "arguments")
    require!(File.dir?(output), "Controller must create a fresh artifact directory")
    require!(Map.fetch!(@arguments, benchmark) == arguments, "Unexpected diagnostic size")
    require!(System.version() == "1.20.4", "Unexpected Elixir")
    require!(:erlang.system_info(:otp_release) == ~c"29", "Unexpected OTP")
    require!(:erlang.system_info(:version) == ~c"17.1", "Unexpected ERTS")
    require!(:erlang.system_info(:emu_flavor) == :jit, "Expected retained JIT")
    require!(:erlang.system_info(:schedulers_online) == 8, "Unexpected scheduler policy")
    require!(:erlang.system_info(:wordsize) == 8, "Unexpected word size")
    require!(String.starts_with?(List.to_string(:erlang.system_info(:system_architecture)), "aarch64-apple-"), "Unexpected architecture")
    require!(File.stat!("/dev/fd/" <> to_string(Map.fetch!(spec, "lock_fd"))).inode == Map.fetch!(spec, "lock_inode"), "Common mutex descriptor identity differs")
    require!(:code.is_loaded(Clbg.Main) == false and :code.is_loaded(Clbg.Support) == false, "Application already loaded")
    tables = for {module, stem} <- [{Clbg.Main, "main"}, {Clbg.Support, "support"}], into: %{} do
      path = Path.join(Map.fetch!(spec, "ebin"), Atom.to_string(module) <> ".beam")
      bytes = File.read!(path)
      digest = Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
      require!(digest == Map.fetch!(spec, stem <> "_beam_sha256"), "Retained BEAM digest differs")
      {:ok, {^module, chunks}} = :beam_lib.chunks(bytes, [:compile_info, :debug_info, :exports, :imports, ~c"Code"])
      source = Map.fetch!(spec, stem <> "_source") |> Path.expand()
      require!(Path.expand(List.to_string(Keyword.fetch!(chunks, :compile_info)[:source])) == source, "Compile source binding differs")
      {:debug_info_v1, :elixir_erl, {:elixir_v1, %{module: ^module, file: debug_source, definitions: definitions}, _}} = Keyword.fetch!(chunks, :debug_info)
      require!(Path.expand(debug_source) == source and is_list(definitions) and definitions != [], "Debug source binding differs")
      # Direct Code-chunk disassembly is distinct evidence from compiler debug definitions.
      {:beam_file, ^module, _exports, _attributes, _compile_info, functions} = disassembly = :beam_disasm.file(bytes)
      artifact(output, stem <> "-chunks", chunks)
      artifact(output, stem <> "-disassembly", disassembly)
      artifact(output, stem <> "-function-inventory", for {:function, name, arity, entry, _code} <- functions, do: {name, arity, entry})
      {:module, ^module} = :code.load_binary(module, String.to_charlist(path), bytes)
      require!(Path.expand(List.to_string(:code.which(module))) == Path.expand(path), "Loaded path differs")
      {module, functions}
    end
    explicit = Map.fetch!(@functions, benchmark)
    # Preserve the actual compiler-generated pair/axis callback arguments for review.
    generated = if benchmark == "nbody" do
      for {:function, name, arity, _entry, _code} <- tables[Clbg.Main],
          String.starts_with?(Atom.to_string(name), ["-advance/1-", "-energy/1-"]), do: {name, arity}
    else
      []
    end
    targets = Enum.uniq(explicit ++ generated)
    returned = Map.get(@returns, benchmark, [])
    for {name, arity} <- targets do
      mfa = {Clbg.Main, name, arity}
      require!(:erlang.trace_pattern(mfa, true, [:call_count]) == 1, "Missing compiled count target #{inspect(mfa)}")
      pattern = cond do
        benchmark == "knucleotide" and name == :count ->
          count_trace_pattern()
        benchmark == "knucleotide" and name == :sequence ->
          sequence_trace_pattern()
        benchmark == "knucleotide" -> [{:_, [], [{:message, :"$_"}]}]
        {name, arity} in returned -> [{:_, [], [{:return_trace}]}]
        true -> true
      end
      require!(:erlang.trace_pattern(mfa, pattern, [:local]) == 1, "Missing compiled call target #{inspect(mfa)}")
    end
    # input and write are authentic retained helpers; only the subject worker is traced.
    argument_message = if benchmark == "knucleotide", do: [{:message, :"$_"}], else: []
    require!(:erlang.trace_pattern({Clbg.Support, :input, 0},
      [{:_, [], [{:return_trace} | argument_message]}], [:local]) == 1, "Missing authentic input target")
    require!(:erlang.trace_pattern({Clbg.Support, :write, 1},
      [{:_, [], argument_message}], [:local]) == 1, "Missing authentic output target")
    parent = self()
    {worker, monitor} = spawn_monitor(fn ->
      receive do
        :go ->
          outcome = try do
            {:ok, apply(Clbg.Main, :main, [arguments])}
          catch
            kind, reason -> {:error, kind, reason, __STACKTRACE__}
          end
          send(parent, {:subject_done, self(), outcome})
          receive do
            :release -> :ok
          end
      end
    end)
    trace_flags = if benchmark == "knucleotide", do: [:arity], else: []
    require!(:erlang.trace(worker, true, [:call, {:tracer, self()} | trace_flags]) == 1, "Worker tracing failed")
    raw = File.open!(Path.join(output, "trace-framed.etf"), [:write, :binary, :exclusive])
    send(worker, :go)
    {events, outcome, raw_bytes} = try do
      collect(worker, monitor, raw, [], nil, nil, 0, 0)
    after
      File.close(raw)
    end
    counts = for {name, arity} <- targets, into: %{} do
      {:call_count, count} = :erlang.trace_info({Clbg.Main, name, arity}, :call_count)
      {{name, arity}, count}
    end
    :erlang.trace(worker, false, [:call])
    send(worker, :release)
    receive do
      {:DOWN, ^monitor, :process, ^worker, :normal} -> :ok
      {:DOWN, ^monitor, :process, ^worker, reason} -> raise "Worker exit: #{inspect(reason)}"
    after
      5_000 -> raise "Worker did not exit"
    end
    artifact(output, "call-counts", counts)
    artifact(output, "subject-outcome", outcome)
    require!(match?({:ok, _}, outcome), "Subject failed; raw trace preserved")
    require!(length(calls(events, :main, 1)) == 1, "Expected exactly one subject main call")
    require!(length(calls(events, :write, 1, Clbg.Support)) == 1, "Expected one authentic output call")
    observed = check(benchmark, events, counts)
    artifact(output, "dynamic-observations", observed)
    summary = %{
      "schema" => "elixir-compiled-work-draft-observation-v1",
      "status" => "dynamic-observations-recorded-awaiting-instruction-review",
      "benchmark" => benchmark, "arguments" => arguments,
      "main_beam_sha256" => Map.fetch!(spec, "main_beam_sha256"),
      "support_beam_sha256" => Map.fetch!(spec, "support_beam_sha256"),
      "subject_main_executions" => 1, "subject_modules_recompiled" => 0,
      "dynamic_assertions_passed" => true,
      "trace_events" => length(events), "trace_artifact_bytes" => raw_bytes,
      "common_mutex_inherited" => true, "source_work_qualified" => false,
      "common_mutex_fd" => Map.fetch!(spec, "lock_fd"),
      "common_mutex_inode" => Map.fetch!(spec, "lock_inode"),
      "compiled_work_qualified" => false, "chart_admission" => false,
      "direct_instruction_review_complete" => false,
      "tree_normal_gc_lifetime_proven" => false,
      "pidigits_two_division_dominance_proven" => false,
      "trace_retention_caveat" => "Trace copies and return-trace frames perturb retention; no normal-GC or scored-memory claim."
    }
    File.write!(Path.join(output, "summary.json"), :json.encode(summary), [:exclusive])
  end

  # Each record is a four-byte big-endian length followed by one external term.
  # The trace-delivered barrier is requested only after main has returned while
  # the monitored worker remains alive. It closes the event stream before checks.
  defp collect(worker, monitor, raw, events, outcome, barrier, count, bytes) do
    receive do
      {:trace, ^worker, _kind, _mfa} = event ->
        record(worker, monitor, raw, events, outcome, barrier, count, bytes, event)
      {:trace, ^worker, _kind, _mfa, _value} = event ->
        record(worker, monitor, raw, events, outcome, barrier, count, bytes, event)
      {:subject_done, ^worker, result} ->
        require!(outcome == nil, "Duplicate subject completion")
        collect(worker, monitor, raw, events, result, :erlang.trace_delivered(worker), count, bytes)
      {:trace_delivered, ^worker, ^barrier} when barrier != nil ->
        {Enum.reverse(events), outcome, bytes}
      {:DOWN, ^monitor, :process, ^worker, reason} -> raise "Premature worker exit: #{inspect(reason)}"
    after
      30_000 -> raise "Trace collection deadline exceeded"
    end
  end

  defp record(worker, monitor, raw, events, outcome, barrier, count, bytes, event) do
    term = :erlang.term_to_binary(event)
    total = bytes + 4 + byte_size(term)
    require!(count < 100_000 and total <= 8_388_608, "Bounded trace budget exceeded")
    :ok = IO.binwrite(raw, <<byte_size(term)::unsigned-big-32, term::binary>>)
    collect(worker, monitor, raw, [event | events], outcome, barrier, count + 1, total)
  end

  defp calls(events, function, arity, module \\ Clbg.Main) do
    Enum.flat_map(events, fn
      {:trace, _pid, :call, {^module, ^function, arguments}} when is_list(arguments) and length(arguments) == arity -> [arguments]
      {:trace, _pid, :call, {^module, ^function, ^arity}, arguments} when is_list(arguments) and length(arguments) == arity -> [arguments]
      _ -> []
    end)
  end
  defp returns(events, function, arity, module \\ Clbg.Main) do
    for {:trace, _pid, :return_from, {^module, ^function, ^arity}, value} <- events, do: value
  end

  def check("binarytrees", events, counts) do
    trees = returns(events, :tree, 1)
    roots = Enum.map(trees, fn {identity, _left, _right} -> identity end)
    require!(length(roots) == 4398 and Enum.all?(roots, &is_reference/1), "Expected 4,398 allocated node identities")
    require!(MapSet.size(MapSet.new(roots)) == length(roots), "Shared or reused node identity")
    constructed = Map.new(trees, fn {identity, _, _} = node -> {identity, node} end)
    {stack, constructed_count} = Enum.reduce(events, {[], 0}, fn
      {:trace, _, :call, {Clbg.Main, :tree, [depth]}}, {stack, amount} ->
        require!(is_integer(depth) and depth >= 0 and depth <= 7, "Invalid constructor depth")
        {[depth | stack], amount}
      {:trace, _, :return_from, {Clbg.Main, :tree, 1}, node}, {[depth | stack], amount} ->
        identities = tree_identities(node, depth, constructed)
        require!(MapSet.size(identities) == Bitwise.bsl(1, depth + 1) - 1, "Returned graph size differs")
        {stack, amount + 1}
      {:trace, _, :return_from, {Clbg.Main, :tree, 1}, _}, {[], _} ->
        raise ArgumentError, "Constructor return without its call"
      _, state -> state
    end)
    require!(stack == [] and constructed_count == 4398, "Constructor calls/returns do not reconcile")
    checked = for [{identity, _left, _right}] <- calls(events, :check, 1), do: identity
    require!(Enum.frequencies(checked) == Map.new(roots, &{&1, 1}), "Every allocated node must be checked exactly once")
    for [node = {identity, _, _}] <- calls(events, :check, 1) do
      require!(Map.fetch!(constructed, identity) === node, "Check did not receive the actual returned node graph")
    end
    depth_calls = calls(events, :depths, 4)
    require!(Enum.map(depth_calls, &Enum.take(&1, 2)) == [[4, 6], [6, 6], [8, 6]], "Depth schedule differs")
    long_roots = Enum.map(depth_calls, fn [_depth, _maximum, {identity, _, _}, _out] -> identity end)
    require!(length(Enum.uniq(long_roots)) == 1, "Long root changes across depth processing")
    long_root = hd(long_roots)
    for [_depth, _maximum, node, _out] <- depth_calls do
      require!(Map.fetch!(constructed, long_root) === node, "Long-lived root graph changed")
      require!(MapSet.size(tree_identities(node, 6, constructed)) == 127, "Long-lived graph differs")
    end
    final_depth_index = Enum.find_index(events, fn
      {:trace, _, :call, {Clbg.Main, :depths, [8, 6, _, _]}} -> true
      _ -> false
    end)
    final_checks = calls(Enum.drop(events, final_depth_index + 1), :check, 1)
    require!(match?([{^long_root, _, _}], hd(final_checks)), "Long root not checked after repeats")
    require!(length(final_checks) == 127, "Long-lived tree traversal incomplete")
    require!(counts[{:tree, 1}] == 4398 and counts[{:check, 1}] == 4398, "Tree/check counters differ")
    for {depth, iterations} <- [{4, 64}, {6, 16}] do
      rows = for [n, ^depth, sum] <- calls(events, :repeat, 3), do: {n, sum}
      nodes = Bitwise.bsl(1, depth + 1) - 1
      require!(rows == Enum.map(iterations..0//-1, &{&1, (iterations - &1) * nodes}), "Fresh-tree repeat schedule differs")
    end
    %{allocated_node_identities: 4398, checked_node_identities: 4398,
      actual_returned_child_graphs_checked: 4398, disjoint_left_right_descendants: true,
      unchanged_long_root_through_depths: long_root, final_long_check_nodes: 127,
      normal_gc_lifetime_proven: false,
      pending: "Review tree/1 make_ref and fresh tuple paths, both recursive calls, repeat construction, and depths/4 live Y-register root across repeat. Trace copies do not prove normal GC lifetime."}
  end

  def check("pidigits", events, counts) do
    states = calls(events, :emit, 8)
    require!(hd(states) == [1, 0, 1, 1, 0, 27, "", []], "Spigot initial state differs")
    transitions = for [current, next] <- Enum.chunk_every(states, 2, 1, :discard) do
      [q, r, t, k, count, wanted, _line, _out] = current
      require!(count < wanted and q > 0 and t > 0, "Invalid candidate state")
      three = div(3 * q + r, t)
      four = div(4 * q + r, t)
      require!(three == Integer.floor_div(3 * q + r, t) and four == Integer.floor_div(4 * q + r, t), "Truncation differs from floor at observed state")
      expected = if three == four do
        [10 * q, 10 * (r - t * three), t, k, count + 1, wanted]
      else
        factor = 2 * k + 1
        [q * k, (r + 2 * q) * factor, t * factor, k + 1, count, wanted]
      end
      require!(Enum.take(next, 6) == expected, "Spigot transition differs")
      %{q: q, r: r, t: t, k: k, count: count, three: three, four: four, admitted: three == four}
    end
    require!(Enum.slice(List.last(states), 4, 2) == [27, 27], "Spigot terminal count differs")
    require!(Enum.count(transitions, & &1.admitted) == 27 and Enum.any?(transitions, &(not &1.admitted)), "Need admitted and rejected candidate observations")
    require!(counts[{:emit, 8}] == length(states), "Spigot trace count differs")
    state_integers = Enum.flat_map(states, &Enum.take(&1, 3))
    largest_integer = Enum.max(Enum.map(state_integers, &abs/1))
    require!(largest_integer > 9_223_372_036_854_775_807, "No greater-than-signed-64-bit arithmetic state observed")
    maximum_integer_bits = largest_integer |> Integer.digits(2) |> length()
    %{candidate_states: transitions, terminal_state: List.last(states),
      signed_64_bit_range_exceeded: true, maximum_state_integer_bits: maximum_integer_bits,
      actual_two_divisions_proven: false,
      pending: "In emit/8 direct disassembly, establish two separate div instructions dominate the equality branch for every nonterminal candidate; follow 3*q+r and 4*q+r numerator and common t denominator data flow. Opcode count or BIF tracing alone is insufficient."}
  end

  def check("knucleotide", events, counts) do
    observations = calls(events, :count, 4)
    terminals = Enum.filter(observations, fn [dna, k, offset, _map] -> offset + k > byte_size(dna) end)
    require!(Enum.map(terminals, &Enum.at(&1, 1)) == [1, 2, 3, 4, 6, 12, 18], "Seven complete widths not observed")
    dna = hd(terminals) |> hd()
    require!(byte_size(dna) >= 18 and byte_size(dna) <= 16_384, "Unexpected bounded DNA size")
    [raw_input] = returns(events, :input, 0, Clbg.Support)
    require!(is_binary(raw_input) and dna == selected_dna(raw_input), "Count input is not the complete selected THREE DNA")
    require!(Enum.all?(observations, fn [sequence, _, _, _] -> sequence == dna end), "Width inputs differ")
    offsets = Enum.flat_map(events, fn
      {:trace, _, :call, {Clbg.Main, :count, 4}, [_sequence, width, offset, _map]} -> [{width, offset}]
      {:trace, _, :call, {Clbg.Main, :count, 4}, {width, offset}} -> [{width, offset}]
      _ -> []
    end)
    expected_offsets = for k <- [1, 2, 3, 4, 6, 12, 18], offset <- 0..(byte_size(dna) - k + 1), do: {k, offset}
    require!(offsets == expected_offsets, "Per-width count offset schedule differs")
    widths = for [^dna, k, offset, actual] <- terminals do
      windows = for position <- 0..(byte_size(dna) - k), do: binary_part(dna, position, k)
      expected = Enum.frequencies(windows)
      require!(offset == byte_size(dna) - k + 1 and actual == expected, "Incomplete/incorrect overlapping map for width #{k}")
      query = %{3 => "GGT", 4 => "GGTA", 6 => "GGTATT", 12 => "GGTATTTTAATT", 18 => "GGTATTTTAATTTATAGT"}[k]
      if query, do: require!(Enum.any?(Map.keys(actual), &(&1 != query)), "No nonquery keys observed")
      early = for [^dna, ^k, position, _] <- observations, position <= 2, do: position
      require!(early == Enum.to_list(0..min(2, offset)), "Initial/early full map observations missing or repeated")
      %{width: k, windows: length(windows), count_invocations: offset + 1,
        distinct_keys: map_size(actual), complete_map: actual}
    end
    for [^dna, k, offset, actual] <- observations, offset <= 2 do
      expected = if offset == 0, do: %{}, else: Enum.frequencies(for position <- 0..(offset - 1), do: binary_part(dna, position, k))
      require!(actual == expected, "Observed prefix update differs")
    end
    expected_calls = Enum.sum(for k <- [1, 2, 3, 4, 6, 12, 18], do: byte_size(dna) - k + 2)
    require!(counts[{:count, 4}] == expected_calls, "Full overlapping traversal call count differs")
    %{dna_bytes: byte_size(dna), selected_dna_sha256: Base.encode16(:crypto.hash(:sha256, dna), case: :lower),
      selected_input_contents_bound: true, count_invocations: expected_calls, widths: widths,
      pending: "Review Code-chunk count/4 binary_part, increment-by-one recursion and Map.update dependency; main/1 must construct all maps before lookup."}
  end

  def check("nbody", events, counts) do
    advance = calls(events, :advance, 1) |> Enum.map(&hd/1)
    advanced = returns(events, :advance, 1)
    energy = calls(events, :energy, 1) |> Enum.map(&hd/1)
    require!(length(advance) == 2 and length(advanced) == 2 and length(energy) == 2, "Two-step/energy calls differ")
    require!(hd(energy) == hd(advance) and Enum.at(advance, 1) == hd(advanced) and List.last(energy) == List.last(advanced), "Body state chain broken")
    require!(Enum.map(calls(events, :steps, 2), &hd/1) == [2, 1, 0], "Step countdown differs")
    require!(Enum.all?(advance ++ advanced, &(tuple_size(&1) == 5)), "Body cardinality differs")
    require!(counts[{:advance, 1}] == 2 and counts[{:energy, 1}] == 2, "Main workload counters differ")
    %{steps: 2, energies: returns(events, :energy, 1), callback_counts: counts,
      pending: "Review generated advance/energy callbacks: ten unordered pairs, both velocity triples, then all five positions. Raw generated callback arguments retained."}
  end

  def check("spectralnorm", events, counts) do
    products = calls(events, :multiply, 2)
    require!(length(products) == 40 and Enum.all?(products, fn [input, _] -> tuple_size(input) == 3 end), "Forty full-size products required")
    require!(Enum.map(products, &Enum.at(&1, 1)) == List.flatten(List.duplicate([false, true], 20)), "Transpose order differs")
    entries = calls(events, :a, 2) |> Enum.frequencies()
    require!(entries == Map.new(for i <- 0..2, j <- 0..2, do: {[i, j], 40}), "Implicit matrix entry traversal incomplete")
    require!(counts[{:ata, 1}] == 20 and counts[{:rounds, 3}] == 11 and counts[{:a, 2}] == 360, "Spectral work counters differ")
    %{matrix_vector_products: 40, matrix_entries: 360, size: 3,
      pending: "Review multiply generated reduction body and a/2 formula, ata ordering and ten rounds in direct instructions."}
  end

  def check("mandelbrot", events, counts) do
    pixels = for [x, y, 9, _byte, _bits, _out] <- calls(events, :row, 6), x < 9, do: {x, y}
    require!(pixels == (for y <- 0..8, x <- 0..8, do: {x, y}), "Pixel traversal incomplete")
    expected = Enum.flat_map(pixels, fn {x, y} -> inside_states(2.0 * x / 9 - 1.5, 2.0 * y / 9 - 1.0, 0.0, 0.0, 0) end)
    actual = calls(events, :inside, 5)
    require!(actual == expected and counts[{:inside, 5}] == length(expected), "Escape recurrence states differ")
    require!(counts[{:row, 6}] == 90, "Partial row completion differs")
    %{pixels: 81, row_calls: 90, recurrence_calls: length(actual),
      pending: "Review Code-chunk recurrence limit50, escape test and row MSB shifts/partial-byte padding; compare saved PBM bytes."}
  end
  def check("fannkuchredux", events, counts) do
    visits = calls(events, :visit, 7)
    permutations = Enum.map(visits, &hd/1)
    require!(length(visits) == 120 and MapSet.size(MapSet.new(permutations)) == 120, "Need all 5! distinct permutations")
    require!(Enum.all?(permutations, &(Enum.sort(Tuple.to_list(&1)) == [0, 1, 2, 3, 4])), "Invalid permutation")
    require!(Enum.map(visits, &Enum.at(&1, 4)) == Enum.to_list(0..119), "Rank traversal differs")
    require!(Enum.map(calls(events, :flips, 1), &hd/1) == permutations, "Permutation flip work missing")
    amounts = returns(events, :flips, 1)
    require!(amounts == Enum.map(permutations, &(independent_flips(Tuple.to_list(&1), 0))), "Flip counts differ")
    require!(counts[{:visit, 7}] == 120 and counts[{:flips, 1}] == 120, "Factorial work counters differ")
    %{permutations: 120, maximum: Enum.max(amounts),
      pending: "Review rotate/carry/ready mixed-radix traversal, flip_work prefix reversal, checksum parity and maximum accumulation."}
  end
  def check("fasta", events, counts) do
    repeated = calls(events, :repeated, 5)
    require!(Enum.map(repeated, &Enum.take(&1, 3)) == (for offset <- 0..62, do: [62 - offset, offset, rem(offset, 60)]), "ALU traversal differs")
    random = calls(events, :random, 6)
    {iub, homo} = Enum.split(random, 94)
    require!(length(iub) == 94 and length(homo) == 156, "Random record work differs")
    require!(Enum.at(hd(iub), 2) == 42 and Enum.at(hd(homo), 2) == Enum.at(List.last(iub), 2), "Seed continuity differs")
    for {rows, size} <- [{iub, 93}, {homo, 155}] do
      require!(Enum.map(rows, &hd/1) == Enum.to_list(size..0//-1), "Random countdown differs")
      require!(Enum.map(rows, &Enum.at(&1, 3)) == Enum.map(0..size, &rem(&1, 60)), "Random wrapping columns differ")
      for [current, next] <- Enum.chunk_every(rows, 2, 1, :discard) do
        require!(Enum.at(next, 2) == rem(Enum.at(current, 2) * 3877 + 29573, 139968), "LCG recurrence differs")
      end
    end
    require!(counts[{:random, 6}] == 250 and counts[{:repeated, 5}] == 63, "FASTA counters differ")
    %{alu_bytes: 62, random_bytes: 248, continued_seed: Enum.at(hd(homo), 2),
      pending: "Review exact ALU literal and modulo length, cumulative tables, choose thresholds and 60-byte wrapping; bounded stdout supplies byte comparison."}
  end

  def check("regexredux", events, _counts) do
    starts = for [regex, text, 0, 0] <- calls(events, :count, 4), do: {Regex.source(regex), text}
    patterns = ["agggtaaa|tttaccct", "[cgt]gggtaaa|tttaccc[acg]", "a[act]ggtaaa|tttacc[agt]t", "ag[act]gtaaa|tttac[agt]ct", "agg[act]taaa|ttta[agt]cct", "aggg[acg]aaa|ttt[cgt]ccct", "agggt[cgt]aa|tt[acg]accct", "agggta[cgt]a|t[acg]taccct", "agggtaa[cgt]|[acg]ttaccct"]
    require!(Enum.map(starts, &elem(&1, 0)) == patterns, "Nine independent variant scans missing")
    replacements = calls(events, :replace, 3)
    replaced = returns(events, :replace, 3)
    expected = [{">[^\n]*\n|\n", ""}, {"tHa[Nt]", "<4>"}, {"aND|caN|Ha[DS]|WaS", "<3>"}, {"a[NSt]|BY", "<2>"}, {"<[^>]*>", "|"}, {"\\|[^|][^|]*\\|", "-"}]
    require!(Enum.map(replacements, fn [regex, _, replacement] -> {Regex.source(regex), replacement} end) == expected, "Cleaning/substitution order differs")
    require!(length(replaced) == 6, "Replacement returns incomplete")
    require!(Enum.all?(starts, &(elem(&1, 1) == hd(replaced))), "Variant inputs differ")
    require!(Enum.map(tl(replacements), &Enum.at(&1, 1)) == Enum.take(replaced, 5), "Substitutions do not consume predecessor output")
    %{independent_variant_scans: 9, cleaning_passes: 1, serial_substitutions: 5,
      pending: "Review count/4 and replace/6 Regex.run offsets/nonoverlap, copied unmatched spans and tails; regex runtime publication remains separate."}
  end

  def check("revcomp", events, _counts) do
    records = calls(events, :record, 2)
    rendered = returns(events, :record, 2)
    require!(length(records) == 3 and length(rendered) == 3, "Expected three IUPAC fixture records")
    pairs = Map.new(Enum.zip(~c"ACGTUMRWSYKVHDBNacgtumrwsykvhdbn", ~c"TGCAAKYWSRMBDHVNTGCAAKYWSRMBDHVN"))
    sizes = for {[header, parts], output} <- Enum.zip(records, rendered) do
      dna = parts |> Enum.reverse() |> IO.iodata_to_binary()
      complemented = dna |> :binary.bin_to_list() |> Enum.reverse() |> Enum.map(&Map.fetch!(pairs, &1))
      lines = complemented |> Enum.chunk_every(60) |> Enum.map(&[&1, 10])
      require!(IO.iodata_to_binary(output) == IO.iodata_to_binary([header, 10, lines]), "Whole-record reverse complement differs")
      byte_size(dna)
    end
    require!(Enum.any?(sizes, &(&1 == 0)) and Enum.any?(sizes, &(&1 > 0)), "Empty/nonempty record coverage missing")
    %{records: 3, sequence_bytes: sizes,
      pending: "Review collect header/parts boundaries, complete reversal and every complement lookup, and wrap traversal in direct instructions."}
  end

  defp tree_identities({identity, nil, nil} = node, 0, constructed) do
    require!(is_reference(identity) and Map.fetch!(constructed, identity) === node, "Unbound returned leaf identity")
    MapSet.new([identity])
  end
  defp tree_identities({identity, left, right} = node, depth, constructed) when depth > 0 do
    require!(is_reference(identity) and Map.fetch!(constructed, identity) === node, "Child is not its actual returned constructor graph")
    left_ids = tree_identities(left, depth - 1, constructed)
    right_ids = tree_identities(right, depth - 1, constructed)
    require!(MapSet.disjoint?(left_ids, right_ids), "Left/right descendants share an identity")
    descendants = MapSet.union(left_ids, right_ids)
    require!(not MapSet.member?(descendants, identity), "Parent identity reused by a descendant")
    MapSet.put(descendants, identity)
  end
  defp tree_identities(_, _, _), do: raise(ArgumentError, "Returned tree shape/depth differs")

  # Independent byte-oriented record selection over the authentic helper return.
  # No subject sequence/header helper or subject histogram is used by this reader.
  defp selected_dna(input) do
    lines = input |> :binary.replace("\r\n", "\n", [:global])
      |> :binary.replace("\r", "\n", [:global]) |> :binary.split("\n", [:global])
    {found, reversed} = Enum.reduce_while(lines, {false, []}, fn
      <<">", _::binary>>, {true, out} -> {:halt, {true, out}}
      <<">", header::binary>>, {false, out} ->
        name = case :binary.match(header, [" ", "\t"]) do
          :nomatch -> header
          {position, _} -> binary_part(header, 0, position)
        end
        {:cont, {name == "THREE", out}}
      <<";", _::binary>>, state -> {:cont, state}
      line, {true, out} ->
        upper = for <<code <- line>>, into: <<>> do
          normalized = if code in ?a..?z, do: code - 32, else: code
          require!(normalized in ~c"ACGT", "Selected input contains an invalid nucleotide")
          <<normalized>>
        end
        {:cont, {true, [upper | out]}}
      _, state -> {:cont, state}
    end)
    require!(found, "Authentic input has no exact THREE record")
    reversed |> Enum.reverse() |> IO.iodata_to_binary()
  end

  defp inside_states(cr, ci, zr, zi, 50), do: [[cr, ci, zr, zi, 50]]
  defp inside_states(cr, ci, zr, zi, count) do
    next_r = zr * zr - zi * zi + cr
    next_i = 2.0 * zr * zi + ci
    tail = if next_r * next_r + next_i * next_i > 4.0, do: [], else: inside_states(cr, ci, next_r, next_i, count + 1)
    [[cr, ci, zr, zi, count] | tail]
  end

  defp independent_flips([0 | _], count), do: count
  defp independent_flips([first | _] = permutation, count) do
    {prefix, suffix} = Enum.split(permutation, first + 1)
    independent_flips(Enum.reverse(prefix) ++ suffix, count + 1)
  end
end

[specification] = System.argv()
CompiledWorkDraft.run(:json.decode(File.read!(specification)))
