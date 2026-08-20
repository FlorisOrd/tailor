# Append-Only Gate Record Protocol

Each performing agent stores its schema-version-2 JSON in `.github/governance/gate-record.json` in an immutable commit whose sole parent is the candidate. It publishes that commit at exactly `refs/governance/gate-records/pr-<pr>/<candidate>/<gate-record-id>` and posts the same JSON itself as a top-level PR comment:

~~~markdown
Gate-Record-Commit: <40-character commit SHA>

```gate-record
{ "schema_version": 2, "gate_record_id": "GATE-...", "...": "..." }
```
~~~

Historical records never change. A later record may point backward through `supersedes`; predecessors have no forward pointer. The graph must be complete, acyclic, unforked, ordered, and role/PR compatible.

## Finding Lifecycle

A finding is permanently recorded as `OPEN`. Closure is derived, never written back:

1. An `Implementation Repair` record adds a `repair_claims` edge naming the source Gate Record, finding ID, and repaired candidate. This does not close the finding.
2. A later qualified record of the original gate type adds a `rechecks` edge naming the source finding, repair record, candidate, and `PASS` or `FAIL`.
3. Only `PASS` by a recorded agent ID distinct from both originator and implementer closes the finding. Wrong role, wrong candidate, wrong ID, same agent, missing evidence, or failed recheck leaves it blocking.

## Release Reconciliation

Release validation independently:

- queries current GitHub PR comments and parses declarations;
- runs `git ls-remote` against `origin` for the complete PR Gate Record namespace;
- fetches every discovered authoritative object;
- compares PR JSON, declared object SHA, remote ref, stored JSON, candidate parent, and graph;
- rejects omissions, additions, duplicates, mutations, forks, truncation, and source disagreement.

Release embeds the exact active Review, QA, and Security record commit SHAs in its authorization. The integration commit carries `Governance-PR` and `Governance-Authorization` trailers.

No separate manifest is used: without an externally protected anchor, a privileged writer who can delete refs could also delete or repoint a manifest head. Live GitHub-comment plus complete remote-ref reconciliation provides equivalent observable integrity without claiming protection that GitHub Free does not supply.
