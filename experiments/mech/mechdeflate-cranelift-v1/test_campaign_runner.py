import tempfile
import unittest
from pathlib import Path

from compare_rebuilt import require_pair, write_new
from verify import inventory, verify_inventory, verify_session


class CampaignRunnerTests(unittest.TestCase):
    def test_identical_roles_are_allowed_only_for_calibration(self):
        binding = {"label": "control", "build_directory": "/build",
                   "source_commit": "reviewed", "compiler_sha256": "pinned",
                   "81": {"sha256": "worker"}, "silesia": {"sha256": "encoder"}}
        alias = {**binding, "label": "candidate"}
        require_pair(binding, alias, calibration=True)
        with self.assertRaises(ValueError):
            require_pair(binding, alias, calibration=False)
        with self.assertRaises(ValueError):
            require_pair(binding, {**alias, "compiler_sha256": "changed"}, calibration=True)
        require_pair(binding, {**alias, "source_commit": "candidate", "build_directory": "/new"},
                     calibration=False)

    def test_seals_reject_missing_changed_or_additional_raw_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            raw = folder / "raw.json"
            raw.write_bytes(b"expected")
            sealed = inventory(folder)
            verify_inventory(folder, sealed)
            raw.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)
            raw.unlink()
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)
            raw.write_bytes(b"expected")
            (folder / "added.json").touch()
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)

    def test_session_must_be_complete_and_at_the_same_inputs_to_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            with self.assertRaises(ValueError):
                verify_session(folder, "manifest", "qualify", "calibration")
            info = {"manifest_sha256": "manifest", "calibration_sha256": "calibration",
                    "stage": "qualify", "session": folder.name,
                    "start_utc": "00", "end_utc": "01", "raw_files": {}}
            path = folder / "record.json"
            write_new(path, info)
            self.assertEqual(verify_session(folder, "manifest", "qualify", "calibration"), info)
            with self.assertRaises(ValueError):
                verify_session(folder, "manifest", "qualify", "changed")
            with self.assertRaises(FileExistsError):
                write_new(path, info)
