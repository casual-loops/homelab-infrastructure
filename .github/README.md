# Repository Continuous Integration

The public repository uses three lightweight GitHub Actions checks on pull requests and on `main`. All jobs use read-only repository permissions, run on GitHub-hosted runners and have a ten-minute timeout.

| Required check | What it tests |
|---|---|
| **Python tests** | Syntax compilation and synthetic tests for the private APT collector and public metrics validator |
| **Public metrics validation** | JSON Schema Draft 2020-12, date/id consistency, inventory totals, and an allowlist of approved fields |
| **Secret scan** | Gitleaks scan of the repository's Git history; reports are redacted |

The checks never connect to private infrastructure, collect live metrics, run deployments, or publish data. Secret scanning and schema validation are defense in depth and **do not replace manual review against** [SECURITY.md](../SECURITY.md).

## Local verification

Requires Python 3.12 and `jsonschema[format]==4.25.1` for the public-metrics validator.

```bash
python3 -m pip install 'jsonschema[format]==4.25.1'
python3 -m unittest discover -s operations/maintenance-collector/tests -v
python3 -m unittest discover -s scripts/tests -v
python3 scripts/validate_public_metrics.py
```

The repository's historical secret scan can be run locally with Gitleaks 8.30.1:

```bash
gitleaks git . --redact --exit-code 1 --no-banner
```

If a scan detects real secrets, treat any committed credentials as compromised. Rotate them and follow the repository's incident handling guidance; removing a secret from the latest commit is not sufficient.

## Branch protection

Once these jobs complete successfully on a pull request, configure protection for `main` using the exact status-check names displayed by GitHub:

* `Python tests`
* `Public metrics validation`
* `Secret scan`

Require pull requests and all three checks before merge. Disallow force pushes and branch deletion. You can keep required reviewer approvals at zero for a solo-maintainer project.

Do **not** enable mandatory status checks before these names appear in a completed workflow run or GitHub may block merging.

## Version management

Action revisions are pinned by commit SHA. Update them deliberately through reviewed pull requests. The validator dependency and Gitleaks version are pinned; monitor them periodically for fixes.
