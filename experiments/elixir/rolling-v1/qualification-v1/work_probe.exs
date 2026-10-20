# Untimed VM trace of the exact production BEAM. No source instrumentation,
# private export rewrite, replacement map, benchmark kernel or timing admission.
defmodule RollingWorkProbe do
  @widths [1, 2, 3, 4, 6, 12, 18]
  def require!(true, _message), do: :ok
  def require!(_, message), do: raise(ArgumentError, message)

  def capture(worker, monitor, raw, events, outcome, barrier) do
    receive do
      {:subject_done, ^worker, value} ->
        capture(worker, monitor, raw, events, value, :erlang.trace_delivered(:all))
      {:trace_delivered, :all, marker} when marker == barrier ->
        {Enum.reverse(events), outcome}
      {:DOWN, ^monitor, :process, ^worker, reason} ->
        raise "Traced worker exited before release: #{inspect(reason)}"
      message when elem(message, 0) == :trace ->
        bytes = :erlang.term_to_binary(message)
        IO.binwrite(raw, [<<byte_size(bytes)::unsigned-big-32>>, bytes])
        capture(worker, monitor, raw, [message | events], outcome, barrier)
    after
      30_000 -> raise "Traced workload timed out"
    end
  end

  def key_text(key, width) when is_integer(key) do
    for shift <- (width - 1)..0//-1, into: <<>> do
      <<:binary.at("ACGT", Bitwise.band(Bitwise.bsr(key, 2 * shift), 3))>>
    end
  end
  def key_text(key, _width) when is_binary(key), do: key

  def check(events, dna, variant) do
    initial = %{width: %{}, pending: %{}, indices: Map.new(@widths, &{&1, 0}),
      histograms: Map.new(@widths, &{&1, %{}}), initial_maps: [], updates: [], spawned: []}
    expected = Map.new(@widths, fn width ->
      count = max(0, byte_size(dna) - width + 1)
      rows = if count == 0, do: [], else: for(index <- 0..(count - 1), do: binary_part(dna, index, width))
      {width, List.to_tuple(rows)}
    end)
    state = Enum.reduce(events, initial, fn message, state ->
      case message do
        {:trace, _pid, :spawn, child, _mfa} -> %{state | spawned: [child | state.spawned]}
        {:trace, pid, :call, {Clbg.Main, :histogram, [encoded, width]}} ->
          require!(width in @widths, "Unplanned width")
          actual = for <<code <- dna>>, into: <<>>, do: <<Enum.find_index(~c"ACGT", &(&1 == code))>>
          require!(encoded == actual, "Encoded sequence differs from independent selected record")
          %{state | width: Map.put(state.width, pid, width)}
        {:trace, pid, :return_from, {Clbg.Main, :histogram, 2}, counts} ->
          width = Map.fetch!(state.width, pid)
          %{state | histograms: Map.put(state.histograms, width, counts)}
        {:trace, pid, :call, {Clbg.Main, :count, [binary, second, third, counts]}} ->
          width = if variant == "parent", do: second, else: Map.fetch!(state.width, pid)
          if variant == "parent", do: require!(binary == dna, "Parent selected sequence differs")
          first = if variant == "parent", do: third == 0, else: byte_size(binary) == max(0, byte_size(dna) - width + 1)
          if first, do: require!(counts == %{}, "Table did not start from default empty map")
          initial_maps = if first, do: [[width, Atom.to_string(:erts_internal.term_type(counts)), map_size(counts)] | state.initial_maps], else: state.initial_maps
          terminal = if variant == "parent", do: third + width > byte_size(binary), else: binary == <<>>
          histograms = if terminal, do: Map.put(state.histograms, width, counts), else: state.histograms
          %{state | initial_maps: initial_maps, histograms: histograms}
        {:trace, pid, :call, {Map, :update, [counts, key, 1, callback]}} ->
          require!(is_function(callback, 1), "Missing standard update callback")
          width = if variant == "parent", do: byte_size(key), else: Map.fetch!(state.width, pid)
          index = Map.fetch!(state.indices, width)
          require!(index < tuple_size(expected[width]) and key_text(key, width) == elem(expected[width], index), "Occurrence key/order differs")
          require!(not Map.has_key?(state.pending, pid), "Nested/unpaired standard map update")
          %{state | pending: Map.put(state.pending, pid, {width, counts, key}), indices: Map.put(state.indices, width, index + 1)}
        {:trace, pid, :return_from, {Map, :update, 4}, updated} ->
          {width, counts, key} = Map.fetch!(state.pending, pid)
          previous = Map.get(counts, key, 0)
          require!(updated === Map.put(counts, key, previous + 1), "Standard map update did not perform exactly this increment")
          row = %{width: width, key: key_text(key, width), previous: previous, value: previous + 1,
            before_size: map_size(counts), after_size: map_size(updated),
            before_type: Atom.to_string(:erts_internal.term_type(counts)), after_type: Atom.to_string(:erts_internal.term_type(updated)),
            pid: inspect(pid)}
          %{state | pending: Map.delete(state.pending, pid), updates: [row | state.updates]}
        _ -> state
      end
    end)
    require!(state.pending == %{}, "Unpaired standard map update return")
    histograms = for width <- @widths do
      observed = state.histograms[width] |> Enum.map(fn {key, value} -> {key_text(key, width), value} end) |> Map.new()
      reference = expected[width] |> Tuple.to_list() |> Enum.frequencies()
      require!(observed == reference, "Whole histogram differs at width #{width}")
      require!(state.indices[width] == tuple_size(expected[width]), "Occurrence update total differs at width #{width}")
      %{width: width, updates: state.indices[width], distinct: map_size(observed), entries: Enum.sort(observed) |> Enum.map(&Tuple.to_list/1)}
    end
    %{histograms: histograms, updates: Enum.reverse(state.updates), initial_maps: Enum.reverse(state.initial_maps),
      update_invocations: length(state.updates), spawned: Enum.uniq(state.spawned)}
  end

  def run(spec_path) do
    spec = spec_path |> File.read!() |> :json.decode()
    output = spec["output"]
    true = File.stat!("/dev/fd/" <> spec["lock_fd"]).inode == spec["lock_inode"]
    true = System.version() == "1.20.4"
    true = :erlang.system_info(:otp_release) == ~c"29"
    true = :erlang.system_info(:version) == ~c"17.1"
    true = :erlang.system_info(:emu_flavor) == :jit
    true = :erlang.system_info(:schedulers_online) == 8
    {:module, Clbg.Main} = Code.ensure_loaded(Clbg.Main)
    path = Clbg.Main |> :code.which() |> List.to_string()
    true = Base.encode16(:crypto.hash(:sha256, File.read!(path)), case: :lower) == spec["main_beam_sha256"]
    pattern = [{:_, [], [{:message, :"$_"}, {:return_trace}]}]
    true = :erlang.trace_pattern({Map, :update, 4}, pattern, []) == 1
    true = :erlang.trace_pattern({Clbg.Main, :count, 4}, [{:_, [], [{:message, :"$_"}]}], [:local]) == 1
    if spec["variant"] != "parent", do: require!(:erlang.trace_pattern({Clbg.Main, :histogram, 2}, pattern, [:local]) == 1, "Histogram trace target missing")
    parent = self()
    {worker, monitor} = spawn_monitor(fn ->
      receive do
        :go ->
          outcome = try do
            Clbg.Main.main(["0"])
            :ok
          catch
            kind, reason -> {:error, kind, reason, __STACKTRACE__}
          end
          send(parent, {:subject_done, self(), outcome})
          receive do :release -> :ok end
      end
    end)
    true = :erlang.trace(worker, true, [:call, :procs, :set_on_spawn, {:tracer, self()}]) == 1
    raw = File.open!(Path.join(output, "trace-framed.etf"), [:write, :binary, :exclusive])
    send(worker, :go)
    {events, outcome} = try do capture(worker, monitor, raw, [], nil, nil) after File.close(raw) end
    :erlang.trace(worker, false, [:call, :procs, :set_on_spawn])
    :erlang.trace_pattern({Map, :update, 4}, false, [])
    :erlang.trace_pattern({Clbg.Main, :count, 4}, false, [:local])
    :erlang.trace_pattern({Clbg.Main, :histogram, 2}, false, [:local])
    send(worker, :release)
    receive do {:DOWN, ^monitor, :process, ^worker, :normal} -> :ok after 5_000 -> raise "Worker cleanup timeout" end
    require!(outcome == :ok, "Production worker failed: #{inspect(outcome)}")
    result = check(events, spec["dna"], spec["variant"])
    Process.sleep(50)
    require!(Enum.all?(result.spawned, &(not Process.alive?(&1))), "Application descendant remains alive")
    report = result |> Map.put(:spawned, Enum.map(result.spawned, &inspect/1))
      |> Map.merge(%{schema: "elixir-rolling-production-work-witness.v1", status: "PASSED", variant: spec["variant"],
        dna_length: byte_size(spec["dna"]), production_source_rewritten: false, standard_map_update_calls_traced: true,
        complete_histograms_compared: 7, application_descendants_cleaned: true, trace_events: length(events),
        main_beam_sha256: spec["main_beam_sha256"], quantitative_benchmark: false, chart_admission: false})
    File.write!(Path.join(output, "witness.json"), :json.encode(report), [:exclusive])
  end
end
RollingWorkProbe.run(hd(System.argv()))
