# Wiki Change Log Entry: 2026-10-29

## October 29, 2026

**Completed full homelab patching and application recovery checks**

Patched the Proxmox hypervisor, six active Linux containers, and four virtual machines during a Checkmk scheduled maintenance window. Confirmed healthy storage, validated guest autostart, verified backups, and rebooted the hypervisor into its updated kernel. All intended guests recovered.

**Application and operating-system updates**

* Updated Pi-hole Core, Web and FTL and verified filtering and DNS resolution.
* Updated the reverse proxy and secure remote-access gateway, including Tailscale; verified private remote connectivity.
* Updated Vaultwarden and its Docker runtime, confirming backup integrity, login, and vault synchronization.
* Patched Samba file services and the PostgreSQL-based knowledge backend, then validated client workflows.
* Updated the monitoring VM, pinned Prometheus and Grafana patch versions, and migrated Grafana to its supported Docker image repository. Dashboards and targets remained functional.
* Patched the development VM, Docker, Node.js and Azure CLI; verified database backup and local applications.
* Updated Home Assistant and verified Core, dashboard, integrations and automations.
* Patched Checkmk's supporting Debian packages and kernel, then verified its monitoring site after reboot.

**Operational findings and lessons learned**

* Home Assistant briefly produced Nginx 502 responses while Core restarted. Direct backend access and proxy logs confirmed temporary unavailability, and the HTTPS route recovered without configuration changes.
* Cleared known stale LXC mount-unit failures only after validating the underlying paths and services.
* Confirmed persistent volumes and restart policies before Docker updates; retained targeted application backups and rollback images.
* Reconciled outdated workload inventory information through current guest inspection.
* Deferred NUT exporter image modernization, Vaultwarden proxy-header review, and Samba cryptography hardening for separate review.

**Outcome:** The planned maintenance and application-level checks passed, with no rollback required. Complete normal monitoring downtime and retained-backup housekeeping as applicable.

[Detailed sanitized maintenance record](https://github.com/casual-loops/homelab-infrastructure/blob/main/change-management/examples/full-homelab-maintenance-2026-10-29.md)
