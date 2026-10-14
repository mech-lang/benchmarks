# Source-authored regression fixtures; native execution is pending the free lane.
# Run only under the same no-overlap policy as other native diagnostic work:
#   retained-elixir experiments/elixir/compiled-work-v1/probe-review-tests.exs
# Compile only the diagnostic module, excluding its CLI entry point. No retained
# Clbg subject source or BEAM is loaded, compiled, instrumented or invoked here.
source = File.read!(Path.join(__DIR__, "probe.exs"))
[module_source, _entry] = String.split(source, "\n[specification] = System.argv()", parts: 2)
Code.compile_string(module_source, Path.join(__DIR__, "probe.exs"))
ExUnit.start()

defmodule CompiledWorkProbeReviewTest do
  use ExUnit.Case, async: false
  @widths [1, 2, 3, 4, 6, 12, 18]
  @dna "ACGTGGTTACCGGTATTTTAATTTATAGTACGTACGTTGCA"

  defp raw_input(dna) do
    {left, right} = String.split_at(String.downcase(dna), 17)
    ">THREEISH decoy\rACGT\r>THREE\tdescription\r\n" <>
      left <> "\n;ignored comment\r" <> right <> "\r>AFTER\nTTTT\n"
  end

  defp k_fixture(dna \\ @dna) do
    events = for width <- @widths, offset <- 0..(byte_size(dna) - width + 1) do
      terminal = byte_size(dna) - width + 1
      payload = if offset <= 2 or offset == terminal do
        map = if offset == 0 do
          %{}
        else
          Enum.frequencies(for position <- 0..(offset - 1), do: binary_part(dna, position, width))
        end
        [dna, width, offset, map]
      else
        {width, offset}
      end
      {:trace, self(), :call, {Clbg.Main, :count, 4}, payload}
    end
    input = {:trace, self(), :return_from, {Clbg.Support, :input, 0}, raw_input(dna)}
    {[input | events], %{{:count, 4} => length(events)}}
  end

  defp check_k(events, counts), do: CompiledWorkDraft.check("knucleotide", events, counts)

  test "native match-spec checker emits full prefixes/terminal and scalar middle" do
    pattern = CompiledWorkDraft.count_trace_pattern()
    for offset <- [0, 1, 2, byte_size(@dna) - 3 + 1] do
      arguments = [@dna, 3, offset, %{}]
      assert {:ok, ^arguments, [], []} = :erlang.match_spec_test(arguments, pattern, :trace)
    end
    assert {:ok, {3, 3}, [], []} =
      :erlang.match_spec_test([@dna, 3, 3, %{}], pattern, :trace)
  end

  test "sequence trace preserves boundary contents and only scalar middle state" do
    pattern = CompiledWorkDraft.sequence_trace_pattern()
    for arguments <- [[[">THREE", "ACGT"], false, []], [[], true, ["ACGT"]]] do
      assert {:ok, ^arguments, [], []} = :erlang.match_spec_test(arguments, pattern, :trace)
    end
    assert {:ok, {2, true, 1}, [], []} =
      :erlang.match_spec_test([["ACGT", "TGCA"], true, ["AAAA"]], pattern, :trace)
  end

  test "seven exact schedules and complete independently selected maps pass" do
    {events, counts} = k_fixture()
    observed = check_k(events, counts)
    assert observed.selected_input_contents_bound
    assert Enum.map(observed.widths, & &1.count_invocations) ==
      Enum.map(@widths, &(byte_size(@dna) - &1 + 2))
  end

  test "missing initial full map is rejected despite unchanged aggregate count" do
    {events, counts} = k_fixture()
    events = Enum.reject(events, &match?({:trace, _, :call, {Clbg.Main, :count, 4}, [_, 1, 0, _]}, &1))
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  test "scalar offset zero cannot replace the required initial empty map" do
    {events, counts} = k_fixture()
    events = Enum.map(events, fn
      {:trace, pid, :call, mfa, [_, 1, 0, _]} -> {:trace, pid, :call, mfa, {1, 0}}
      event -> event
    end)
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  test "scalar offset two cannot replace a required early map" do
    {events, counts} = k_fixture()
    events = Enum.map(events, fn
      {:trace, pid, :call, mfa, [_, 3, 2, _]} -> {:trace, pid, :call, mfa, {3, 2}}
      event -> event
    end)
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  test "compensating per-width count changes cannot preserve qualification" do
    {events, counts} = k_fixture()
    events = Enum.map(events, fn
      {:trace, pid, :call, mfa, {3, 3}} -> {:trace, pid, :call, mfa, {4, 3}}
      event -> event
    end)
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  test "duplicated initial observation fails" do
    {events, counts} = k_fixture()
    initial = Enum.find(events, &match?({:trace, _, :call, {Clbg.Main, :count, 4}, [_, 1, 0, _]}, &1))
    assert_raise ArgumentError, fn -> check_k([initial | events], counts) end
  end

  test "internally consistent maps for another DNA fail authentic input binding" do
    {events, counts} = k_fixture(String.reverse(@dna))
    events = Enum.map(events, fn
      {:trace, pid, :return_from, {Clbg.Support, :input, 0}, _} ->
        {:trace, pid, :return_from, {Clbg.Support, :input, 0}, raw_input(@dna)}
      event -> event
    end)
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  test "complete terminal map loses no nonquery key" do
    {events, counts} = k_fixture()
    events = Enum.map(events, fn
      {:trace, pid, :call, mfa, [dna, 3, offset, map]} = event ->
        if offset + 3 > byte_size(dna) do
          key = Enum.find(Map.keys(map), &(&1 != "GGT"))
          {:trace, pid, :call, mfa, [dna, 3, offset, Map.delete(map, key)]}
        else
          event
        end
      event -> event
    end)
    assert_raise ArgumentError, fn -> check_k(events, counts) end
  end

  defp call(name, arguments), do: {:trace, self(), :call, {Clbg.Main, name, arguments}}
  defp tree(depth) do
    {left, left_events, right, right_events} = if depth == 0 do
      {nil, [], nil, []}
    else
      {left, le} = tree(depth - 1)
      {right, re} = tree(depth - 1)
      {left, le, right, re}
    end
    node = {make_ref(), left, right}
    {node, [call(:tree, [depth])] ++ left_events ++ right_events ++
      [{:trace, self(), :return_from, {Clbg.Main, :tree, 1}, node}]}
  end
  defp checks({_, nil, nil} = node), do: [call(:check, [node])]
  defp checks({_, left, right} = node), do: [call(:check, [node])] ++ checks(left) ++ checks(right)
  defp repeated(depth, iterations) do
    nodes = Bitwise.bsl(1, depth + 1) - 1
    Enum.flat_map(iterations..0//-1, fn remaining ->
      entry = call(:repeat, [remaining, depth, (iterations - remaining) * nodes])
      if remaining == 0 do
        [entry]
      else
        {node, events} = tree(depth)
        [entry | events] ++ checks(node)
      end
    end)
  end
  defp tree_fixture() do
    {stretch, stretch_events} = tree(7)
    {long, long_events} = tree(6)
    events = stretch_events ++ checks(stretch) ++ long_events ++
      [call(:depths, [4, 6, long, []])] ++ repeated(4, 64) ++
      [call(:depths, [6, 6, long, []])] ++ repeated(6, 16) ++
      [call(:depths, [8, 6, long, []])] ++ checks(long)
    {events, %{{:tree, 1} => 4398, {:check, 1} => 4398}}
  end
  defp check_trees(events, counts), do: CompiledWorkDraft.check("binarytrees", events, counts)
  defp change_first(events, predicate, change) do
    index = Enum.find_index(events, predicate)
    List.update_at(events, index, change)
  end

  test "actual nested graphs pass while normal GC remains explicitly unproved" do
    {events, counts} = tree_fixture()
    observed = check_trees(events, counts)
    assert observed.disjoint_left_right_descendants
    assert observed.actual_returned_child_graphs_checked == 4398
    refute observed.normal_gc_lifetime_proven
  end

  test "shared left/right descendants fail despite unique returned root IDs" do
    {events, counts} = tree_fixture()
    events = change_first(events,
      &match?({:trace, _, :return_from, {Clbg.Main, :tree, 1}, {_, {_, nil, nil}, {_, nil, nil}}}, &1),
      fn {:trace, pid, kind, mfa, {identity, left, _right}} -> { :trace, pid, kind, mfa, {identity, left, left}} end)
    assert_raise ArgumentError, fn -> check_trees(events, counts) end
  end

  test "constructor requested depth binds actual returned shape" do
    {events, counts} = tree_fixture()
    events = List.replace_at(events, 0, call(:tree, [6]))
    assert_raise ArgumentError, fn -> check_trees(events, counts) end
  end

  test "check cannot receive another shape with the same root identity" do
    {events, counts} = tree_fixture()
    events = change_first(events,
      &match?({:trace, _, :call, {Clbg.Main, :check, [{_, {_, _, _}, _}]}}, &1),
      fn {:trace, pid, kind, {module, function, [{identity, _, _}]}} ->
        {:trace, pid, kind, {module, function, [{identity, nil, nil}]}}
      end)
    assert_raise ArgumentError, fn -> check_trees(events, counts) end
  end

  test "long root graph cannot change while retaining its root identity" do
    {events, counts} = tree_fixture()
    events = change_first(events,
      &match?({:trace, _, :call, {Clbg.Main, :depths, [6, 6, _, _]}}, &1),
      fn {:trace, pid, kind, {module, function, [depth, maximum, {identity, left, _}, out]}} ->
        {:trace, pid, kind, {module, function, [depth, maximum, {identity, left, left}, out]}}
      end)
    assert_raise ArgumentError, fn -> check_trees(events, counts) end
  end
end
