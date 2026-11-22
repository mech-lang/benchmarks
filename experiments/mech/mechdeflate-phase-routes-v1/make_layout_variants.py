"""Try measured edge and aggregate-visit layouts for the unchanged allocated matcher."""
from argparse import ArgumentParser
from pathlib import Path
from runpy import run_path
from run_study import BLOCK_LAYOUT, add_profile, bind_recipe, emit, read, write

parser = ArgumentParser(__doc__)
for name in ("lab", "packet", "mech-root", "compiler", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
raw = args.output / "shared-bases-linear-4096-unlaid"
history = args.lab / "derive-coalesced-layout.py"
original = history.read_text()
census = raw / "counts-word-reuse-v1-475"
counts = read(census / "counts.json")
shape = read(census / "native-shape.json")
driver = run_path(str(args.lab / "matcher-pair-combination-study/native-tools.py"))["driver"]
recipe, _ = bind_recipe(args.packet)
template = args.lab / "fp-spill-keep-pairs-study/census/keep-pairs2"
flags = read(raw / "receipt.json")["flags"]
print("Only final block order varies in these two roles.", flush=True)
substitutions = {
    "shared-bases-edges-linear-4096": ("potential + .35 * weighted[src, dst] + .001",
                                     "weighted[src, dst] + .001"),
    "shared-bases-visits-linear-4096": ("peak = max(counts)",
                                      "peak = max(b['visits'] for x in trace['cases'].values() for b in x['blocks'])"),
}
for name, (old, new) in substitutions.items():
    assert original.count(old) == 1
    code = original.replace(old, new)
    env = {}
    exec(compile(code, str(history), "exec"), env)
    profile, proof = env["derive"](shape, counts)
    profile_path = raw / (name + "-layout.json")
    write(profile_path, profile)
    final = args.output / name
    emit(final, add_profile(flags, BLOCK_LAYOUT, profile_path), args, recipe, driver, template)
    write(final / "layout-proof.json", proof)
    print("PREPARED", name, flush=True)
