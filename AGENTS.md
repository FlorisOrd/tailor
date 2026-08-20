# Repository Guidelines

## Authority and Scope

The product owner defines product outcomes but does not edit, inspect, debug, or maintain code. Codex agents own technical execution. Ask the owner only about choices that materially affect product behavior, UX, branding, business, spending, privacy, legal/compliance matters, or irreversible external actions. Never ask the owner to run commands, resolve conflicts, inspect logs, or debug.

GitHub is the permanent source of truth. Work in isolated branches or worktrees; never commit secrets or populated environment files. Use proven, maintainable approaches and record consequential decisions in `DECISIONS.md`.

## Required Separation of Duties

No agent may be the sole reviewer of its own material implementation. For material work, Implementation, Independent Code Review, QA, and Release must each be assigned to different Codex threads/agents. Use the roles and handoffs in `WORKFLOW.md`: Lead / Engineering Manager, Product / Requirements, Architecture, Implementation, Independent Code Review, QA, UX / Accessibility Review, Security Review, Release, and Operations / Regression Monitoring. Other roles may be combined only when independence and required specialist review are preserved.

## Completion Standard

Follow `PRODUCT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`, `QUALITY.md`, and `SECURITY.md`. Objective evidence—tests, builds, browser checks, accessibility checks, and security checks—takes priority over claims. Material work is incomplete until acceptance criteria are met, independent review findings are resolved, and all applicable quality gates pass.

User-facing changes require browser verification and accessibility consideration. Authentication, authorization, billing, personal data, uploads, external APIs, secrets, and similar sensitive areas require dedicated Security Review. Release only from reviewed, verified work; record evidence and monitor after release.

Report outcomes to the product owner in plain, nontechnical language, including what changed, what was verified, remaining risks, and any owner decision required.
