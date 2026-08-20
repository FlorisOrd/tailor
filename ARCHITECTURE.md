# Architecture Governance

## Current State

No product architecture or technology stack has been selected. Architecture work begins only after sufficient product requirements exist. Do not add frameworks, services, hosting, databases, or paid dependencies speculatively.

## Principles

Architecture decisions should favor:

- the simplest design that satisfies confirmed requirements;
- well-supported, maintainable technologies with clear ownership;
- modular boundaries, explicit interfaces, and reversible choices;
- secure defaults, least privilege, and minimal data collection;
- automated testing, observability, accessibility, and operability;
- reproducible local, CI, staging, and production behavior;
- graceful failure and documented recovery paths;
- low vendor lock-in unless a documented benefit justifies it.

Dependencies must have a clear purpose, acceptable license, active maintenance, and proportionate supply-chain risk. Avoid custom infrastructure when a stable, economical standard solution is sufficient.

## Architecture Role

Architecture translates approved requirements into technical boundaries and identifies consequential choices before Implementation begins. It may decide routine implementation details autonomously. It must escalate choices that affect product behavior, meaningful cost, privacy, compliance, vendor commitments, or irreversible external state.

Architecture review is required for new runtimes or frameworks, persistence models, deployment topology, external services, trust boundaries, public APIs, cross-cutting migrations, and changes that are costly to reverse.

Bootstrap Governance v0 is intentionally limited to this repository's frozen governance foundation. Reusable orchestration, project profiles, generalized evidence lifecycles, and version migration belong in the future `agent-software-factory` repository, which starts with a uniform protocol from genesis.

## Decision Records

Record consequential decisions in `DECISIONS.md` before or alongside implementation. Each record includes context, decision, rationale, alternatives, consequences, status, date, and evidence or follow-up. Supersede earlier records rather than deleting history.

Diagrams belong in `docs/architecture/` when prose cannot clearly show system boundaries or data flow. Keep diagrams version-controlled and update them with the affected decision.
