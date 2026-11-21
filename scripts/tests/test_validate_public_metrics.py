"""Synthetic event validation tests, without live or private infrastructure data."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "scripts" / "validate_public_metrics.py"
spec = importlib.util.spec_from_file_location("public_validator", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
schema = json.loads((ROOT / "operations/public-metrics/event.schema.json").read_text())


def sample():
    return {
        "schema_version": 1, "id": "maintenance-2026-11-20",
        "date": "2026-11-20", "category": "scheduled-maintenance",
        "outcome": "completed",
        "systems": {"total": 11, "hypervisors": 1, "virtual_machines": 4, "containers": 6},
        "validation": {
            "guests_expected": 10, "guests_recovered": 10,
            "monitored_hosts_observed": 12, "monitored_hosts_up": 12,
            "service_warnings": 0, "service_unknown": 0, "service_critical": 0,
            "storage_integrity_errors": 0, "scheduled_log_rotation_succeeded": True,
            "administrative_closeout_verified": False
        },
        "maintenance": {
            "obsolete_kernels_removed": 5, "guest_backup_archives_observed": 10,
            "restore_tests_verified": None, "packages_upgraded": None,
            "maintenance_duration_minutes": None
        }
    }


class PublicMetricsTests(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(module.validate_event(sample(), "2026-11-20.json", schema), [])

    def test_rejects_unknown_identity_fields(self):
        data = sample()
        data["hostname"] = "example-host"
        self.assertTrue(module.validate_event(data, "2026-11-20.json", schema))

    def test_rejects_inconsistent_inventory(self):
        data = sample()
        data["systems"]["total"] = 12
        self.assertTrue(any("do not sum" in e for e in module.validate_event(data, "2026-11-20.json", schema)))

    def test_rejects_impossible_recovery(self):
        data = sample()
        data["validation"]["guests_recovered"] = 11
        self.assertTrue(any("exceeds" in e for e in module.validate_event(data, "2026-11-20.json", schema)))

    def test_rejects_wrong_filename(self):
        self.assertTrue(any("filename" in e for e in module.validate_event(sample(), "2026-11-21.json", schema)))

    def test_rejects_negative_counts(self):
        data = sample()
        data["maintenance"]["packages_upgraded"] = -1
        self.assertTrue(module.validate_event(data, "2026-11-20.json", schema))


if __name__ == "__main__":
    unittest.main()
