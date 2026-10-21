#!/usr/bin/env python3
"""Restore exact retained compiler distributions without running installers."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url, output):
    req = urllib.request.Request(url, headers={"User-Agent": "Mech benchmark retained-toolchain restore"})
    with urllib.request.urlopen(req, timeout=50) as response, output.open("xb") as stream:
        assert response.status == 200
        for block in iter(lambda: response.read(1024 * 1024), b""):
            stream.write(block)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", choices=("typescript", "crystal"))
    args = parser.parse_args()
    target = HERE / ".build" / args.language
    target.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": "exact-audit-toolchain-restoration.v1", "language": args.language,
               "started_at": datetime.now(timezone.utc).isoformat(), "install_scripts_executed": False,
               "native_processes_started": 0, "packages": []}
    try:
        if args.language == "typescript":
            original = ROOT / "experiments/typescript/toolchain-v1/retained-packages-v1.json"
            receipt["retained_receipt"] = {"path": str(original.relative_to(ROOT)), "sha256": digest(original)}
            for index, package in enumerate(json.loads(original.read_bytes())["packages"]):
                archive = target / f"package-{index}.tgz"
                dist = package["registry_manifest"]["dist"]
                download(dist["tarball"], archive)
                assert digest(archive) == package["archive_sha256"]
                assert archive.stat().st_size == package["archive_bytes"]
                integrity = "sha512-" + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
                assert integrity == dist["integrity"]
                unpacked = target / f"unpack-{index}"
                unpacked.mkdir()
                with tarfile.open(archive) as source:
                    source.extractall(unpacked, filter="data")
                top = list(unpacked.iterdir())
                assert len(top) == 1 and top[0].is_dir()
                installed = target / "node_modules" / package["name"]
                installed.parent.mkdir(parents=True, exist_ok=True)
                top[0].rename(installed)
                actual = {str(p.relative_to(installed)): {"sha256": digest(p), "bytes": p.stat().st_size}
                          for p in installed.rglob("*") if p.is_file()}
                assert actual == package["files"], package["name"] + " file closure differs"
                receipt["packages"].append({"name": package["name"], "version": package["version"],
                    "url": dist["tarball"], "archive_sha256": digest(archive), "integrity_verified": True,
                    "installation": str(installed), "retained_files_exact": True, "files": actual})
        else:
            release = ROOT / "archive/languages/crystal/20261012/research/crystal-release.json"
            receipt["retained_release"] = {"path": str(release.relative_to(ROOT)), "sha256": digest(release)}
            asset = next(a for a in json.loads(release.read_bytes())["assets"]
                         if a["name"] == "crystal-1.21.1-1-darwin-universal.tar.gz")
            archive = target / asset["name"]
            download(asset["browser_download_url"], archive)
            assert digest(archive) == asset["digest"].removeprefix("sha256:")
            assert archive.stat().st_size == asset["size"]
            installed = target / "distribution"
            installed.mkdir()
            with tarfile.open(archive) as source:
                source.extractall(installed, filter="data")
            files = {}
            for path in sorted(installed.rglob("*")):
                relative = str(path.relative_to(installed))
                if path.is_symlink():
                    assert path.resolve().is_relative_to(installed.resolve())
                    files[relative] = {"symlink": str(path.readlink())}
                elif path.is_file():
                    files[relative] = {"sha256": digest(path), "bytes": path.stat().st_size}
            receipt["packages"].append({"name": asset["name"], "url": asset["browser_download_url"],
                "archive_sha256": digest(archive), "release_digest_verified": True,
                "installation": str(installed), "files": files})
        receipt["status"] = "restored-no-native-execution"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = repr(error)
        raise
    finally:
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        (HERE / f"{args.language}-restore.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({k: v for k, v in receipt.items() if k != "packages"}))


if __name__ == "__main__":
    main()
