# Read-only APT maintenance collector

This is a **private-report generator** intended to run on the Proxmox hypervisor. It collects historical APT transaction summaries from the host and active Debian or Ubuntu LXC containers and QEMU Guest Agent-enabled VMs. It makes no package, configuration, guest-state, or monitoring changes.

It requires Python 3 on the host and each inspected guest. It uses Proxmox `pct exec` and `qm guest exec` without opening guest SSH or adding credentials.

## Usage

Copy `collect_apt_maintenance.py` to a private location on the Proxmox host, outside the public Git checkout.

For an APT maintenance window that crossed local midnight, execute as an authorized Proxmox administrator:

```bash
python3 /root/collect_apt_maintenance.py \
  --date 2026-11-20 \
  --through-date 2026-11-21 \
  --exclude-vm '<NON_APT_APPLIANCE_ID>' \
  --output /root/maintenance-private/apt-2026-11-20.json
```

Replace the appliance placeholder with its VM ID **only in your private shell**, not in a repository commit. Repeat `--exclude-vm` for additional non-APT appliances.

The collector returns nonzero if the report is incomplete, but still writes a private report identifying missing systems. It refuses to overwrite existing files and creates the report with restrictive file permissions. A VM without a usable guest agent is recorded as not collected. A stopped guest is not started.

## Semantics and limitations

* Dates select transactions by their **start calendar date in each system's local timezone**, inclusive. OS and host timezones may differ.
* Matching APT transactions outside the intended maintenance window on those days may also appear. Review before attributing the counts to the window.
* Upgraded, installed, removed, purged, downgraded and reinstalled package entries are **operation counts**, not distinct package names.
* APT duration sums logged transaction start-to-end elapsed times. It **is not** the total maintenance duration, active operator time, reboot time or downtime.
* Missing history, incomplete transactions and guest-agent failures are explicitly flagged. Aggregate values become `null` rather than silently treating partial counts as complete.
* Backup creation and service recovery are **not** restore tests. This script cannot verify restore-test counts.
* Non-APT guests (for example Home Assistant OS) must be explicitly excluded. They are not counted as missing APT coverage.
* A successful command does not independently prove that all historical log files have been retained. Rotated `.gz` histories are read when available.

## Privacy and publication

The report is **PRIVATE** and contains guest IDs and per-system counts. Never commit generated reports or raw APT logs. The public portfolio must use separately reviewed allowlisted aggregate data, as defined in [public metrics](../public-metrics/README.md) and [SECURITY.md](../../SECURITY.md). Do not deploy a web endpoint that reads these reports.

## Tests

Run the standard-library test suite locally before deployment:

```bash
python3 -m unittest discover -s operations/maintenance-collector/tests -v
```
