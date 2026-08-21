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

The finite Bootstrap-v0 context is: repository and head repository; PR number/state/merged status; base branch/SHA; governed head branch/SHA; candidate tree; remote base/head SHAs; ancestry result; and CI workflow name/path, event, exact single PR association, head SHA, status, and conclusion. Trusted constants are `FlorisOrd/tailor`, `main`, and `.github/workflows/governance.yml` / `Governance Baseline`; the expected PR number and governed head branch are required independent verifier inputs. Missing, malformed, duplicate, ambiguous, unavailable, or mismatched fields fail closed.

REVIEW-05 through REVIEW-08 and their objects, refs, migration binding, and publication audit remain unchanged historical evidence for superseded candidates. They guide regression testing and review, but Release does not normalize or reconcile their formats.
