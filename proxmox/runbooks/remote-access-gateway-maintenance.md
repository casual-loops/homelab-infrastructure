# Secure Remote Access Gateway Maintenance

## Scope

This runbook documents maintenance for the dedicated Linux container that provides secure overlay-network subnet routing.

The public version intentionally omits live network ranges, node identities, route advertisements, access-policy details, authentication keys, and administrative addresses.

## Monitoring suppression

Schedule Checkmk downtime before disruptive maintenance and keep it active through route and policy validation.

Follow the [Checkmk maintenance downtime standard](../../monitoring/checkmk/maintenance-downtime.md).

## Pre-maintenance checks

Confirm:

* the gateway is included in current backup coverage
* the overlay-network service is active
* required forwarding state is present
* intended routes are available
* no unexplained failed systemd units remain
* at least one independent administrative recovery path exists if remote access is interrupted

Do not make the remote-access gateway the only recovery path for the hypervisor or its own container.

## Operating-system maintenance

Refresh metadata and review pending updates:

```bash
apt update
apt list --upgradable
```

Apply reviewed updates:

```bash
apt full-upgrade
```

Stop and inspect any configuration-file replacement prompt before accepting it.

## LXC mount-unit findings

In an LXC, mount units such as `dev-mqueue.mount`, `run-lock.mount`, or `tmp.mount` can remain in a failed state even while the corresponding paths exist and function normally.

Validate first:

```bash
ls -ld /dev/mqueue /run/lock /tmp
```

If the paths and application behavior are healthy and the failures are confirmed stale, clear the failed state:

```bash
systemctl reset-failed dev-mqueue.mount run-lock.mount tmp.mount
systemctl --failed
```

Do not mask units or weaken container isolation merely to eliminate cosmetic failed-state entries.

## Validation

Validate both positive and negative behavior after maintenance:

* the gateway service is active
* expected private routes are available
* an approved remote client can reach an intended administrative target
* a non-approved or backend-only path remains unavailable
* host-level authentication still applies independently of overlay reachability
* Checkmk returns to the expected monitored state

## Security considerations

* do not publish authentication keys, node identities, tailnet names, private routes, or live policy rules
* retain deny-by-default access policy
* keep SSH or other host authentication independent of overlay membership
* do not expose administrative services publicly merely because overlay access is unavailable
* preserve an out-of-band or local recovery method before changing routing or access policy

## Rollback

Restore the prior known-good guest or service configuration. If a package or policy change breaks remote reachability, use the local or console recovery path rather than broadening access controls as a temporary workaround.
