# Security Governance

## Baseline Rules

- Never commit passwords, tokens, private keys, populated environment files, or production data.
- Store secrets in an approved secret manager or local ignored environment; provide redacted examples only.
- Apply least privilege, deny by default, validate untrusted input, encode output, and use safe framework primitives.
- Minimize collected data, define retention, protect data in transit and at rest, and avoid sensitive values in logs or analytics.
- Pin or lock dependencies where supported; review provenance, maintenance, license, and known vulnerabilities.
- Keep error messages useful without exposing internals, credentials, or personal data.
- Do not weaken security controls merely to make a test pass.

## Mandatory Security Review Triggers

A dedicated Security Review by an agent other than the implementer is required for authentication, authorization, session management, billing or payments, personal or regulated data, file uploads, external APIs or webhooks, secrets or cryptography, database access or migrations, privilege boundaries, executable content, dependency or infrastructure changes, public endpoints, and any change that alters trust boundaries.

## Review Evidence

Security Review records the data and trust boundaries, plausible abuse cases, access-control behavior, input and output handling, secret handling, dependency or vulnerability results, logging and privacy impact, failure modes, and required mitigations. Use automated scanners where appropriate, but do not treat a clean scan as complete threat analysis.

Critical or high-risk findings block release. Medium-risk findings require repair or a documented, time-bounded exception with compensating controls. Product-owner approval is required when accepting risk could affect privacy, legal/compliance duties, spending, customers, or irreversible external actions.

## Incident Handling

Agents must avoid copying exposed secrets into issues, commits, or chat. If exposure is suspected: stop propagation, preserve non-sensitive evidence, rotate or revoke the credential through an authorized channel, assess Git history and downstream systems, and document remediation. Rewriting shared history or making external disclosures requires explicit owner approval because those actions may be irreversible or legally consequential.

Report vulnerabilities privately through a repository security advisory or another owner-approved private channel once one is configured. Do not publish exploit details before remediation.
