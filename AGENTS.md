# Repository Guidelines

## Authority and Scope

The product owner defines product outcomes but does not edit, inspect, debug, or maintain code. Codex agents own technical execution. Ask the owner only about decisions that materially affect product behavior, UX, branding, business, spending, privacy, legal/compliance matters, or irreversible external actions. Never ask the owner to run commands, resolve conflicts, inspect logs, or debug.

GitHub is the permanent source of truth. Never commit secrets or populated environment files. Use proven, maintainable approaches and record consequential decisions in `DECISIONS.md`.

The authoritative policy is `.github/governance/policy.json`. Gate evidence is append-only matching PR JSON plus immutable Git objects. Repairs never self-close findings; a qualified distinct recorded agent must recheck them. Release independently reconciles live GitHub comments with `origin`'s complete PR evidence namespace. Pre-protocol evidence uses the allowlisted provenance-only binding process; migration is never approval. A summary, mutable comment alone, or local ref subset is never proof.

## Change Control

Treat work as material by default; `WORKFLOW.md` defines the minimum scope. Material changes must use an isolated branch/worktree and a GitHub pull request or equivalent durable review record. Do not commit or push material work directly to `main`.

Before final verification, update the candidate with current `main` and record the base SHA, candidate SHA, and candidate tree hash. Review and tests apply to that candidate. Every repair or other material change creates a new candidate and invalidates affected approvals and evidence. Release alone issues separate **Authorization to Merge** and **Authorization to Deploy** decisions. Governed material work uses a merge commit; after integration, verify the main commit tree equals the candidate tree and that the recorded base remained current. A mismatch or moved base blocks deployment and requires renewed verification under `WORKFLOW.md`.

## Separation and Gates

For the same material change, Implementation, Independent Code Review, QA, and Release must each be a different Codex thread/agent; no thread may hold more than one of these roles. Triggered Security Review must additionally be separate from Implementation, Lead/gate authority, QA, and Release, and Security must recheck security-relevant repairs. These separations are non-waivable.

Follow `PRODUCT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`, `QUALITY.md`, `SECURITY.md`, and `INCIDENT_RESPONSE.md`. Objective evidence takes priority over claims. The canonical non-waivable gates are: the role separations above; triggered Security Review and Security recheck; secret protection; repair and independent recheck of BLOCKING/MAJOR findings; exact candidate/base/tree and integration verification; both Release authorizations; required-evidence integrity; and representative non-local isolated pre-production verification before any high-risk production release defined in `WORKFLOW.md`. No exception may waive them.

User-facing visual or flow changes require browser, UX/accessibility, keyboard, zoom/responsiveness, and appropriate automated accessibility checks. Sensitive areas listed in `SECURITY.md` require dedicated Security Review. Work is incomplete while a required gate fails or evidence is stale.

Keep evidence in the GitHub pull request using `.github/PULL_REQUEST_TEMPLATE.md`, not only in chat. Report outcomes to the owner in plain language: what changed, what was verified, remaining risks, and any owner decision required.
