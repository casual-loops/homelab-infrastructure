# Maintenance Record: Full Homelab Maintenance, 2026-11-20

## Maintenance window

**Date:** 2026-11-20 local, continuing into 2026-11-21 UTC  
**Category:** Routine planned maintenance  
**Scope:** One Proxmox hypervisor, six active Linux containers, four active virtual machines, supporting services and monitoring  
**Result:** Maintenance and observed recovery checks passed; one nonblocking guest compatibility issue retained for private follow-up. Final scheduled monitoring downtime clearance was not independently confirmed.

This is a deliberately sanitized public operations record. It omits live identifiers, addresses, guest IDs, private endpoints, internal topology details, backup locations and operational fault specifics.

## Preparation and recovery controls

* Reconciled the active inventory before host maintenance.
* Confirmed backup archives existed for all ten guests. Backup existence does not prove independently tested restoration.
* Reviewed package transactions, kernel fallback availability and boot configuration before rebooting the hypervisor.
* Verified guest autostart configuration prior to the coordinated host restart.
* Used scheduled monitoring downtime for the disruptive maintenance window.

## Maintenance performed

| Area | Work completed | Validation |
|---|---|---|
| Hypervisor | Applied Proxmox maintenance updates and activated an updated signed kernel | Reboot completed, boot configuration valid, storage healthy, no failed host systemd units |
| Linux guests | Installed Debian and Ubuntu package and kernel updates where applicable | OS service checks, retained fallback kernels and package integrity checks |
| Container runtime | Updated Docker on applicable guests and checked stateful service persistence | Expected containers resumed; an additional database container startup policy was corrected |
| Infrastructure monitoring | Updated Checkmk Community and its supporting OS, retaining a previous application installation for rollback | Monitoring site available; all twelve observed hosts UP with zero WARN, UNKNOWN and CRIT services |
| DNS and filtering | Updated Pi-hole components and separated two conflicting log rotation schedules | DNS resolution passed; revised rotation completed successfully at 02:00 UTC on November 21 |
| Remote access and ingress | Updated applicable system packages and gateway software | Relevant daemons active and remote-access peer status visible; reverse-proxy services active |
| Password management | Updated host runtime and verified application health | Container healthy and application liveness endpoint responsive |
| Monitoring metrics | Updated monitoring guest and runtime | Grafana, Prometheus and power exporter containers running |
| Application development | Updated development tooling and runtime | Database and supporting application containers recovered and reported healthy |
| Home automation | Validated appliance recovery following hypervisor reboot | UI, updates, repairs, integrations and entities checked successfully |
| Knowledge backend | Updated Linux and PostgreSQL components | Database service active; application API deployment not established by the available checks |

## Measured results

| Measure | Observed value | Interpretation |
|---|---:|---|
| Infrastructure systems in scope | 11 | One hypervisor and ten active guests |
| Linux containers | 6 | Active maintenance inventory |
| Virtual machines | 4 | Active maintenance inventory |
| Guest recovery after host reboot | 10 / 10 | All expected guests running |
| Monitoring host states | 12 / 12 UP | Snapshot after maintenance, not an uptime percentage |
| Monitored warning, unknown and critical service counts | 0 | Observed in final Checkmk overview |
| Obsolete kernel packages removed | 5 | Two from the hypervisor; one from each of three Linux VMs |
| ZFS known data errors | 0 | Post-maintenance storage inspection |
| Confirmed successful scheduled log rotations after timer change | 1 | Successful service exit status |
| Guest backup archives observed | 10 / 10 | Restore testing not independently established |

Do not interpret guest recovery as an availability percentage or the monitored health snapshot as proof of zero downtime. Total updated package counts and the exact maintenance duration were not independently reconciled and are intentionally omitted.

## Operational findings

* A home automation appliance required an extended but graceful shutdown. It recovered and passed its application checks without a forced stop.
* An auxiliary database container did not restart automatically. Its existing restart policy was adjusted and the runtime state inspected.
* A scheduled rotation collided with another rotation process at midnight. Moving the systemd timer to a separate execution window was validated by a successful scheduled run.
* A nonblocking compatibility warning was identified on one Linux container. The affected guest's database was operational; no unsupported mount workaround was applied. Further investigation is retained in private operational records.
* Application-level verification identified differences between a healthy operating system, a running container and a responding application.

## Rollback and cleanup

* Preserved a currently running kernel plus a recent fallback on each maintained Linux VM.
* Preserved the active hypervisor kernel and a previously working fallback.
* Removed five obsolete kernel packages after reviewing package-manager simulations.
* Retained a prior monitoring application version temporarily for rollback.
* No rollback was required during the completed maintenance tasks.
* Independent restore testing and the disposition of all temporary recovery artifacts were not evidenced as completed in this record.

## Monitoring and closeout

The post-maintenance monitoring overview showed twelve hosts UP and no warning, unknown or critical service counts. A separate confirmation that scheduled Checkmk downtime had expired or been removed was not captured, so it remains an administrative closeout check.

**Outcome:** Planned updates, host reboot, guest recovery, and the recorded application and monitoring validations succeeded. Follow-up issues and any private operational details remain outside the public repository.
