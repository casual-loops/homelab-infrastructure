# Knowledge and Retrieval Container Maintenance

## Scope

This runbook documents maintenance for the Linux container that hosts the private knowledge and retrieval backend.

The public version intentionally omits live guest identifiers, addresses, database names, credentials, source-content locations, and storage paths.

## Monitoring suppression

Schedule Checkmk downtime before disruptive maintenance and retain it through database and application validation.

Follow the [Checkmk maintenance downtime standard](../../monitoring/checkmk/maintenance-downtime.md).

## Pre-maintenance checks

Confirm:

* the guest is included in current backup coverage
* the PostgreSQL cluster is online
* required extensions are available
* filesystem and systemd health are normal
* authoritative source content remains protected independently of rebuildable retrieval state

Useful checks include:

```bash
systemctl --failed
pg_lsclusters
systemctl status postgresql --no-pager
```

## Operating-system maintenance

Refresh metadata and review pending updates:

```bash
apt update
apt list --upgradable
```

Review the transaction before applying it. Then:

```bash
apt full-upgrade
```

Stop and review any configuration-file replacement prompt before accepting it.

## PostgreSQL validation

The umbrella `postgresql.service` may report `active (exited)` while the actual database cluster runs under a versioned unit. Validate the cluster itself rather than treating the umbrella service as the application process.

Examples:

```bash
pg_lsclusters
sudo -u postgres psql -c "SELECT version();"
systemctl --failed
```

Where application-specific databases or extensions are in use, validate them with least-privilege application checks rather than exposing credentials in shell history.

## LXC mount-unit findings

Some systemd mount units can appear failed in an LXC even when the corresponding runtime paths are present and usable.

Before treating failures such as `dev-mqueue.mount`, `run-lock.mount`, or `tmp.mount` as application outages:

1. inspect the affected paths and expected permissions
2. confirm the application and database are healthy
3. clear only stale failed state after validation

Example:

```bash
ls -ld /dev/mqueue /run/lock /tmp
systemctl reset-failed dev-mqueue.mount run-lock.mount tmp.mount
systemctl --failed
```

Do not mask a mount unit or change container features solely to suppress a warning without establishing the cause.

## Validation

Maintenance is complete when:

* PostgreSQL reports the expected cluster online
* a representative database query succeeds
* required extensions remain available
* no unexplained failed systemd units remain
* application-specific health checks pass where the application layer is active
* Checkmk returns to the expected state

## Security considerations

* do not publish database credentials, connection strings, private source paths, or source documents
* keep authoritative source content separate from rebuildable retrieval indexes
* use dedicated application identities where practical
* avoid placing secrets in shell history or public maintenance records

## Rollback

Use the established guest backup or application-native database recovery method appropriate to the failure. If only derived retrieval state is affected, prefer rebuilding it from authoritative source content rather than restoring stale derived data.
