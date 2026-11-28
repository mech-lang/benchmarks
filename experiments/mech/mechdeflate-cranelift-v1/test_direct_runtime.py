import hashlib
import io
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from verify_direct_runtime import extract_archive, verify_direct_runtime


PACKET = Path(__file__).resolve().parent
RECORD = (PACKET / "stabilization/route-memory/3a66a014c853e082ad907ed4db1673c9dadf0c69"
          / "F-m1-direct-20261127T162006Z")


class DirectRuntimeVerification(unittest.TestCase):
    def test_replay_a_relocated_record_without_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            record = scratch / "relocated-record"
            shutil.copytree(RECORD, record)
            open_path = Path.open
            checkout = PACKET.parents[2]

            def open_relocated(path, *args, **kwargs):
                if path.is_relative_to("/Users") and not path.is_relative_to(checkout):
                    raise AssertionError(f"Replay opened an original machine path: {path}")
                return open_path(path, *args, **kwargs)

            process = AssertionError("Offline replay launched a process.")
            with (patch.object(Path, "open", open_relocated),
                  patch("subprocess.Popen", side_effect=process),
                  patch("os.system", side_effect=process)):
                result = verify_direct_runtime(record, scratch / "replay")

            self.assertEqual(result["case_rows"], 1116)
            self.assertEqual(result["individual_leg_exceptions"], 3)
            self.assertEqual((result["fixture_calls"], result["silesia_calls"]), (5895936, 2592))

    def test_rejects_missing_or_changed_observation_and_actor_members(self):
        originals = {
            "session/fixture/observations.json.gz": b"original observation",
            "actor/mech-worker": b"original actor",
        }
        inventory = {"directories": {}, "files": {
            name: {"mode": "0644", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in originals.items()
        }}
        for member in originals:
            for action in ("missing", "changed"):
                with self.subTest(member=member, action=action), tempfile.TemporaryDirectory() as temporary:
                    scratch = Path(temporary)
                    archive = scratch / "record.tar.gz"
                    with tarfile.open(archive, "w:gz") as stream:
                        for name, data in originals.items():
                            if name == member:
                                if action == "missing":
                                    continue
                                data = b"!" + data[1:]
                            entry = tarfile.TarInfo(name)
                            entry.size = len(data)
                            stream.addfile(entry, io.BytesIO(data))
                    with self.assertRaisesRegex(ValueError, member):
                        extract_archive(archive, inventory, scratch / "extracted")


if __name__ == "__main__":
    unittest.main()
