"""Rebuild and reproduce the reported Mech encoder object from source."""
from argparse import ArgumentParser
from pathlib import Path
from runpy import run_path
from subprocess import run, check_output

from run_study import BLOCK_LAYOUT, REGISTER_WEIGHTS, bind_recipe, drop_matcher, read, sha, write

HERE = Path(__file__).resolve().parent
PARENT_PACKET = HERE.parent / "mechdeflate-masked-fields-v1"


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("--mech-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--target-dir", type=Path)
    parser.add_argument("--checked", action="store_true")
    args = parser.parse_args()
    root, out = args.mech_root.resolve(), args.output.resolve()
    roles = read(HERE / "roles.json")
    role = roles[args.role]
    commit = check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert commit == role["source_commit"]
    recipe, control_flags = bind_recipe(PARENT_PACKET)
    source = root / recipe["codec_source"]
    assert sha(source) == recipe["codec_source_sha256"]
    out.mkdir(parents=True)
    prior = run_path(str(PARENT_PACKET / "reproduce.py"))
    compiler = (args.compiler.resolve() if args.compiler else
                prior["build_compiler"](root, out, args.target_dir or out / "target"))
    flags = (drop_matcher(control_flags) if role.get("profiles") else control_flags) | role.get("options", {})
    for key in (REGISTER_WEIGHTS, BLOCK_LAYOUT):
        for symbol, relative in role.get("profiles", {}).get(key, {}).items():
            profile = HERE / relative
            assert sha(profile) == profile.stem
            flags[key] = ";".join((flags[key], f"{symbol}@{profile}"))
    if args.checked:
        flags["MECH_COMPACT_PAIR_REGISTER_SPILLS"] = "checked"
    frontend = out / "frontend"
    command = [str(compiler), str(source), str(frontend), "compact"]
    with (out / "compile.log").open("w") as log:
        run(command, cwd=root, env=prior["clean_environment"]() | flags, stdout=log, stderr=log, check=True)
    actual = {name: sha(frontend / name) for name in role["artifacts"]}
    assert actual == role["artifacts"], (actual, role["artifacts"])
    write(out / "reproduction.json", {"role": args.role, "source_commit": commit, "compiler_sha256": sha(compiler),
                                     "checked": args.checked, "command": command, "artifacts": actual})
    print(args.role, "object, metadata and canonical bytecode match exactly")


if __name__ == "__main__":
    main()
