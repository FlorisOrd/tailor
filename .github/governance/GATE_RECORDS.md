# Bootstrap Governance v0 Gate Records

Bootstrap v0 uses one current, candidate-specific protocol. Review, QA, Security Review, and Release each publish their own `Bootstrap Governance v0 Gate Record` for the exact PR, base SHA, candidate SHA, and candidate tree.

The gate agent stores the JSON at `.github/governance/gate-record.json` in an immutable commit whose only parent is the candidate. Publish it at:

`refs/governance/bootstrap-gates/pr-<pr>/<candidate>/<gate-type>/<gate-record-id>`

The same agent adds an exact PR-visible declaration:

~~~markdown
Bootstrap-Gate-Commit: <object SHA>

```bootstrap-gate
{ "record_type": "Bootstrap Governance v0 Gate Record", "...": "..." }
```
~~~

Lead transcription is not gate evidence. Recorded publisher and gate-agent identities must match. GitHub Free cannot prove that textual identities represent physically separate Codex processes; thread separation remains a mandatory procedural control.

## Current Findings and Freshness

A PASS record cannot contain a BLOCKING or MAJOR finding. A serious finding produces FAIL. Repair creates a new candidate, making earlier candidate-specific evidence stale. A fresh independent gate agent reviews or tests the complete new candidate and publishes a fresh record. Bootstrap v0 does not compute approval through a historical repair graph.

## Release Selection

Release explicitly selects exactly one current PASS record for each required gate: Independent Code Review, QA, Security Review, and Release. Validation checks exact identity, immutable object, canonical ref, PR-visible copy, disposition, findings, and recorded role separation. Historical records cannot satisfy a current gate.

Before merge, Release runs `scripts/verify_integration.py authorization --authorization <sha> --reconcile-live --pr-number <expected-pr> --head-branch <expected-head>`. The expected PR and head branch are explicit trusted verifier inputs; they are not derived from the authorization or live GitHub state. Live reconciliation is mandatory. One canonical `LiveReleaseContext` is built independently from GitHub PR state, exact freshly queried `origin` refs, local Git objects/ancestry, and the selected Actions run. Gate Records, CI, and authorization are compared to that same context. Integration later consumes the immutable authorized context and verifies its exact parents/tree while rechecking selected PR-visible gates and CI identity.

The finite Bootstrap-v0 authorization context is: repository and head repository; PR number/state/merged status; base branch/SHA; governed head branch/SHA; candidate tree; remote base/head SHAs; ancestry result; and CI workflow name/path, event, exact single PR association, head SHA, status, and conclusion. Before merge, the candidate Actions PR association is live release identity and must contain exactly the trusted PR. Trusted constants are `FlorisOrd/tailor`, `main`, and `.github/workflows/governance.yml` / `Governance Baseline`; the expected PR number and governed head branch are required independent verifier inputs. Missing, malformed, duplicate, ambiguous, unavailable, or mismatched fields fail closed.

After merge, immutable authorization preserves the authorized PR identity. Integration reconciliation queries that merged PR directly and binds its number, closed/merged state, base and head repositories and branches, candidate head SHA, merge commit SHA, and exposed original base SHA to the authorization and integration. Historical CI is bound by its authorized run ID, repository, workflow name/path, pull-request event, candidate SHA, completed/success result, and exposed head branch/repository. GitHub may empty an Actions run's `pull_requests` array after merge; empty is allowed only with all stronger bindings intact. One association must match the authorized PR; conflicting, multiple, or malformed associations fail.

REVIEW-05 through REVIEW-08 and their objects, refs, migration binding, and publication audit remain unchanged historical evidence for superseded candidates. They guide regression testing and review, but Release does not normalize or reconcile their formats.

## Corrective Implementation Status

REL-CORR-01: **IMPLEMENTATION REPAIRED — AWAITING INDEPENDENT RECHECK**. The Release FAIL `BOOTSTRAP-GATE-RELEASE-BV0-CORR-01-20260821` remains historical evidence for superseded candidate `8aa23907acdd381f6a081af4eaa69f5a8ee6ed91`; its Review, QA, and Security PASS evidence is stale for the repaired candidate. Fresh Independent Code Review, QA, Security Review, and Release evidence is required.

REL-CORR-02: **IMPLEMENTATION REPAIRED — AWAITING INDEPENDENT RECHECK**. Implementation is `IMPL-BV0-CORR-03 Post-Merge CI Association Repair`; Lead is `LEAD-BV0-CORR-03 Post-Merge CI Association Repair` (PR #2 comment 5373749206). Historical authorization `74bd931c1e9469e8e0feef215bfd888d97903942`, Release Gate `ae2c4a9d7a8c86afe736237e2dd4950c3d8cf44a`, integration `b7a3262d83e8851267ab93a4d6c48e27ade92fa8`, and failed run `32512908001` remain unchanged audit evidence. Fresh Independent Code Review, QA, Security Review, and Release are required.
