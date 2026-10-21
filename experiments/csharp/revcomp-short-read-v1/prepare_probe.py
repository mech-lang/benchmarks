#!/usr/bin/env python3
"""Prepare exact private-helper projections without launching .NET or a benchmark."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = ROOT / 'archive/comparisons/remaining-languages-comparison/20261011/sources/csharp/revcomp-csharpcore-9-arm64-faithful.cs'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(check):
    rows = []
    for label, source in (('parent', PARENT), ('fixed', HERE / 'source/Program.cs')):
        raw = source.read_bytes()
        marker = b'public static class Program\n'
        assert raw.count(marker) == 1
        projected = raw.replace(marker, b'public static partial class Program\n', 1)
        directory = HERE / 'diagnostic-v1' / label
        project = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings><Nullable>disable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks><Optimize>true</Optimize>
    <InvariantGlobalization>true</InvariantGlobalization>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <UseSharedCompilation>false</UseSharedCompilation>
    <StartupObject>ReadBlockDiagnostic</StartupObject>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="Program.cs" />
    <Compile Include="../../ReadBlockDiagnostic.cs" />
  </ItemGroup>
</Project>
'''.encode()
        for filename, content in (('Program.cs', projected), ('app.csproj', project)):
            path = directory / filename
            if check:
                assert path.read_bytes() == content
            else:
                directory.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(content)
        rows.append(dict(label=label, original_source=str(source.relative_to(ROOT)),
            original_sha256=sha(raw), projected_source=str((directory / 'Program.cs').relative_to(ROOT)),
            projected_sha256=sha(projected), project_sha256=sha(project),
            transformation='Only add partial to Program so a separate diagnostic can call the exact private helper.',
            native_execution_qualified=False))
    return dict(schema='csharp-short-read-helper-preparation.v1', projections=rows,
        generator_sha256=sha(Path(__file__).read_bytes()),
        diagnostic_sha256=sha((HERE / 'ReadBlockDiagnostic.cs').read_bytes()),
        planned_check_pairs=18, execution_modes=['jit', 'aot'],
        expected_capture_policy='Retain the parent failure and all fixed-form results; no assertion here claims either was observed.',
        native_processes_started=0, benchmark_main_executed=False,
        benchmark_samples=0, source_work_qualified=False, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build(args.check)
    path = HERE / 'diagnostic-v1/plan.json'
    if args.check:
        assert json.loads(path.read_bytes()) == result
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'prepared',
                          source_projections=2, native_processes_started=0)))
