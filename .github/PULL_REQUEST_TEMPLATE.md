# Work Record

> This GitHub pull request is the durable evidence record. Do not paste secrets, exploit details, or unnecessary personal data. Every repair or material change creates a new candidate; update its identity and rerun affected evidence or obtain an independent unaffected determination.

## Scope and Classification

- Work item / request:
- Material: Yes / No
- If No, reason and non-implementer concurrence (required when bypassing a gate):
- Product-owner decisions or approvals (link only when required):

## Acceptance Criteria

- [ ] Criterion 1:
- [ ] Criterion 2:
- Out of scope:

## Candidate

- Branch:
- Recorded current `main` / base commit SHA:
- Exact candidate commit SHA:
- Candidate tree hash:
- Base-is-ancestor result:
- Candidate divergence/conflict result:
- Final pre-authorization remote `main` SHA check:
- Implementation agent/thread:
- Summary of material changes after prior evidence, or `None`:

## Independent Roles

The table is a summary only. Each formal gate agent must publish its own schema-valid JSON Gate Record in a fenced `gate-record` PR comment; record the immutable comment link and Gate Record ID below. Lead transcription is not evidence.

| Gate | Agent/thread or durable review link | Candidate SHA | Disposition |
| --- | --- | --- | --- |
| Independent Code Review |  |  | Pending |
| QA |  |  | Pending |
| UX / Accessibility (or approved N/A) |  |  | Pending |
| Security Review (or trigger assessment) |  |  | Pending |
| Release |  |  | Pending |

- Independent Review Gate Record ID/comment:
- QA Gate Record ID/comment:
- Security Gate Record ID/comment:
- Release Gate Record ID/comment:
- Gate Record validator command/result:
- Content-addressed Gate Record commit SHAs and exact canonical refs:
- PR-comment JSON equals stored Gate Record JSON:
- Complete live GitHub-comment / `origin` remote-ledger reconciliation:
- Append-only repair claims and distinct independent recheck edges:
- Unresolved historical BLOCKING/MAJOR finding inventory:

- [ ] Implementation, Independent Code Review, QA, and Release are four different threads/agents; no thread occupies more than one role.
- [ ] If Security is triggered, Security Review is separate from Implementation, Lead/gate authority, QA, and Release.
- [ ] Required role separations are treated as non-waivable; no exception combines these roles.

## Automated and Manual Evidence

| Check | Command / procedure and environment | Candidate SHA | Result / artifact link |
| --- | --- | --- | --- |
| Format / lint |  |  |  |
| Static / type |  |  |  |
| Unit |  |  |  |
| Integration |  |  |  |
| Production build |  |  |  |
| Browser / end-to-end |  |  |  |
| Accessibility automation |  |  |  |
| Secret scan |  |  |  |
| Dependency / SCA |  |  |  |

For each N/A: record the reason and non-implementer concurrence. A blank cell is not N/A.

## Findings and Debt

| Severity | Finding | Disposition | Independent recheck / debt owner and target date |
| --- | --- | --- | --- |
|  |  |  |  |

- [ ] All BLOCKING and MAJOR findings were repaired and independently rechecked.
- [ ] Each MINOR finding was repaired or accepted as tracked debt with owner and target date.
- [ ] Each formal-review SUGGESTION has a recorded disposition.

## UX / Accessibility

- Visual or user-flow effect: Yes / No
- Browser/viewports:
- Keyboard and visible-focus result:
- Zoom/reflow/responsiveness result:
- Automated accessibility result:
- Screenshots/recording links, or independently approved N/A reasoning:

## Security

- Security trigger(s), or reason none apply:
- Threat/data-boundary summary:
- Secret and dependency scan disposition:
- Security-relevant repairs and Security recheck:
- [ ] Every security-relevant repair returned to the independent Security reviewer.

## Authorization to Merge

- [ ] Release confirms candidate evidence is complete, current, and tied to the recorded candidate/base/tree.
- [ ] Remote `main` still equals the recorded base.
- Release agent/thread:
- Decision and date:
- Candidate SHA/tree authorized for merge:
- Recorded base SHA authorized for merge:
- Authorization record ID:
- Immutable authorization commit SHA:
- Published authorization ref (`refs/governance/authorizations/pr-<number>/<candidate-sha>`):
- Authorization record exact PR/base/candidate/tree/timestamp/Release identity validation:
- Required integration trailer (`Governance-Authorization: <authorization-commit-sha>`):
- Required PR trailer (`Governance-PR: <pr-number>`):
- Exact Review/QA/Security Gate Record commit identities embedded in authorization:

## Integration Record

- Integration/main commit SHA:
- Integration tree hash:
- Integration parent SHAs:
- [ ] Integration parents equal the authorized base and candidate.
- [ ] Integration tree hash exactly equals the authorized candidate tree hash.
- Post-integration CI/check evidence:
- Evidence invalidated, rerun, or independently determined unaffected:
- Exact authorized-tuple verifier result (authorization/base/candidate/tree/integration equality):

## Staging and Smoke Verification

- Environment and production-parity differences:
- Exact deployed integration revision/artifact identity:
- Startup/health and critical-flow result:
- Configuration/secrets, external boundaries, authorization, persistence/migration, errors/recovery, and observability results as applicable:
- High-risk category or reason not triggered:
- Representative non-local isolated pre-production evidence for high-risk work:
- [ ] If high-risk, a purely local environment did not substitute and the representative environment requirement was not waived.
- Security approval of security-relevant parity differences:
- Release acceptance of parity differences and compensating verification:

## Release Readiness and Monitoring

- Revision-specific rollback or roll-forward procedure and execution evidence:
- Migration/backward-compatibility and backup/recovery compatibility:
- Health signals and thresholds:
- Observation window:
- Alert route / Operations owner:
- Rollback triggers:
- Unresolved lower-severity debt:

## Authorization to Deploy

- [ ] Release confirms all pre-deployment portions of this record are complete, integration identity is verified, required CI and staging evidence applies to the integration revision, and no stale approval is relied upon.
- Release agent/thread:
- Decision and date:
- Authorized integration/main SHA and artifact:

## Post-Release Monitoring

- Exact deployed integration SHA/artifact:
- Observation start/end:
- Health signals and threshold results:
- Alerts, regressions, or rollback decision:
- Recorded post-release verification and Operations disposition:
