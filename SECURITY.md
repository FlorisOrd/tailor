# Security Governance

## Baseline Rules

- Never commit passwords, tokens, private keys, populated environment files, or production data.
- Store secrets in an approved secret manager or ignored local environment; provide redacted examples only.
- Apply least privilege and deny by default; validate untrusted input, encode output, and use safe framework primitives.
- Minimize collected data, define retention, protect data in transit and at rest, and exclude sensitive values from logs and analytics.
- Keep errors useful without exposing internals, credentials, or personal data.
- Never weaken a security control merely to make a test pass.

Secret protection is non-waivable. Suspected exposure follows `INCIDENT_RESPONSE.md`.

## Mandatory Security Review and Independence

Dedicated Security Review is required for authentication, authorization, sessions, billing/payments, personal or regulated data, uploads, external APIs or webhooks, secrets or cryptography, databases or migrations, privilege boundaries, executable content, dependencies, infrastructure, public endpoints, and any changed trust boundary.

For a triggered change, Security Review must be a different Codex thread/agent from Implementation, Lead/gate authority, QA, and Release. It records threat and data boundaries, plausible abuse cases, access-control behavior, input/output handling, secret handling, dependencies, logging/privacy impact, failure modes, and mitigations. Every security-relevant repair creates a new candidate and must return to the independent Security reviewer for recheck. These independence and recheck requirements are non-waivable under the canonical list in `WORKFLOW.md`.

Authentication, authorization, billing/payments, personal data, persisted-data migrations, infrastructure, deployment/security boundary changes, and other security-sensitive behavior require representative non-local isolated pre-production verification before production. The environment requirement is non-waivable; a local substitute never qualifies. Security Review approves security-relevant parity differences and compensating verification, but cannot waive the representative environment.

## Secrets and Supply Chain

`.github/workflows/governance.yml` configures Gitleaks secret scanning for pushes, pull requests, manual runs, and a weekly schedule. This configuration is not a required check without branch protection and scheduled runs do not operate from this feature branch; current enforcement status is documented in `.github/GOVERNANCE_ENFORCEMENT.md`.

When code or dependencies exist, CI must also run an appropriate dependency/SCA and vulnerability scanner on pull requests and at least weekly. Dependency additions or updates require:

- deterministic, integrity-checked lockfiles where the ecosystem supports them;
- review of direct and material transitive changes;
- vulnerability results and documented disposition;
- provenance, maintenance, and license review proportionate to risk;
- pinned third-party CI actions by full commit SHA;
- an update to `.github/dependabot.yml` or an equivalent scheduler for every supported ecosystem.

Until an ecosystem is selected, no dependency scanner is claimed active. The first dependency-bearing change is incomplete until it supplies canonical install/audit commands, CI scanning, lockfile policy, and scheduled rescanning.

## Security Severity Thresholds

Use the shared taxonomy in `WORKFLOW.md`. Confirmed secret exposure, active compromise, exploitable critical vulnerability, authorization bypass, or material personal-data exposure is BLOCKING. High-severity exploitable vulnerabilities and material defense failures are at least MAJOR. BLOCKING and MAJOR findings block approval/release and require independent Security recheck. Medium or lower findings map to MAJOR, MINOR, or SUGGESTION based on exploitability and impact; MINOR acceptance requires tracked debt, owner, target date, and compensating controls where relevant.

Automated scans supplement rather than replace threat analysis. False positives require documented evidence and Security Review disposition; they are not silently ignored.

## Private Reporting

Keep vulnerability details out of public channels. Use a private GitHub security advisory or another owner-approved private channel once configured. Do not publish exploit details before remediation. External disclosure, legal notices, or acceptance of privacy/compliance risk requires owner approval.
