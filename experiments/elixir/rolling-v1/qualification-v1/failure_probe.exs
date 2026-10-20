# Untimed injected-failure descendant cleanup. The production candidate is not
# altered: this script loads only the separately hash-bound callback twin.
defmodule RollingFailureProbe do
  def require!(true, _), do: :ok
  def require!(_, message), do: raise(ArgumentError, message)
  def collect(worker, monitor, spawned, reason, barrier) do
    receive do
      {:trace, _parent, :spawn, child, _mfa} -> collect(worker, monitor, [child | spawned], reason, barrier)
      {:trace, _, _, _} -> collect(worker, monitor, spawned, reason, barrier)
      {:DOWN, ^monitor, :process, ^worker, why} ->
        collect(worker, monitor, spawned, why, :erlang.trace_delivered(:all))
      {:trace_delivered, :all, marker} when marker == barrier -> {Enum.uniq(spawned), reason}
    after 15_000 -> raise "Injected failure did not propagate" end
  end
  def wait_dead(pids, 0), do: require!(Enum.all?(pids, &(not Process.alive?(&1))), "Application descendant remains alive")
  def wait_dead(pids, remaining) do
    if Enum.any?(pids, &Process.alive?/1) do
      Process.sleep(20)
      wait_dead(pids, remaining - 1)
    else
      :ok
    end
  end
  def run(spec_path) do
    spec = spec_path |> File.read!() |> :json.decode()
    true = File.stat!("/dev/fd/" <> spec["lock_fd"]).inode == spec["lock_inode"]
    true = System.version() == "1.20.4"
    true = :erlang.system_info(:version) == ~c"17.1"
    {:module, Clbg.Main} = Code.ensure_loaded(Clbg.Main)
    path = Clbg.Main |> :code.which() |> List.to_string()
    true = Base.encode16(:crypto.hash(:sha256, File.read!(path)), case: :lower) == spec["main_beam_sha256"]
    {worker, monitor} = spawn_monitor(fn -> receive do :go -> Clbg.Main.main(["0"]) end end)
    true = :erlang.trace(worker, true, [:procs, :set_on_spawn, {:tracer, self()}]) == 1
    send(worker, :go)
    {spawned, reason} = collect(worker, monitor, [], nil, nil)
    reason_text = inspect(reason, limit: :infinity, printable_limit: :infinity)
    require!(reason != :normal and String.contains?(reason_text, "injected width3 failure"), "Wrong worker failure")
    wait_dead([worker | spawned], 100)
    report = %{schema: "elixir-rolling-injected-failure.v1", status: "PASSED", worker: inspect(worker),
      spawned: Enum.map(spawned, &inspect/1), reason: reason_text, failure_propagated: true,
      all_application_descendants_dead: true, production_source_changed: false,
      callback_twin_only: true, quantitative_benchmark: false, chart_admission: false}
    File.write!(spec["result"], :json.encode(report), [:exclusive])
  end
end
RollingFailureProbe.run(hd(System.argv()))
