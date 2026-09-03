# Tailor

**An experimental governance framework for reliable software development with coding agents.**

Tailor explores how teams can avoid accepting plausible agent-generated work without sufficient evidence. It separates implementation, independent review, QA, security and release responsibilities; binds evidence to exact candidate versions; and preserves explicit human authority over consequential product and release decisions.

The repository currently contains a frozen governance foundation, machine-readable policy, evidence schemas, validation scripts, regression tests and GitHub Actions checks. It does not yet define a product audience, feature set, technology stack or deployment target, and it should not be treated as a completed commercial product.

## What the framework defines

- **Role separation.** Implementation, Independent Code Review, QA and Release are distinct roles for the same material change. Security Review is additionally independent when triggered.
- **Candidate-specific evidence.** Gate records identify the pull request, base commit, candidate commit and candidate tree rather than approving a moving branch or a narrative claim.
- **Stale-evidence handling.** A material repair creates a new candidate and invalidates affected evidence; the complete new candidate receives fresh independent verification.
- **Separate release decisions.** Authorization to Merge and Authorization to Deploy are different decisions tied to exact revisions and evidence.
- **Deterministic integration checks.** The workflow records and verifies candidate/base identities, merge parents and candidate/integration tree equality.
- **Human authority.** Product behaviour, privacy, legal/compliance commitments, spending, vendors, public launch and other consequential choices remain with the product owner.

The canonical structured controls live in [`.github/governance/policy.json`](.github/governance/policy.json). The [Gate Records protocol](.github/governance/GATE_RECORDS.md) describes how independent roles publish candidate-specific evidence.

## Delivery lifecycle

The intended path is:

1. Record the problem, scope, acceptance criteria and owner-controlled constraints.
2. Implement in an isolated branch or worktree.
3. Synchronize and identify the exact base, candidate commit and candidate tree.
4. Run independent review, QA, applicable security/accessibility checks and automated validation against that candidate.
5. Issue a candidate-specific Authorization to Merge, integrate with the prescribed merge shape and verify the integrated tree.
6. Verify the integrated revision in an appropriate pre-release environment before a separate Authorization to Deploy.

A claim that work is complete is not evidence. Missing, stale, ambiguous or mismatched required evidence fails closed under the documented process.

## Current verification

The repository's current baseline can be checked with:

```bash
python3 scripts/validate_governance.py
python3 -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions also runs governance validation, Bootstrap v0 regression tests, Gitleaks secret scanning, candidate identity checks and post-integration identity checks where applicable.

## Documentation map

- [Product definition and owner authority](PRODUCT.md)
- [Architecture governance](ARCHITECTURE.md)
- [Engineering workflow](WORKFLOW.md)
- [Quality gates](QUALITY.md)
- [Security governance](SECURITY.md)
- [Incident response](INCIDENT_RESPONSE.md)
- [Decision log](DECISIONS.md)
- [GitHub enforcement status](.github/GOVERNANCE_ENFORCEMENT.md)

These documents and the structured policy are the source of truth. This README is an orientation layer, not a replacement for them.

## What GitHub evidence can and cannot prove

The framework can inspect observed commits, trees, refs, ancestry, pull-request state, workflow identity and current agreement between evidence sources. Content-addressed objects and exact refs make mutation or substitution detectable when observed.

GitHub cannot by itself prove that textual agent identities correspond to physically separate processes, that different roles used separate credentials, or that a privileged writer never deleted or repointed evidence before observation. On the current private GitHub Free repository, branch protection and required status checks are not claimed as hard-enforced controls; documented procedural controls and CI report violations but cannot make every prohibited action technically impossible.

## Current status and limitations

- This is a research and governance prototype, not a production software product.
- No user-facing product, stack, runtime, database, service or deployment is currently approved.
- The governance model has not demonstrated quantified performance or defect-prevention improvements.
- Process independence is procedural rather than cryptographically guaranteed.
- The current Bootstrap Governance v0 scope is repository bootstrap; reusable orchestration and generalized factory capabilities are explicitly deferred.
- Formal compliance, production readiness and universal applicability are not claimed.

## My role and development approach

I designed the requirements, governance model, role boundaries, evidence lifecycle, acceptance criteria and release logic. I used coding agents to explore, implement and review parts of the framework while retaining responsibility for consequential decisions and final risk acceptance.
