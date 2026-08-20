# Engineering Workflow

Critical controls are authoritative in `.github/governance/policy.json`. This document explains their operation and must not contradict that structured policy. Stable IDs include `GOV-ROLE-SEPARATION`, `GOV-SECURITY-INDEPENDENCE`, `GOV-GATE-RECORDS`, `GOV-STALE-EVIDENCE`, and `GOV-EXACT-INTEGRATION`.

## Operating Roles

- **Lead / Engineering Manager:** plans work, assigns independent roles, tracks risks and gate state, and communicates with the owner. The Lead cannot waive gates or act as Security Review.
- **Product / Requirements:** converts owner intent into bounded scope and testable acceptance criteria.
- **Architecture:** selects maintainable approaches and records consequential decisions.
- **Implementation:** builds on an isolated branch/worktree, adds tests, and identifies the candidate revision.
- **Independent Code Review:** reviews the complete candidate diff for requirements, correctness, maintainability, tests, and risk.
- **QA:** independently tests acceptance criteria, failures, regressions, and applicable browser behavior.
- **UX / Accessibility Review:** independently evaluates user-facing flows, content, responsiveness, keyboard use, focus, semantics, contrast, zoom, and motion.
- **Security Review:** performs the dedicated review required by `SECURITY.md`.
- **Release:** independently confirms the evidence record, issues separate Authorization to Merge and Authorization to Deploy decisions, and verifies integration, staging, and rollback readiness.
- **Operations / Regression Monitoring:** observes release health, routes alerts, records verification, and initiates rollback or repair.

For the same material change, Implementation, Independent Code Review, QA, and Release must each be a different Codex thread/agent. No thread may occupy more than one of those four roles. Therefore every pair is separated: Implementation from Independent Code Review, QA, and Release; Independent Code Review from QA and Release; and QA from Release. These separations are non-waivable.

For security-triggered work, Security Review must additionally be a different thread/agent from Implementation, Lead/gate authority, QA, and Release. Security-relevant repairs must return to the independent Security reviewer. These Security separations and recheck are non-waivable. Other roles may combine only when this governance does not require their independence.

## Material Work Classification

Material work includes, at minimum: application code; configuration; dependencies and lockfiles; database or schema changes; infrastructure; deployment configuration; governance; security behavior; user-facing behavior; APIs; authentication or authorization; data handling; build/test tooling; and release-affecting changes. Ambiguity defaults to material.

Work may be classified non-material only when it cannot affect behavior, risk, verification, release, or governance (for example, a typo-only correction). If that classification bypasses a gate, a non-implementing role must approve it in the durable work record before merge. Classification does not override any non-waivable gate.

## Change Control and Lifecycle

Agents must not routinely commit or push directly to `main`; material work must never do so. Use a feature branch or isolated worktree. A GitHub pull request is the normal durable review record. If GitHub cannot host a PR, use a versioned equivalent record linked from GitHub and explain the limitation.

Product request → acceptance criteria → isolated implementation → candidate synchronized with `main` → final candidate verification → Authorization to Merge → deterministic integration → integration/tree verification and CI → representative staging verification → Authorization to Deploy → production release → post-release monitoring.

Independent Code Review, automated checks, QA/browser/accessibility checks, and Security Review where triggered verify one exact candidate commit SHA. Every repair or other material change creates a new candidate revision and invalidates affected approvals and evidence. Each affected gate must be rerun; alternatively, its independent owner may record why it is unaffected. Release rejects missing, stale, or self-attested evidence.

### Durable Gate Records

Every formal gate agent publishes its own candidate-specific Bootstrap v0 Gate Record using `.github/governance/GATE_RECORDS.md`. Release explicitly selects one current Review, QA, Security, and Release record and validates its exact PR/base/candidate/tree, immutable object/ref, PR-visible copy, PASS disposition, findings, freshness, and recorded-agent separation. Lead transcription and historical evidence cannot satisfy a current gate.

A BLOCKING or MAJOR finding produces FAIL. Repair creates a new candidate and invalidates earlier candidate-specific evidence. The complete new candidate receives fresh independent verification; Bootstrap v0 does not derive approval from a historical finding graph.

`main` changes require a PR or equivalent durable review record before becoming authoritative. The exact-candidate integration protocol below is procedural on the current GitHub plan; `.github/GOVERNANCE_ENFORCEMENT.md` records the lack of hard enforcement.

## Exact-Candidate Integration Protocol

### A. Candidate Creation

Before final verification, update the candidate branch with the latest remote `main` without rewriting reviewed history. Record the base/main commit SHA, candidate commit SHA, and candidate tree hash. The recorded base must be an ancestor of the candidate, the candidate must have no unresolved conflicts or divergence from that base, and remote `main` must still equal the recorded base when final verification begins.

Useful identity commands are `git rev-parse <ref>`, `git rev-parse <ref>^{tree}`, `git merge-base --is-ancestor <base> <candidate>`, and `git rev-list --left-right --count <base>...<candidate>`. Record results in the PR; do not ask the product owner to run them.

### B. Final Candidate Verification

Independent Code Review, QA, triggered Security Review, automated checks, and other applicable gates verify the recorded candidate SHA. Evidence names that SHA. After final verification begins, a repair or material change creates a new candidate and invalidates affected evidence under the stale-evidence rule. Immediately before merge authorization, Release fetches remote state and confirms `main` still equals the recorded base.

### C. Authorization to Merge

Release may issue **AUTHORIZATION TO MERGE** only when agent-published Gate Records are complete and current. Release publishes its own PASS Gate Record, then creates an immutable Git authorization commit containing `.github/governance/authorization.json` and publishes it under `refs/governance/authorizations/pr-<number>/<candidate-sha>`. It records exact PR, base, candidate, tree, timestamp, Release identity, and Release Gate Record ID. Before authorization, the verifier fails closed unless the open, unmerged GitHub PR and freshly queried `origin` `main` and candidate refs match that exact tuple. It authorizes only that tuple and is not authorization to deploy.

### D. Deterministic Integration

Governed material changes use **MERGE COMMIT ONLY** with fast-forward, squash, and rebase merging prohibited. The integration message contains exactly one `Governance-PR: <pr>` and one `Governance-Authorization: <sha>` trailer. The verifier derives the only valid authorization ref from the record's PR and candidate, requires exact ref equality, validates the authorized Gate Record objects, and checks exact parents and trees. Namespace membership and ancestry never substitute for equality.

GitHub Free cannot prove which Codex process authored a comment/commit, map textual `agent_id` to a physically distinct process, enforce separate credentials, or prove a privileged writer never deleted/repointed evidence before observation. It can verify observed commits, trees, objects, refs, graph relationships, and current GitHub/remote consistency. These identity and pre-observation deletion limits remain explicit.

After merge, record the integration/main commit SHA and tree hash. Verify its parent identities and verify that its tree hash exactly equals the approved candidate tree hash. A different tree, parents, or base condition blocks deployment and requires appropriate renewed verification; never rationalize the mismatch as merge-only metadata.

### E. Authorization to Deploy

After integration, run required CI on the integration commit and verify staging/pre-release evidence for the integrated revision. Release may issue **AUTHORIZATION TO DEPLOY** only after recording the integration SHA/tree, proving tree equality with the candidate, confirming base/parent conditions, confirming required evidence remains valid, and rejecting stale approvals. Production may deploy only the authorized integration revision/artifact.

### F. Durable Release Record

The PR record contains: base SHA; candidate SHA and tree hash; final-verification evidence; Authorization to Merge; integration/main SHA and tree hash; parent/base and tree-equality results; post-integration CI and staging evidence; evidence invalidation/reruns; and Authorization to Deploy.

## Shared Finding Severity

- **BLOCKING:** immediate safety, security, data, correctness, compliance, or release-integrity risk; repair is mandatory before approval or release.
- **MAJOR:** material requirement, reliability, maintainability, accessibility, or control failure; repair is mandatory before approval or release.
- **MINOR:** bounded issue that does not block safe use; repair it or record tracked debt with an accountable owner and target date.
- **SUGGESTION:** optional improvement; record its disposition when raised in a formal review.

BLOCKING and MAJOR repairs must be independently rechecked by the role that raised them or an equally independent qualified role. Security-relevant repairs must be rechecked by Security Review.

## Exceptions and Non-Waivable Gates

The canonical non-waivable gates are:

1. Implementation, Independent Code Review, QA, and Release are four different threads/agents for the same material change; no thread occupies two roles.
2. Triggered Security Review is independent from Implementation, Lead/gate authority, QA, and Release, and Security rechecks security-relevant repairs.
3. Secret protection.
4. Repair and independent recheck of every BLOCKING and MAJOR finding.
5. Exact candidate/base/tree identity, deterministic integration, integration tree/parent verification, stale-evidence handling, and required-evidence integrity.
6. Separate Authorization to Merge and Authorization to Deploy decisions issued only by Release.
7. Representative non-local isolated pre-production verification before a high-risk production release as defined below.

No exception may waive these gates. Any other temporary exception requires a written justification, risk and compensating controls, independent concurrence, relevant specialist concurrence, Release concurrence, expiry date, and durable PR record. The Lead alone cannot waive a gate. Owner approval is additionally required when an exception crosses the decision boundaries in `PRODUCT.md`.

## Staging and Pre-Release Verification

Staging or the pre-release environment must verify the integrated revision/artifact authorized for possible production use and materially match production runtime, configuration shape, integrations or faithful test doubles, data/schema version, access boundaries, observability, and deployment path. Candidate-only evidence may inform testing but cannot replace required post-integration identity and staging checks.

Before the first high-risk production release, the repository must establish a representative **non-local isolated pre-production environment**. This non-waivable capability applies to authentication, authorization, billing/payments, personal data, database/schema migrations affecting persisted data, infrastructure changes, deployment/security boundary changes, and other security-sensitive behavior. A developer machine or purely local substitute never satisfies it. No staging platform is required before a product or high-risk release exists, but Release cannot mark such a production release complete without this capability and evidence.

Exact parity details may differ only when production parity is impossible. Record each difference, assess its risk, obtain independent Security approval when security-relevant, obtain Release acceptance, and add compensating verification where appropriate. These controlled parity differences do not waive the representative non-local environment itself.

Minimum smoke checks are: deployed revision identity; startup and health; critical route or workflow; configuration and secret injection without disclosure; persistence/migration compatibility where applicable; external-boundary behavior; error and recovery path; authorization boundary where applicable; logging/metrics/alerts; and rollback or roll-forward execution evidence.

## Release, Rollback, and Monitoring

Release readiness is demonstrable, not a statement of intent. Where applicable, the PR record must contain a revision-specific rollback or roll-forward procedure; migration and backward-compatibility assessment; backup/restore compatibility; named health signals and thresholds; observation window; alert route and accountable Operations role; rollback triggers; and post-release verification result.

Failed gates return work to the appropriate role. Agents resolve technical failures themselves and ask the owner only when a decision crosses `PRODUCT.md` boundaries. Incidents follow `INCIDENT_RESPONSE.md`.

REVIEW-05 through REVIEW-08 and their published objects/refs remain unchanged audit evidence for superseded candidates and regression-test context. They are not normalized or used as current Release prerequisites.
