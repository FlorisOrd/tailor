# Gate Record Protocol

Formal gate evidence is JSON conforming to `gate-record.schema.json`. Before commenting, the performing agent creates an immutable commit whose sole parent is the candidate and whose `.github/governance/gate-record.json` is exactly that JSON. It publishes the commit at exactly `refs/governance/gate-records/pr-<pr>/<candidate>/<gate-record-id>`, then publishes its own PR comment:

~~~markdown
Gate-Record-Commit: <40-character commit SHA>

```gate-record
{
  "schema_version": 1,
  "gate_record_id": "GATE-QA-20260820-001",
  "gate_type": "QA",
  "agent_role": "QA",
  "agent_id": "codex-thread-or-agent-id",
  "pr_number": 1,
  "base_sha": "<40 lowercase hex>",
  "candidate_sha": "<40 lowercase hex>",
  "candidate_tree": "<40 lowercase hex>",
  "timestamp": "2026-08-20T12:00:00Z",
  "scope": "Acceptance criteria and regression suite",
  "checks": ["command/procedure and result"],
  "findings": [],
  "disposition": "PASS",
  "repository_state_changed": false,
  "supersedes": null,
  "superseded_by": null
}
```
~~~

The validator requires comment/export JSON, stored JSON, commit parent, object SHA, and exact canonical ref to agree. A different or moved ref, altered JSON, reused ID, or another candidate fails closed.

BLOCKING and MAJOR findings remain open until a later reciprocal successor carries the same finding ID as `CLOSED` and names its rechecking Gate Record. Links must exist, be reciprocal, preserve PR and gate type, advance candidate and timestamp, and remain acyclic. Never edit old evidence; candidate changes make it stale without erasing defect history.

Before authorization, Release fetches and validates the complete `refs/governance/gate-records/pr-<pr>/` ledger, not a selected subset. This keeps every historical OPEN BLOCKING/MAJOR finding visible until a valid successor closes it. Release publishes its own Gate Record only after the complete graph passes.

Release records the exact Review, QA, and Security Gate Record commit SHAs in the authorization. It creates `.github/governance/authorization.json` in a dedicated candidate-parent commit, publishes it exactly at `refs/governance/authorizations/pr-<pr>/<candidate>`, and adds `Governance-PR: <pr>` plus `Governance-Authorization: <sha>` to the integration commit. Never move or reuse evidence refs.
