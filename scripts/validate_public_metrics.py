#!/usr/bin/env python3
"""Validate allowlisted, sanitized public maintenance-event JSON files.

This validator checks shape, logical consistency, and a small set of privacy
indicators. It is not a substitute for human review of reconnaissance risk.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "operations" / "public-metrics"
DATE_FILENAME = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
SENSITIVE_KEY = re.compile(
    r"(?:hostname|guest_id|vmid|ip_address|endpoint|url|port|username|token|"
    r"secret|password|mac_address|cidr|subnet|device_id|storage_path)",
    flags=re.IGNORECASE,
)


def validate_event(event: dict, filename: str, schema: dict) -> list[str]:
    """Return all validation errors without printing event values."""
    errors = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(event), key=lambda error: str(error.path)):
        location = ".".join(str(part) for part in err.path) or "(root)"
        errors.append(f"{filename}: invalid field at {location}: {err.validator}")

    if not isinstance(event, dict):
        return errors

    def check_keys(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                if SENSITIVE_KEY.search(key):
                    errors.append(f"{filename}: forbidden field name at {path}{key}")
                check_keys(child, f"{path}{key}.")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_keys(child, f"{path}{index}.")

    check_keys(event)

    if not DATE_FILENAME.fullmatch(filename):
        errors.append(f"{filename}: event filename must be YYYY-MM-DD.json")
    if event.get("date") and filename != f"{event['date']}.json":
        errors.append(f"{filename}: filename and event date differ")
    if event.get("id") and event.get("date") and event["id"] != f"maintenance-{event['date']}":
        errors.append(f"{filename}: event id and date differ")

    systems = event.get("systems")
    if isinstance(systems, dict):
        keys = ("hypervisors", "virtual_machines", "containers", "total")
        if all(type(systems.get(k)) is int for k in keys):
            if sum(systems[k] for k in keys[:-1]) != systems["total"]:
                errors.append(f"{filename}: system type counts do not sum to total")

    validation = event.get("validation")
    if isinstance(validation, dict):
        for counted, expected in (
            ("guests_recovered", "guests_expected"),
            ("monitored_hosts_up", "monitored_hosts_observed"),
        ):
            if type(validation.get(counted)) is int and type(validation.get(expected)) is int:
                if validation[counted] > validation[expected]:
                    errors.append(f"{filename}: {counted} exceeds {expected}")
    return errors


def main() -> int:
    schema_file = DATA_DIR / "event.schema.json"
    if not schema_file.is_file():
        print("Missing public metrics schema", file=sys.stderr)
        return 1

    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (ValueError, OSError, Exception) as exc:
        print(f"Invalid schema: {type(exc).__name__}", file=sys.stderr)
        return 1

    files = sorted((DATA_DIR / "events").glob("*.json"))
    if not files:
        print("No public metrics events found", file=sys.stderr)
        return 1

    issues = []
    for path in files:
        try:
            event = json.loads(path.read_text(encoding="utf-8"))
            issues.extend(validate_event(event, path.name, schema))
        except (OSError, ValueError) as exc:
            issues.append(f"{path.name}: unreadable or malformed JSON ({type(exc).__name__})")

    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print(f"Public metrics validation failed ({len(issues)} findings)", file=sys.stderr)
        return 1
    print(f"Validated {len(files)} sanitized public maintenance event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
