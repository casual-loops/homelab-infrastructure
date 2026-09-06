# Service Dependency Mapping

## Purpose

This document maps major homelab services to the supporting components they depend on. The goal is to improve troubleshooting by making failure domains explicit.

Exact IP addresses, public domains, and sensitive network details are intentionally omitted.

## Dependency model

A user-facing service may depend on several separate layers:

```text
Client
  |
  v
DNS
  |
  v
Network path
  |
  v
Reverse proxy / ingress
  |
  v
Backend application
  |
  v
Authentication / data store / external integration
```

A failure at any layer can produce a similar user symptom, such as "the site is down," even when the root cause is different.

## Service matrix

| Service | Primary dependencies | Validation focus |
|---|---|---|
| Reverse proxy | container health, Nginx, local DNS, wildcard certificate, backend reachability | host health, listeners, certificate trust, hostname routing, backend response |
| Checkmk web access | local DNS, reverse proxy, wildcard certificate, Checkmk backend | DNS resolution, HTTPS response, proxy routing, application sign-in, active DNS check |
| Vaultwarden | local DNS, reverse proxy, TLS certificate, Docker service, persistent application data | DNS resolution, HTTPS response, container health, client sign-in and sync |
| Home Assistant | VM health, local DNS, reverse proxy, wildcard certificate, trusted-proxy configuration, backend listener, integrations | DNS resolution, HTTPS response, WebSocket connectivity, authentication, UI access, integration availability, automation execution, backup access |
| Pi-hole | container health, network path, upstream DNS | local resolution, upstream resolution, filtering behavior |
| Grafana | Monitoring VM, Docker, local DNS, reverse proxy, wildcard certificate, persistent Grafana data, Prometheus data source | DNS resolution, HTTPS response, authentication, dashboard access, data-source connectivity, direct-backend denial |
| Prometheus | Monitoring VM, Docker, target network reachability, configuration file, internal container network | container health, active target health, query execution through internal service paths, absence of unnecessary host exposure |
| NUT exporter | Monitoring VM Docker network, UPS/NUT source, Prometheus scrape configuration | Prometheus target reports `up` and returns expected metrics |
| Samba file services | file-services container, smbd, host firewall, storage path, share permissions, local network path | LAN reachability, authenticated share access, expected file persistence, non-local denial |
| Home Assistant backups | Home Assistant backup subsystem, Samba share, dedicated service account, file-services container | backup completes locally and externally, backup file exists on share |
| Development applications | development host, local network path, application runtime, database where applicable | application starts locally, LAN access only when needed, no premature publication |
| PostgreSQL development database | Development VM, PostgreSQL service, local storage | service status, successful application database query, logical backup, absence of unnecessary remote exposure |

## Development workloads

Development applications are not treated as production web services simply because they may later become user-facing.

While under active development and used only from the home LAN, they remain outside centralized ingress and remote-access publication. Reverse proxy, DNS, and Tailscale access should be introduced only when an actual requirement exists.

## Operational use

When a service fails, use the dependency map to test from the outside inward:

1. Can the client resolve the expected name?
2. Can the client reach the expected network endpoint?
3. Does the proxy or ingress layer respond where one is intentionally used?
4. Is the certificate valid for the requested hostname?
5. Does the backend application respond directly where appropriate?
6. Does the application trust and correctly process the ingress source where forwarded headers are used?
7. Are dependent services healthy?
8. Does the user workflow succeed end to end?
9. Where direct backend access is intentionally restricted, does the denied path remain blocked?
10. For LAN-only services, is the client using the local network path rather than an unintended overlay route?

This approach reduces the tendency to restart the application before proving which layer is actually failing.
