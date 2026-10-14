# Unscored source inspection. Parsed application ASTs are never evaluated.
defmodule SourceCountReader do
  def ensure(true, _message), do: :ok
  def ensure(false, message), do: raise(ArgumentError, message)

  def digest(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)

  # Preserve arbitrary literal bytes, atoms, tuples, lists, and metadata without
  # guessing that every tuple is an AST node or every binary is UTF-8 text.
  def tagged(value) when is_atom(value), do: ["atom", Atom.to_string(value)]
  def tagged(value) when is_binary(value), do: ["binary", Base.encode64(value)]
  def tagged(value) when is_integer(value), do: ["integer", Integer.to_string(value)]
  def tagged(value) when is_float(value), do: ["float", Float.to_string(value)]
  def tagged(value) when is_tuple(value), do: ["tuple", value |> Tuple.to_list() |> Enum.map(&tagged/1)]
  def tagged(value) when is_list(value), do: ["list", Enum.map(value, &tagged/1)]
  def tagged(value) when is_map(value) do
    ["map", value |> Enum.sort() |> Enum.map(fn {key, item} -> [tagged(key), tagged(item)] end)]
  end

  def write(path, bytes), do: File.write!(path, bytes, [:exclusive])
  def json(path, value), do: write(path, JSON.encode!(value) <> "\n")

  def parse(text, path) do
    Code.string_to_quoted_with_comments(text,
      file: path, columns: true, token_metadata: true, unescape: false,
      literal_encoder: fn literal, metadata -> {:ok, {:__block__, metadata, [literal]}} end)
  end

  def semantic(text, path) do
    text
    |> Code.string_to_quoted!(file: path)
    |> Macro.prewalk(fn
      {form, metadata, arguments} when is_list(metadata) -> {form, [], arguments}
      value -> value
    end)
  end

  def inspect_source(item, output) do
    directory = Path.join(output, item["id"])
    File.mkdir!(directory)
    text = if item["kind"] == "application", do: File.read!(item["path"]), else: item["text"]
    ensure(digest(text) == item["sha256"], "Source changed: " <> item["id"])
    ensure(String.valid?(text), "Source must be valid UTF-8")
    write(Path.join(directory, "source.exs"), text)
    case parse(text, item["path"]) do
      {:ok, ast, comments} ->
        ensure(item["expected_parse"] == "ok", "Invalid-source fixture unexpectedly parsed")
        write(Path.join(directory, "ast.etf"), :erlang.term_to_binary({ast, comments}))
        json(Path.join(directory, "ast.json"), %{"ast" => tagged(ast), "comments" => tagged(comments)})
        formatted = Code.format_string!(text, file: item["path"], line_length: 98) |> IO.iodata_to_binary()
        formatted = formatted <> "\n"
        ensure(semantic(text, item["path"]) == semantic(formatted, item["path"]),
          "Formatter changed the metadata-stripped AST")
        {:ok, formatted_ast, formatted_comments} = parse(formatted, item["path"])
        write(Path.join(directory, "formatted.exs"), formatted)
        json(Path.join(directory, "formatted-ast.json"),
          %{"ast" => tagged(formatted_ast), "comments" => tagged(formatted_comments)})
        %{"id" => item["id"], "status" => "parsed-and-formatted", "source_sha256" => digest(text),
          "formatted_sha256" => digest(formatted), "semantic_ast_preserved" => true,
          "canonical_loc" => nil, "formatted_loc" => nil}
      {:error, error} ->
        json(Path.join(directory, "parse-error.json"), %{"error" => tagged(error)})
        ensure(item["expected_parse"] == "error", "Application or valid fixture failed to parse")
        %{"id" => item["id"], "status" => "expected-parse-rejection", "source_sha256" => digest(text),
          "canonical_loc" => nil, "formatted_loc" => nil}
    end
  end

  def main([plan_path, output, common_fd]) do
    plan = plan_path |> File.read!() |> JSON.decode!()
    ensure(plan["schema"] == "elixir-source-reader-plan-v1", "Unexpected source-reader plan")
    ensure(System.version() == "1.20.4", "Unexpected Elixir runtime")
    ensure(:erlang.system_info(:emu_flavor) == :jit, "Unexpected BEAM runtime")
    ensure(:erlang.system_info(:schedulers_online) == 8, "Unexpected scheduler configuration")
    %{inode: inode} = File.stat!("/dev/fd/" <> common_fd)
    ensure(inode == 79859134, "Common mutex was not inherited")
    ensure(:code.is_loaded(Clbg.Main) == false and :code.is_loaded(Clbg.Support) == false,
      "Application modules must not be loaded by a source reader")
    File.mkdir!(output)
    json(Path.join(output, "started.json"), %{"elixir_version" => System.version(),
      "otp_release" => :erlang.system_info(:otp_release) |> List.to_string(),
      "system_version" => :erlang.system_info(:system_version) |> List.to_string(),
      "common_mutex_inode" => inode, "source_evaluations" => 0})
    items = Enum.map(plan["inputs"], &inspect_source(&1, output))
    ensure(:code.is_loaded(Clbg.Main) == false and :code.is_loaded(Clbg.Support) == false,
      "Source reading loaded an application module")
    json(Path.join(output, "report.json"), %{"schema" => "elixir-native-source-reader-v1",
      "status" => "read-awaiting-canonical-owner-review", "items" => items,
      "application_files" => Enum.count(plan["inputs"], &(&1["kind"] == "application")),
      "fixture_files" => Enum.count(plan["inputs"], &(&1["kind"] == "fixture")),
      "formatter" => %{"api" => "Code.format_string!/2", "line_length" => 98, "elixir" => System.version()},
      "source_evaluations" => 0, "subject_recompilations" => 0, "subject_main_invocations" => 0,
      "canonical_loc_qualified" => false, "formatted_loc_qualified" => false, "chart_admission" => false})
  end
end

SourceCountReader.main(System.argv())
