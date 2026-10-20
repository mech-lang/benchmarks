# Appended after the exact retained SourceCountReader module bytes. This replaces
# only the historical executable entrypoint, whose mutex inode is host-specific.
# Qualified parse/semantic/formatter/tagged/inspect_source functions are unchanged.
defmodule RetainedRollingReaderHost do
  def main([plan_path, output, common_fd]) do
    plan = plan_path |> File.read!() |> JSON.decode!()
    SourceCountReader.ensure(plan["schema"] == "elixir-source-reader-plan-v1", "Wrong retained reader plan schema")
    SourceCountReader.ensure(System.version() == "1.20.4", "Wrong exact Elixir")
    SourceCountReader.ensure(:erlang.system_info(:otp_release) == ~c"29", "Wrong exact OTP")
    SourceCountReader.ensure(:erlang.system_info(:version) == ~c"17.1", "Wrong exact ERTS")
    SourceCountReader.ensure(:erlang.system_info(:emu_flavor) == :jit, "Wrong retained JIT")
    SourceCountReader.ensure(:erlang.system_info(:schedulers_online) == 8, "Wrong retained schedulers")
    %{inode: inode} = File.stat!("/dev/fd/" <> common_fd)
    SourceCountReader.ensure(inode == plan["common_mutex_inode"], "Current common mutex not inherited")
    SourceCountReader.ensure(:code.is_loaded(Clbg.Main) == false and :code.is_loaded(Clbg.Support) == false,
      "Application modules must not be loaded")
    File.mkdir!(output)
    SourceCountReader.json(Path.join(output, "started.json"), %{
      "elixir_version" => System.version(), "otp_release" => List.to_string(:erlang.system_info(:otp_release)),
      "system_version" => List.to_string(:erlang.system_info(:system_version)), "common_mutex_inode" => inode,
      "source_evaluations" => 0, "subject_recompilations" => 0, "subject_main_invocations" => 0,
      "retained_reader_functions_unchanged" => true, "historical_entrypoint_called" => false})
    items = Enum.map(plan["inputs"], &SourceCountReader.inspect_source(&1, output))
    SourceCountReader.ensure(:code.is_loaded(Clbg.Main) == false and :code.is_loaded(Clbg.Support) == false,
      "Reading application data loaded a module")
    SourceCountReader.json(Path.join(output, "report.json"), %{
      "schema" => "elixir-native-source-reader-v1", "status" => "read-awaiting-canonical-owner-review", "items" => items,
      "application_files" => Enum.count(plan["inputs"], &(&1["kind"] == "application")),
      "fixture_files" => Enum.count(plan["inputs"], &(&1["kind"] == "fixture")),
      "formatter" => %{"api" => "Code.format_string!/2", "line_length" => 98, "elixir" => System.version()},
      "source_evaluations" => 0, "subject_recompilations" => 0, "subject_main_invocations" => 0,
      "canonical_loc_qualified" => false, "formatted_loc_qualified" => false, "chart_admission" => false})
  end
end
RetainedRollingReaderHost.main(System.argv())
