# Maintenance Record: Full Homelab Maintenance, 2026-10-03

## Maintenance window

**Date:** 2026-10-03  
**Scope:** Hypervisor, active infrastructure containers, active Linux VMs, Home Assistant, and monitoring  
**Status:** Complete

This public record is sanitized and omits live hostnames, addresses, usernames, guest identifiers, share names, and authentication material.

## Pre-maintenance checks

* reconciled the live VM and container inventory
* confirmed current backup coverage before disruptive work
* reviewed guest autostart behavior
* scheduled Checkmk downtime for the affected hosts and services
* confirmed hypervisor storage and systemd health

## Changes performed

* updated the Proxmox host and rebooted into the newly installed kernel
* updated the DNS, password-management, file-services, knowledge-backend, monitoring, development, and Checkmk workloads
* confirmed the reverse-proxy and remote-access workloads were already current
* confirmed Home Assistant had no pending appliance updates
* refreshed the password-management application container
* corrected a guest DHCPv6 configuration that was causing network-service startup timeouts
* corrected Compose handling for a hashed administrative value containing literal dollar-sign characters
* added one interactive Samba identity for approved multi-share workstation access while retaining dedicated service identities for share ownership
* corrected missing autostart settings for core infrastructure guests

## Operational findings

During the Proxmox package transaction, service restarts interrupted management access and stopped Linux containers before the planned reboot. The host itself had not rebooted. The runbook now requires explicit uptime and running-kernel checks before assuming a reboot occurred.

Some Linux containers reported failed mount units even though the corresponding paths were present and usable. The maintenance process now requires validating the paths and application health before clearing stale failed state.

One Checkmk host temporarily showed vanished services after an agent communication failure. Connectivity and the agent transport were verified, then a fresh host check restored the expected service inventory. Discovery cleanup was not required.

## Validation

Post-maintenance validation confirmed:

* the expected hypervisor kernel was active
* all intended guests were running
* hypervisor storage was active
* no unexplained failed systemd units remained on the hypervisor
* DNS resolution worked
* the password-management container was healthy
* file shares were reachable from a client
* PostgreSQL was online and accepted a validation query
* metrics and visualization containers were running
* maintained VMs returned on their expected kernels
* Home Assistant remained current and reachable
* the Checkmk site was operational
* monitored hosts returned to their expected state

## Security and documentation controls

* no live credentials, secret values, private keys, internal addresses, or user identifiers are recorded here
* machine identities remain separate from interactive access where practical
* remote-access controls remain deny-by-default
* management fallback procedures are documented generically rather than with live endpoints
* the maintenance runbooks were updated with lessons learned from this window

## Result

Maintenance completed successfully with no rollback required.
