"""Unit tests use synthetic APT histories and do not connect to live infrastructure."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collect_apt_maintenance as module

SAMPLE = """Start-Date: 2026-11-20  19:15:49
Commandline: apt full-upgrade
Install: first:amd64 (1, automatic), second:amd64 (1, automatic)
Upgrade: apt:amd64 (3, 4), pve-manager:amd64 (9, 10)
End-Date: 2026-11-20  19:17:22

Start-Date: 2026-11-20  19:40:06
Commandline: apt autoremove
Remove: old-one:amd64 (1), old-two:amd64 (1)
End-Date: 2026-11-20  19:40:13

Start-Date: 2026-11-21  00:01:00
Upgrade: next-day:amd64 (1, 2)
End-Date: 2026-11-21  00:01:20
"""


class AptParserTests(unittest.TestCase):
    def test_single_date(self):
        report = module.parse_history(SAMPLE, "2026-11-20")
        self.assertEqual(report["transactions"], 2)
        self.assertEqual(report["package_operations"]["upgrade"], 2)
        self.assertEqual(report["package_operations"]["install"], 2)
        self.assertEqual(report["package_operations"]["remove"], 2)
        self.assertEqual(report["apt_duration_seconds"], 100)

    def test_cross_midnight_range(self):
        report = module.parse_history(SAMPLE, "2026-11-20", "2026-11-21")
        self.assertEqual(report["transactions"], 3)
        self.assertEqual(report["package_operations"]["upgrade"], 3)
        self.assertEqual(report["apt_duration_seconds"], 120)

    def test_incomplete_duration_is_unknown(self):
        report = module.parse_history(
            "Start-Date: 2026-11-20  23:00:00\nUpgrade: pkg:amd64 (1, 2)",
            "2026-11-20")
        self.assertEqual(report["incomplete_transactions"], 1)
        self.assertIsNone(report["apt_duration_seconds"])

    def test_remote_parser_agrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "history.log").write_text(SAMPLE)
            code = module.REMOTE_CODE.replace(
                'Path("/var/log/apt")', f"Path({tmp!r})")
            result = subprocess.run(
                [sys.executable, "-c", code, "2026-11-20", "2026-11-21"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            remote = json.loads(result.stdout)
            self.assertEqual(remote["package_operations"]["remove"], 2)
            self.assertEqual(remote["apt_duration_seconds"], 120)

    def test_vm_status_column(self):
        output = "VMID NAME STATUS MEM(MiB) BOOTDISK(GiB) PID\n103 sample running 4096 32.00 1234\n"
        with patch.object(module, "run", return_value=subprocess.CompletedProcess(
                ["qm", "list"], 0, stdout=output)):
            self.assertEqual(module.inventory(["qm", "list"], "vm"),
                             [("103", "running")])

    def test_lxc_status_column(self):
        output = "VMID Status Lock Name\n100 running sample\n"
        with patch.object(module, "run", return_value=subprocess.CompletedProcess(
                ["pct", "list"], 0, stdout=output)):
            self.assertEqual(module.inventory(["pct", "list"], "lxc"),
                             [("100", "running")])


if __name__ == "__main__":
    unittest.main()
