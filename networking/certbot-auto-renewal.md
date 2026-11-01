# Automated ACME Certificate Renewal

## Implementation status

Completed and validated on 2026-11-01. The dedicated Nginx ingress container uses Certbot in a Python virtual environment, DNS challenge authentication through Porkbun, and a single apex plus wildcard certificate. Certificate material and DNS credentials stay on the proxy, never in this repository.

The configured workflow is:

1. A systemd timer starts a Certbot renewal check twice daily, with randomized delay and persistent scheduling.
2. Certbot attempts reissuance only when its renewal policy considers the certificate due.
3. A deploy hook validates Nginx configuration and gracefully reloads Nginx after successful certificate renewal.
4. A successful systemd invocation updates a persistent last-success marker.
5. A Checkmk local check monitors the timer, last run result, and age of the last successful invocation. Separate HTTPS active checks monitor the actual certificate expiration.

## Sanitized systemd service

File: `/etc/systemd/system/certbot-renew.service`

```ini
[Unit]
Description=Renew Let's Encrypt TLS certificates
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/certbot/bin/certbot renew --quiet
```

File: `/etc/systemd/system/certbot-renew.timer`

```ini
[Unit]
Description=Scheduled Let's Encrypt certificate renewal checks

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

Enable with `systemctl daemon-reload && systemctl enable --now certbot-renew.timer`.

## Nginx deploy hook

Place an executable script in `/etc/letsencrypt/renewal-hooks/deploy/`:

```bash
#!/bin/bash
set -e
/usr/sbin/nginx -t
/bin/systemctl reload nginx
```

A deploy hook is only executed after a successful certificate renewal. Its validity and the Nginx reload were tested independently.

## Persistent monitoring marker

Create `/var/lib/certbot-monitor/` and add this systemd drop-in at `/etc/systemd/system/certbot-renew.service.d/monitor.conf`:

```ini
[Service]
ExecStartPost=/usr/bin/touch /var/lib/certbot-monitor/last-success
```

The marker records the last *successful Certbot invocation*, not the last certificate issuance. Reload systemd after adding the drop-in and start the service once to initialize the marker.

## Checkmk service

Install the executable local-check script documented at [Certbot Renewal local check](../monitoring/checkmk/local-checks/certbot_renewal) into `/usr/lib/check_mk_agent/local/certbot_renewal` on the reverse proxy.

The service is named **Certbot Renewal**. Its default execution-age levels are WARN at 36 hours and CRIT at 48 hours. Disabled or inactive timer and detectable execution failures are CRIT. Missing history is UNKNOWN.

Inspect actual agent data using `cmk-agent-ctl dump`, then discover and accept the local service in Checkmk. The validated service reported OK. The service's normal inactive state is not itself an error because it is a systemd oneshot.

The marker persists across restarts; in-memory systemd failure details may not. Keep the separate HTTPS certificate expiration check enabled: successful renewal *checks* do not prove certificates have been renewed.

## Validation performed

- Certbot `renew --dry-run` succeeded using DNS challenge credentials.
- Nginx configuration test and reload hook succeeded.
- systemd timer was enabled and active, with a future activation.
- Manual start of the renewal service completed with `status=0/SUCCESS`.
- Certbot recognized one ECDSA certificate covering the domain apex and wildcard.
- The persistent marker was written after a successful run.
- The Checkmk controller exported `<<<local:sep(0)>>>` with `Certbot Renewal` reporting OK.
- Checkmk discovery and active service status were confirmed OK.

No real renewal was claimed during these checks. The original certificate was still valid and awaiting its normal renewal window.

## Operations

```bash
systemctl status certbot-renew.timer
systemctl list-timers --all certbot-renew.timer
systemctl status certbot-renew.service
journalctl -u certbot-renew.service -n 50 --no-pager
/opt/certbot/bin/certbot certificates
/opt/certbot/bin/certbot renew --dry-run
cmk-agent-ctl dump | grep -A 2 '<<<local'
```

If monitoring becomes CRIT, first verify timer state, Certbot service exit status, and journal logs. If certificate expiration is approaching, verify the live certificate and the DNS challenge flow. Do not bypass certificate validation just to return monitoring to green.

## Security and recovery

Do not commit Porkbun API credentials, the ACME account, private keys, the live renewal configuration containing account identifiers, or live infrastructure hostnames and addresses. Preserve those artifacts in protected backups of the proxy. Following a rebuild, restore secure credentials separately, recreate the timer, hook, and monitoring files, then repeat a dry run and full monitoring validation.
