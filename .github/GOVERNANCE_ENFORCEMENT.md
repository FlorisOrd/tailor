# Governance Enforcement Status

## Account Constraint

This is a private repository on GitHub Free. The owner reports that private-repository branch protection/rulesets are unavailable. This repository therefore does **not** claim that GitHub technically blocks direct pushes, requires pull requests, enforces reviews, or requires status checks on `main`.

Governance remains mandatory even when a control is procedural. A capability limitation is not permission to bypass a gate.

## Controls Available Now

The following files are configured on `bootstrap/agent-company`. They become the repository baseline only after an authorized merge to the default branch:

- `.github/workflows/governance.yml` runs governance validation and Gitleaks secret scanning on pushes, pull requests, manual dispatch, and a weekly schedule. Scheduled workflows use the default branch; CI status is informative rather than technically required while branch protection is unavailable.
- `.github/PULL_REQUEST_TEMPLATE.md` makes each PR a durable work, review, test, staging, release, and debt record.
- `scripts/validate_governance.py` checks required governance files, formatting, key control language, pinned Action references, and initial dependency readiness.
- `.github/dependabot.yml` requests weekly updates for GitHub Actions dependencies after it is present on the default branch and Dependabot is enabled for the repository.

The Lead and Release roles procedurally enforce feature-branch work, exact-candidate identity, independent roles, evidence freshness, and release authorization. The GitHub PR and commit history provide the durable audit trail. Distinct Codex-agent roles may use one GitHub account, so GitHub identity alone cannot prove agent independence; the PR record must identify the separate threads/agents and their dispositions.

## Not Currently Hard-Enforced

GitHub may still technically allow a direct or force push, deletion of `main`, merge with failing checks, self-merge, missing reviews, or dismissal/bypass of review state. Required CI and reviewer counts are not claimed. The governance workflow and scheduled automation also depend on GitHub Actions/Dependabot being enabled and, until this branch is merged, are not controls on `main`.

Release must treat absent or failing automation as a failed gate, not as success. When an automated service is unavailable, follow the documented exception rules only for waivable gates; non-waivable gates remain blocked.

## Future Technical Enforcement

When account capabilities allow, configure a `main` ruleset or branch protection to:

1. require pull requests and prevent direct/force pushes and branch deletion;
2. require the governance and secret-scan checks plus product-specific quality/security checks;
3. dismiss stale approvals and require approval of the latest reviewable push;
4. require conversation resolution and linear, traceable history where compatible;
5. restrict bypass to a documented emergency path with audit logging;
6. require signed commits or verified signatures if operationally supportable.

GitHub settings cannot by themselves guarantee that separate Codex threads performed Implementation, Review, QA, Security, and Release. Keep the durable role/evidence record even after hard branch controls become available.

Any change to the account plan or repository capabilities requires the Lead to reassess this file and record the resulting enforcement decision in `DECISIONS.md`.
