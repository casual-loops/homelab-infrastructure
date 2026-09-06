# Monitoring VM Maintenance Runbook

## Purpose

This runbook documents a verified maintenance workflow for a Proxmox VE virtual machine hosting a Docker-based monitoring stack.

The monitored application stack consists of:

* Prometheus
* Grafana OSS
* Prometheus NUT Exporter

The exact guest ID, hostname, IP address, internal zone names, and other environment-specific identifiers are intentionally omitted from the public version.

## Monitoring suppression

Before disruptive maintenance, schedule Checkmk downtime for the monitored metrics and visualization host and any separately monitored dependency that will intentionally become unavailable.

Follow the [Checkmk maintenance downtime standard](../../monitoring/checkmk/maintenance-downtime.md). Verify the downtime is active before rebooting, restarting Docker, or recreating containers. Keep it active through Prometheus, Grafana, exporter, and guest-agent validation, then remove it early or allow it to expire after the host returns to its expected monitored state.

## Maintenance scope

A full maintenance cycle covers:

1. guest operating-system updates
2. Docker engine and Compose package updates
3. QEMU Guest Agent validation
4. monitoring container image refresh
5. application health validation
6. access-path validation
7. rollback cleanup

## Access model

The co-hosted monitoring services use different access models.

Grafana is the private user-facing visualization service and is presented through the centralized reverse proxy and trusted HTTPS path. Direct client access to the backend listener is restricted at the host firewall so the expected ingress path remains authoritative.

Prometheus is backend infrastructure. Grafana reaches Prometheus through the internal Docker network, so Prometheus does not require a normal host-published web listener for routine operation.

This distinction should be preserved during Compose, firewall, and maintenance changes.

## Pre-maintenance checks

### Confirm guest state

Verify the VM is running and confirm its role before making changes.

From the Proxmox host, validate the guest inventory rather than relying only on a static checklist.

### Verify management access

Preferred access is SSH from an administrative workstation.

If guest-agent access is expected, validate it from the Proxmox host:

```bash
qm guest cmd <vmid> ping
```

If the command fails because the guest agent is unavailable, restore access before future maintenance cycles.

### Confirm storage headroom

Before taking a snapshot, inspect LVM thin-pool utilization:

```bash
lvs
```

Review both `Data%` and `Meta%` for the thin pool. Thin-provisioning overcommit warnings are not equivalent to current pool exhaustion, but a nearly full thin pool is a maintenance blocker.

### Create rollback protection

Take a pre-maintenance VM snapshot when appropriate.

Recommended naming pattern:

```text
pre-maintenance-YYYY-MM-DD
```

Do not keep temporary maintenance snapshots indefinitely.

## Operating-system maintenance

### Identify the OS and kernel

```bash
cat /etc/os-release
uname -r
```

### Refresh package metadata

```bash
sudo apt update
```

### Review pending upgrades

```bash
apt list --upgradable
```

When Docker or container runtime packages are included, identify the active application stack before upgrading the underlying runtime.

### Identify active containers

```bash
sudo docker ps
```

Record the expected container set before maintenance.

### Locate the Compose project

For a container managed by Docker Compose:

```bash
sudo docker inspect <container> --format '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}'
```

Review the Compose configuration before changing container images:

```bash
cd <compose-project-directory>
cat docker-compose.yml
```

Confirm persistent application data is stored in named volumes or bind mounts before recreating containers.

### Apply package upgrades

```bash
sudo apt full-upgrade
```

Review the transaction summary before accepting when practical. Unexpected package removals require investigation.

### Check systemd health

```bash
sudo systemctl --failed
```

Expected result:

```text
0 loaded units listed.
```

## QEMU Guest Agent

If the Proxmox configuration expects QEMU Guest Agent but the service is absent, install it inside the guest:

```bash
sudo apt install qemu-guest-agent
```

Start the service:

```bash
sudo systemctl start qemu-guest-agent
```

Check status:

```bash
sudo systemctl status qemu-guest-agent --no-pager
```

The service may be a static systemd unit, so a warning from `systemctl enable` is not necessarily a failure. The important checks are that the service is active and Proxmox can reach it.

Validate from the Proxmox host:

```bash
qm guest cmd <vmid> ping
```

## Monitoring stack maintenance

The verified stack uses Docker Compose and persistent volumes for Prometheus and Grafana data.

Application image refresh is treated as a separate step from operating-system package maintenance.

### Pull current images

```bash
sudo docker compose pull
```

### Recreate the stack

```bash
sudo docker compose up -d
```

### Confirm containers are running

```bash
sudo docker ps
```

Expected services include:

* Prometheus
* Grafana OSS
* Prometheus NUT Exporter

After recreation, confirm that container publishing still matches the intended access model. A Compose change should not silently reintroduce a host-published Prometheus listener or broaden direct Grafana backend access.

## Application validation

### Grafana

Validate Grafana through the normal named HTTPS path rather than relying only on the backend listener.

Confirm:

* the expected hostname resolves to the centralized reverse proxy
* the trusted HTTPS path loads normally
* authentication succeeds
* existing dashboards render and contain data
* Prometheus remains available as the configured data source
* direct client access to the backend listener remains blocked where expected

### Prometheus

Prometheus is consumed through the internal Docker network by Grafana and other intended monitoring components.

Validate container health and query behavior without requiring a host-published web listener. Examples include executing a query from an authorized container path or confirming healthy data-source access from Grafana.

### Exporter health through Prometheus

A container port that is only exposed inside the Docker network may not be reachable through `localhost` on the host. Validate the exporter through Prometheus target health instead.

Expected validation should confirm that the exporter is functioning in the context that matters: Prometheus can scrape it successfully.

## Host firewall validation

Review the host firewall after network or container changes.

The intended policy should preserve:

* administrative access from approved management networks
* Grafana backend access only from the expected reverse-proxy path
* monitoring-agent access only from the expected monitoring source
* no obsolete allowance for Prometheus when its host listener is not published

Public documentation intentionally omits live addresses and exact rule numbering.

## Post-maintenance validation

Run final checks:

```bash
sudo systemctl --failed
sudo docker ps
sudo ufw status
```

Also confirm:

* Grafana loads through the centralized HTTPS path
* direct Grafana backend access remains restricted
* Grafana dashboards still contain current data
* Prometheus remains reachable to Grafana through the internal container network
* expected Prometheus targets are healthy
* no unnecessary Prometheus host listener has been reintroduced
* Proxmox guest-agent communication succeeds
* Checkmk reports the expected final host and service states before downtime is removed

## Cleanup

After validation:

1. detach any temporary Ubuntu installation or rescue ISO from the virtual CD/DVD drive
2. restore normal boot order if it was changed
3. remove the temporary pre-maintenance snapshot
4. record the maintenance outcome and any deviations

## Access recovery note

If administrative credentials are unavailable, a live Ubuntu Server ISO can be used as a rescue environment to mount the installed root filesystem and reset a local account password.

This is a recovery procedure, not part of normal maintenance. Avoid changing partitions or reinstalling the OS when using the rescue environment.

## Rollback

If the guest or monitoring services fail validation after maintenance:

1. stop further changes
2. preserve diagnostic information where practical
3. revert to the pre-maintenance snapshot if necessary
4. confirm the VM boots and the monitoring stack returns to its previous state
5. document the failed change before retrying
