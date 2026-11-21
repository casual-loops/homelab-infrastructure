# Public Infrastructure Maintenance Metrics

This directory holds **curated, sanitized historical summaries** for a public portfolio. It is not an infrastructure inventory, a configuration export, a live monitoring feed or a synchronization target.

## Publication boundary

Raw source logs, guest configurations, Checkmk exports, incident details, backups and internal names must never be copied here. The private operator reviews evidence and publishes only an explicitly approved aggregate record.

**Allowlisted public fields:** event identifier, local calendar date, maintenance category, outcome, counts of infrastructure classes, counts of recovered guests and monitored hosts, obsolete kernel removal count, observed storage-integrity error count, and strictly generic verification states.

**Excluded fields:** hostnames, guest IDs, addresses, internal URLs, credentials, ports, network paths and topology, detailed software version fingerprints, exact backup locations, vulnerability and security findings, logs, incident narratives and unsanitized free text.

## Data model

Files in `events/` contain one sanitized JSON object per maintenance event. All numeric fields represent **observed** counts, not extrapolated estimates. The monitoring-health metrics describe a point-in-time observation; they are not availability or uptime measurements.

A value of `null` means not recorded or not independently verified. Never substitute zero for missing evidence.

`outcome` describes maintenance work performed, while `administrative_closeout_verified` explicitly records whether downtime and other formal closeout tasks were separately checked.

## Publishing workflow

1. Collect source evidence within private infrastructure.
2. Independently review and reconcile counts against the completed change record.
3. Construct a **new object from the allowlist**; do not redact a full raw export and publish the remainder.
4. Validate against the accompanying JSON Schema and review the final diff for inference and reconnaissance risks.
5. Publish the sanitized record through a reviewed pull request, preferably after maintenance is fully concluded.

## Portfolio integration

A frontend can read these static JSON records at build time for timeline charts, aggregate counters and optional abstract 3D illustrations. The public site must never query monitoring or management infrastructure directly. A 3D visualization should present abstract categories rather than the actual network topology.

Related: [Sanitization policy](../../SECURITY.md) and [maintenance record](../../change-management/examples/full-homelab-maintenance-2026-11-20.md).
