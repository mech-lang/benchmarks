defmodule Clbg.Main do
  import Bitwise
  alias Clbg.Support, as: S
  @queries ["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"]
  @widths [1, 2, 3, 4, 6, 12, 18]

  defp digit(code) when code in [?A, ?a], do: 0
  defp digit(code) when code in [?C, ?c], do: 1
  defp digit(code) when code in [?G, ?g], do: 2
  defp digit(code) when code in [?T, ?t], do: 3
  defp digit(_code), do: raise(ArgumentError, "Unsupported nucleotide")

  defp header_name(line) do
    line |> binary_part(1, byte_size(line) - 1) |> :binary.split([" ", "\t"]) |> hd()
  end

  defp sequence([], _selected, out), do: out |> Enum.reverse() |> IO.iodata_to_binary()
  defp sequence([<<">", _rest::binary>> = line | lines], selected, out) do
    if selected, do: sequence([], false, out), else: sequence(lines, header_name(line) == "THREE", out)
  end
  defp sequence([line | lines], selected, out) do
    if selected and line != "" and :binary.at(line, 0) != ?; do
      encoded = for <<code <- line>>, into: <<>>, do: <<digit(code)>>
      sequence(lines, selected, [encoded | out])
    else
      sequence(lines, selected, out)
    end
  end

  defp prefix(binary, 0, key), do: {binary, key}
  defp prefix(<<>>, _remaining, _key), do: :short
  defp prefix(<<base, rest::binary>>, remaining, key) do
    prefix(rest, remaining - 1, (key <<< 2) ||| base)
  end

  defp count(<<>>, _mask, _key, counts), do: counts
  defp count(<<base, rest::binary>>, mask, key, counts) do
    next = ((key <<< 2) ||| base) &&& mask
    updated = Map.update(counts, next, 1, fn value -> value + 1 end)
    count(rest, mask, next, updated)
  end

  defp histogram(dna, width) do
    case prefix(dna, width - 1, 0) do
      :short -> %{}
      {rest, key} -> count(rest, (1 <<< (2 * width)) - 1, key, %{})
    end
  end

  defp pack(query) do
    Enum.reduce(:binary.bin_to_list(query), 0, fn code, key -> (key <<< 2) ||| digit(code) end)
  end

  defp decode(key, width) do
    for shift <- (width - 1)..0//-1, into: <<>> do
      <<:binary.at("ACGT", (key >>> (2 * shift)) &&& 3)>>
    end
  end

  defp result(dna, width) do
    counts = histogram(dna, width)
    if width <= 2 do
      ordered = Enum.sort(counts, fn {ka, va}, {kb, vb} -> va > vb or (va == vb and ka < kb) end)
      total = max(0, byte_size(dna) - width + 1)
      [Enum.map(ordered, fn {key, amount} -> [decode(key, width), " ", S.fixed(100.0 * amount / total, 3), "\n"] end), "\n"]
    else
      query = Enum.find(@queries, fn query -> byte_size(query) == width end)
      "#{Map.get(counts, pack(query), 0)}\t#{query}\n"
    end
  end

  def main(_arguments) do
    dna = S.input() |> S.lines() |> sequence(false, [])
    output =
      @widths
      |> Task.async_stream(fn width -> result(dna, width) end,
        max_concurrency: 7, ordered: true, timeout: :infinity)
      |> Enum.map(fn {:ok, result} -> result end)
    S.write(output)
  end
end
