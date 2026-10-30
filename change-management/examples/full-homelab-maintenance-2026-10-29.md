# Maintenance Record: Full Homelab Maintenance, 2026-10-29

## Maintenance window

**Date:** 2026-10-29 (local), continuing into 2026-10-30 UTC  
**Scope:** Proxmox hypervisor, six active Linux containers, four active VMs, application services, and monitoring  
**Category:** Routine planned maintenance  
**Result:** Completed patching and workload validation; final monitoring downtime clearance and artifact cleanup not independently recorded.

This is a sanitized public record. Live addresses, hostnames, account identifiers, guest IDs, internal storage paths, and authentication material are intentionally omitted.

## Pre-maintenance controls

* Reconciled the live inventory: six active containers and four active VMs. The retired media workload was not included.
* Confirmed all active guests had recent scheduled backup archives, with healthy ZFS pools and active storage.
* Verified guest autostart configuration, hypervisor service health, and the package transaction before applying updates.
* Scheduled Checkmk maintenance downtime before service disruption.
* Kept an alternate management path independent of the reverse proxy and local DNS.
* Took additional application and VM recovery points for sensitive data and changes to stateful Docker applications.

## Changes performed

| Workload | Maintenance performed | Validation |
|---|---|---|
| Proxmox hypervisor | Upgraded manager from 9.2.21 to 9.2.24; activated kernel 7.0.14-26 after host reboot | Storage, ZFS, service health, all ten guest recoveries |
| DNS and filtering | Applied Debian security updates; updated Pi-hole Core to 6.5, Web to 6.6.1, and FTL to 6.8 | DNS queries, filtering, listeners, service health, web interface |
| Nginx reverse proxy | Applied Debian timezone update; cleared previously understood stale mount-unit failures after path checks | Configuration test, listeners, HTTPS routing |
| Secure remote access | Applied Debian updates and updated Tailscale from 1.102.3 to 1.104.4 | Daemon, forwarding, tailnet state, remote subnet access from a client |
| Password management | Applied Debian and Docker updates; updated Vaultwarden from 1.37.3 to 1.37.4 | Application health, HTTPS login, vault content, synchronization |
| File services | Applied Ubuntu security and system updates | Samba configuration, storage mounts, and client SMB access |
| Knowledge and retrieval | Applied Debian security updates | PostgreSQL connectivity and query, retrieval workflow, service health |
| Metrics and visualization | Applied Ubuntu and Docker updates; pinned Prometheus at 3.13.5 and Grafana at 13.0.12; switched Grafana to supported image repository | Metrics readiness, scrape targets, dashboards, application login |
| Development | Applied Ubuntu, Docker, Node.js, and Azure CLI updates | Supabase containers, PostgreSQL query and application checks, development services |
| Home automation | Installed available Home Assistant OS, Core, and custom component updates | Core, direct and proxied access, dashboard, integrations and automations |
| Infrastructure monitoring | Applied Debian updates, including Apache, PHP and kernel 6.12.113; Checkmk remained 2.5.0p11 Community | Site status and HTTPS UI after VM reboot |

No intentional major OS release upgrade, storage rearchitecture, network policy change, or application database reset was performed.

## Backups and rollback readiness

* Verified recent backup archives for each active workload before starting.
* Created and verified a password-management SQLite backup with a checksum comparison and database integrity check. Also retained a protected archive of supporting application files and a previous container image reference.
* Created a VM backup and separate stopped-application data archive before the Grafana image migration.
* Created a compressed PostgreSQL logical dump for the development stack and verified archive integrity; also created a fresh VM backup.
* Created a Checkmk site backup before updating its operating system.
* Home Assistant used its appliance backup workflow and existing VM-level backup protection.

Backup creation and archive checks do not constitute a full restoration exercise. Temporary recovery artifacts remain subject to retention and cleanup review.

## Operational findings

### Short-lived Home Assistant 502 response

Immediately after appliance updates, the Nginx frontend returned HTTP 502. Direct access later succeeded. The proxy's configured upstream was correct, and its logs recorded connection refusals and connection resets while Home Assistant was restarting. After Core completed initialization, the normal HTTPS dashboard recovered without a proxy configuration change.

**Runbook improvement:** After Home Assistant OS or Core updates, expect a temporary backend outage. Check Core startup and direct application access before modifying the proxy; use an HTTP GET rather than HEAD when checking the application's endpoint.

### Stale LXC mount-unit states

The reverse-proxy and knowledge-backend guests reported failed mount units for message queues, lock, and temporary directories. After confirming the relevant paths were present and applications functional, stale systemd failures were cleared. No application fault was established.

### Docker image and recovery practices

Validated Docker restart policies and persistent mounts before daemon upgrades. Kept stateful image updates separate from OS patching. Pinned Prometheus and Grafana versions rather than relying on mutable `latest` tags; Grafana was moved from the legacy OSS image path to its supported repository. An aging UPS exporter image was intentionally left unchanged pending a separate review.

### Inventory reconciliation

Corrected an outdated internal address-to-workload mapping through direct guest inspection. The public record does not publish those addresses.

## Post-maintenance validation

The operator reported completing final application-level validation, including file-share access, knowledge retrieval, development application checks, Home Assistant integrations, and automations. Proxmox recovered all ten intended guests after reboot. Checkmk and its UI returned following the monitoring VM reboot.

**Not separately evidenced in this record:** A final screenshot or export of all Checkmk host/service states, exact downtime removal time, and removal or retention disposition of temporary local backups. These are administrative closeout items, not evidence of a known service outage.

## Follow-up actions

1. Confirm Checkmk scheduled downtime expired or was removed and normal alert delivery resumed.
2. Review retained temporary backup archives and pre-upgrade Docker images against recovery retention policy.
3. Review the UPS exporter image's maintenance status and replacement options.
4. Review Vaultwarden trusted proxy and client-IP forwarding configuration in light of the application update.
5. Review Samba's weak-cryptography allowance separately from routine patching.
6. Verify that external or independently recoverable copies of critical backups exist and periodically test restoration.
7. Refresh sanitized architecture and maintenance runbooks where actual access paths, image versions, or startup dependencies have evolved.

## Outcome

All planned host, guest, and application patches were reported successful, and maintained services returned to operation. The transient Home Assistant proxy error cleared after application startup. No rollback was required.
