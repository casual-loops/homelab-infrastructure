#!/usr/bin/env python3
"""Read-only APT transaction collector for a Proxmox host and its guests.

Private results contain guest IDs. Never commit generated reports to a public repo.
Uses only Python standard library, pct, qm, and guest-agent exec.
"""
import argparse
import datetime as dt
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import sys

KINDS = ("Install", "Upgrade", "Remove", "Purge", "Downgrade", "Reinstall")
PKG_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9+.:~_-]*)\s+\(")
DATE_FMT = "%Y-%m-%d  %H:%M:%S"


def parse_history(text, requested_date, through_date=None):
    """Count APT package operations from matching transaction start dates."""
    counts = {name.lower(): 0 for name in KINDS}
    transactions, duration, incomplete = 0, 0, 0
    for block in re.split(r"\n\s*\n", text.strip()):
        fields = dict(line.split(": ", 1) for line in block.splitlines()
                      if ": " in line)
        if "Start-Date" not in fields:
            continue
        try:
            start = dt.datetime.strptime(fields["Start-Date"].strip(), DATE_FMT)
        except ValueError:
            incomplete += 1
            continue
        if not requested_date <= start.date().isoformat() <= (through_date or requested_date):
            continue
        transactions += 1
        for name in KINDS:
            counts[name.lower()] += len(PKG_RE.findall(fields.get(name, "")))
        try:
            end = dt.datetime.strptime(fields["End-Date"].strip(), DATE_FMT)
            elapsed = int((end - start).total_seconds())
            if elapsed < 0:
                raise ValueError("negative elapsed time")
            duration += elapsed
        except (KeyError, ValueError):
            incomplete += 1
    return {"transactions": transactions, "package_operations": counts,
            "apt_duration_seconds": duration if not incomplete else None,
            "incomplete_transactions": incomplete}


def local_apt_summary(start_date, end_date):
    files = sorted(Path("/var/log/apt").glob("history.log*"))
    if not files:
        return {"status": "missing_history", "reason": "no APT history files"}
    sections = []
    try:
        for path in files:
            if path.name.endswith(".gz"):
                with gzip.open(path, "rt", encoding="utf-8", errors="replace") as source:
                    sections.append(source.read())
            else:
                sections.append(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {"status": "error", "reason": "unreadable APT history"}
    result = parse_history("\n\n".join(sections), start_date, end_date)
    result["status"] = "incomplete" if result["incomplete_transactions"] else "ok"
    result["history_files_read"] = len(files)
    return result


# Only read APT history. The same parser runs inside each supported guest.
REMOTE_CODE = r'''
import sys,json,gzip,re,datetime as dt
from pathlib import Path
K=("Install","Upgrade","Remove","Purge","Downgrade","Reinstall")
P=re.compile(r"([A-Za-z0-9][A-Za-z0-9+.:~_-]*)\s+\(")
files=sorted(Path("/var/log/apt").glob("history.log*"))
r={"status":"ok","transactions":0,"package_operations":{k.lower():0 for k in K},"apt_duration_seconds":0,"incomplete_transactions":0,"history_files_read":len(files)}
if not files: r={"status":"missing_history","reason":"no APT history files"}
else:
 try:
  for p in files:
   with (gzip.open(p,"rt",encoding="utf-8",errors="replace") if p.name.endswith(".gz") else p.open("r",encoding="utf-8",errors="replace")) as f: data=f.read()
   for block in re.split(r"\n\s*\n",data.strip()):
    d=dict(line.split(": ",1) for line in block.splitlines() if ": " in line)
    if "Start-Date" not in d: continue
    try: start=dt.datetime.strptime(d["Start-Date"].strip(),"%Y-%m-%d  %H:%M:%S")
    except ValueError:
     r["incomplete_transactions"]+=1
     continue
    if not sys.argv[1]<=start.date().isoformat()<=sys.argv[2]: continue
    r["transactions"]+=1
    for k in K: r["package_operations"][k.lower()]+=len(P.findall(d.get(k,"")))
    try:
     end=dt.datetime.strptime(d["End-Date"].strip(),"%Y-%m-%d  %H:%M:%S")
     duration=int((end-start).total_seconds())
     if duration<0: raise ValueError("negative elapsed time")
     r["apt_duration_seconds"]+=duration
    except (KeyError,ValueError):r["incomplete_transactions"]+=1
  if r["incomplete_transactions"]:r["status"]="incomplete";r["apt_duration_seconds"]=None
 except OSError:r={"status":"error","reason":"unreadable APT history"}
print(json.dumps(r,separators=(",",":")))
'''


def run(command):
    return subprocess.run(command, capture_output=True, text=True,
                          timeout=45, check=False)


def inventory(command, kind):
    response = run(command)
    if response.returncode:
        raise RuntimeError(f"failed inventory: {command[0]}")
    result = []
    for line in response.stdout.splitlines()[1:]:
        cols = line.split()
        if cols and cols[0].isdigit() and len(cols) >= (3 if kind == "vm" else 2):
            result.append((cols[0], cols[2] if kind == "vm" else cols[1]))
    return result


def guest_summary(kind, guest_id, start_date, end_date):
    if kind == "lxc":
        command = ["pct", "exec", guest_id, "--", "/usr/bin/python3",
                   "-c", REMOTE_CODE, start_date, end_date]
    else:
        command = ["qm", "guest", "exec", guest_id, "--", "/usr/bin/python3",
                   "-c", REMOTE_CODE, start_date, end_date]
    try:
        response = run(command)
        if response.returncode:
            return {"status": "error", "reason": "guest execution command failed"}
        if kind == "vm":
            wrapper = json.loads(response.stdout)
            if (not wrapper.get("exited") or wrapper.get("exitcode") != 0
                    or wrapper.get("out-truncated")):
                return {"status": "error", "reason": "guest agent did not return complete successful output"}
            content = wrapper.get("out-data", "")
        else:
            content = response.stdout
        return json.loads(content.strip())
    except (subprocess.TimeoutExpired, ValueError, KeyError):
        return {"status": "error", "reason": "guest command timed out or returned invalid JSON"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="First date YYYY-MM-DD")
    parser.add_argument("--through-date", help="Last date, inclusive (defaults to --date)")
    parser.add_argument("--exclude-vm", action="append", default=[],
                        metavar="ID", help="Non-APT VM or appliance; repeat as needed")
    parser.add_argument("--output", required=True, type=Path,
                        help="Absolute PRIVATE report path outside public repository")
    args = parser.parse_args()
    end_date = args.through_date or args.date
    try:
        dt.date.fromisoformat(args.date)
        dt.date.fromisoformat(end_date)
    except ValueError:
        parser.error("invalid date, expected YYYY-MM-DD")
    if end_date < args.date:
        parser.error("--through-date precedes --date")
    if not args.output.is_absolute():
        parser.error("--output must be an absolute path")
    if args.output.exists():
        parser.error("output already exists; refusing to overwrite")
    os.umask(0o077)
    report = {
        "schema_version": 1, "date_start": args.date,
        "date_end_inclusive": end_date,
        "scope": "APT transaction start dates in each system's local timezone",
        "collection": "read-only", "systems": [
            {"kind": "host", "id": "local", **local_apt_summary(args.date, end_date)}
        ]
    }
    try:
        groups = [("lxc", inventory(["pct", "list"], "lxc")),
                  ("vm", inventory(["qm", "list"], "vm"))]
    except (RuntimeError, subprocess.TimeoutExpired):
        print("Could not obtain guest inventory", file=sys.stderr)
        return 2
    for kind, guests in groups:
        for guest_id, state in guests:
            item = {"kind": kind, "id": guest_id}
            if kind == "vm" and guest_id in args.exclude_vm:
                item["status"] = "excluded_non_apt"
            elif state != "running":
                item.update(status="not_collected", reason="guest not running")
            else:
                if kind == "vm":
                    try:
                        cfg = run(["qm", "config", guest_id])
                        agent_enabled = cfg.returncode == 0 and bool(
                            re.search(r"^agent:\s*(?:1|enabled=1)(?:\s|,|$)",
                                      cfg.stdout, re.M))
                    except subprocess.TimeoutExpired:
                        agent_enabled = False
                    if not agent_enabled:
                        item.update(status="not_collected", reason="QEMU guest agent unavailable")
                        report["systems"].append(item)
                        continue
                item.update(guest_summary(kind, guest_id, args.date, end_date))
            report["systems"].append(item)
    applicable = [s for s in report["systems"] if s["status"] != "excluded_non_apt"]
    successful = [s for s in applicable if s["status"] == "ok"]
    complete = len(applicable) == len(successful)
    report["aggregate"] = {
        "complete": complete,
        "systems_collected": len(successful),
        "systems_expected": len(applicable),
        "package_operations": {
            name.lower(): sum(s["package_operations"][name.lower()] for s in successful)
            if complete else None for name in KINDS
        },
        "apt_duration_seconds":
            sum(s["apt_duration_seconds"] for s in successful) if complete else None,
        "note": "APT transaction time, not full maintenance window or restore testing."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(f"Private report written: {args.output}; "
          f"collected {len(successful)}/{len(applicable)} applicable systems")
    if not complete:
        print("Aggregate withheld because collection is incomplete.", file=sys.stderr)
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
