# Gate Record Protocol

Formal Independent Code Review, QA, Security Review, and Release evidence is a JSON object conforming to `gate-record.schema.json`. The agent performing the gate must publish its own record as a top-level PR comment in this form:

~~~markdown
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

The publishing agent records findings in the same record. BLOCKING and MAJOR findings remain open until a new independent Gate Record closes them and names the recheck. Never edit a prior record to change its disposition; publish a new linked record. Candidate changes make prior records stale even when their history remains useful.

Before authorization, Release exports the agent-authored JSON records without rewriting them and runs `scripts/validate_gate_records.py` for the exact PR/base/candidate/tree and required gates. Release publishes its own Gate Record only after validation passes.

Release then creates `.github/governance/authorization.json` in a dedicated immutable authorization commit whose sole parent is the exact candidate (the authorization file is not in the candidate tree), publishes it under `refs/governance/authorizations/pr-<pr>/<candidate>`, and places its SHA in the integration commit's `Governance-Authorization` trailer. Do not move or reuse an authorization ref. Any changed candidate requires a new Gate Record set, authorization ID, commit, and ref.
