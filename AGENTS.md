# Repository Guidelines

## Authority and Scope

The product owner defines product outcomes but does not edit, inspect, debug, or maintain code. Codex agents own technical execution. Ask the owner only about decisions that materially affect product behavior, UX, branding, business, spending, privacy, legal/compliance matters, or irreversible external actions. Never ask the owner to run commands, resolve conflicts, inspect logs, or debug.

GitHub is the permanent source of truth. Never commit secrets or populated environment files. Use proven, maintainable approaches and record consequential decisions in `DECISIONS.md`.

## Change Control

Treat work as material by default; `WORKFLOW.md` defines the minimum scope. Material changes must use an isolated branch/worktree and a GitHub pull request or equivalent durable review record. Do not commit or push material work directly to `main`. The exact final candidate revision must be the revision reviewed and verified. Every repair or other material change creates a new candidate and invalidates affected approvals and evidence until an independent role reruns them or records why they are unaffected. Only Release may authorize a verified candidate for release.

## Separation and Gates

For material work, Implementation, Independent Code Review, QA, and Release must each be different Codex threads/agents. Triggered Security Review must also be separate from those roles and the Lead. No agent may be the sole reviewer of its own work.

Follow `PRODUCT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`, `QUALITY.md`, `SECURITY.md`, and `INCIDENT_RESPONSE.md`. Objective evidence takes priority over claims. Non-waivable gates include role separation, triggered Security Review, secret protection, disposition and recheck of BLOCKING/MAJOR findings, exact-revision verification, Release authorization, and evidence integrity.

User-facing visual or flow changes require browser, UX/accessibility, keyboard, zoom/responsiveness, and appropriate automated accessibility checks. Sensitive areas listed in `SECURITY.md` require dedicated Security Review. Work is incomplete while a required gate fails or evidence is stale.

Keep evidence in the GitHub pull request using `.github/PULL_REQUEST_TEMPLATE.md`, not only in chat. Report outcomes to the owner in plain language: what changed, what was verified, remaining risks, and any owner decision required.
