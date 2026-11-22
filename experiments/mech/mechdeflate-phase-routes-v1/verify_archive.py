"""Verify the archive's file hashes and the recipe profiles and shipped actors."""
from hashlib import file_digest
from pathlib import Path
import tarfile

from run_study import read, sha


def main():
    packet = Path(__file__).resolve().parent
    archive = packet / "raw-evidence.tar.gz"
    manifest = read(packet / "raw-manifest.json")
    assert sha(archive) == manifest["archive_sha256"]
    remaining = manifest["files"].copy()
    with tarfile.open(archive, mode="r|gz") as stream:
        for member in stream:
            info = remaining.pop(member.name)
            assert member.isfile() and member.size == info["bytes"], member.name
            with stream.extractfile(member) as content:
                assert file_digest(content, "sha256").hexdigest() == info["sha256"], member.name
    assert not remaining
    previous = read(packet.parent / "mechdeflate-masked-fields-v1" / "raw-manifest.json")
    oracle = previous["files"]["pinned-peers/libdeflate-output-oracle.json"]
    assert sha(packet / "libdeflate-output-oracle.json") == oracle["sha256"]
    for name, role in read(packet / "roles.json").items():
        for profiles in role["profiles"].values():
            for relative in profiles.values():
                path = packet / relative
                assert sha(path) == path.stem
        actor = packet / "actors" / name
        if actor.is_dir():
            assert sha(actor / "mech-worker") == role["worker_sha256"]
            assert sha(actor / "metadata.json") == role["artifacts"]["metadata.json"]
    print(f"Verified {len(manifest['files'])} archived files, all recipe profiles and the shipped actors.")


if __name__ == "__main__":
    main()
