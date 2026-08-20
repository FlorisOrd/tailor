"""Validate the stack-neutral governance baseline without product assumptions."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "AGENTS.md",
    "PRODUCT.md",
    "ARCHITECTURE.md",
    "WORKFLOW.md",
    "QUALITY.md",
    "SECURITY.md",
    "INCIDENT_RESPONSE.md",
    "DECISIONS.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/GOVERNANCE_ENFORCEMENT.md",
    ".github/dependabot.yml",
    ".github/workflows/governance.yml",
)

REQUIRED_TEXT = {
    "AGENTS.md": (
        "GitHub is the permanent source of truth",
        "Do not commit or push material work directly to `main`",
        "Only Release may authorize a verified candidate",
        "Non-waivable gates",
    ),
    "PRODUCT.md": ("not yet defined", "Approved features: None"),
    "WORKFLOW.md": (
        "Ambiguity defaults to material",
        "BLOCKING",
        "MAJOR",
        "MINOR",
        "SUGGESTION",
        "Every repair or other material change creates a new candidate revision",
    ),
    "QUALITY.md": (
        "canonical commands",
        "automated accessibility",
        "dependency/software-composition",
        "A genuinely inapplicable gate requires a written N/A rationale",
    ),
    "SECURITY.md": (
        "different Codex thread/agent from Implementation, Lead/gate owner, QA, and Release",
        "lockfiles",
        "scheduled rescanning",
    ),
    "INCIDENT_RESPONSE.md": ("Containment", "Recovery", "Postmortem"),
    ".github/GOVERNANCE_ENFORCEMENT.md": (
        "does **not** claim",
        "Not Currently Hard-Enforced",
        "Future Technical Enforcement",
    ),
}

COMMON_DEPENDENCY_MANIFESTS = {
    "package.json": ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml"),
    "pyproject.toml": ("poetry.lock", "uv.lock", "Pipfile.lock"),
    "requirements.txt": (),
    "Cargo.toml": ("Cargo.lock",),
    "go.mod": ("go.sum",),
    "Gemfile": ("Gemfile.lock",),
    "composer.json": ("composer.lock",),
}


def validate_text_file(relative: str, problems: list[str]) -> str:
    path = ROOT / relative
    if not path.is_file():
        problems.append(f"missing required file: {relative}")
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        problems.append(f"not valid UTF-8: {relative}")
        return ""
    if not text.strip():
        problems.append(f"empty required file: {relative}")
    if not text.endswith("\n"):
        problems.append(f"missing final newline: {relative}")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.rstrip() != line:
            problems.append(f"trailing whitespace: {relative}:{number}")
        if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            problems.append(f"merge-conflict marker: {relative}:{number}")
    return text


def validate_action_pins(workflow: str, problems: list[str]) -> None:
    references = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
    if not references:
        problems.append("governance workflow contains no Action references")
    for reference in references:
        if reference.startswith("./"):
            continue
        if not re.search(r"@[0-9a-fA-F]{40}$", reference):
            problems.append(f"Action is not pinned to a full commit SHA: {reference}")


def validate_dependency_readiness(problems: list[str]) -> None:
    for manifest, lockfiles in COMMON_DEPENDENCY_MANIFESTS.items():
        if not (ROOT / manifest).exists() or not lockfiles:
            continue
        if not any((ROOT / lockfile).exists() for lockfile in lockfiles):
            problems.append(
                f"dependency manifest {manifest} exists without a supported integrity lockfile"
            )


def main() -> int:
    problems: list[str] = []
    contents = {
        relative: validate_text_file(relative, problems) for relative in REQUIRED_FILES
    }

    for relative, snippets in REQUIRED_TEXT.items():
        text = contents.get(relative, "")
        for snippet in snippets:
            if snippet.casefold() not in text.casefold():
                problems.append(f"required control text missing from {relative}: {snippet}")

    agents_words = len(re.findall(r"\b[\w'-]+\b", contents.get("AGENTS.md", "")))
    if agents_words > 500:
        problems.append(f"AGENTS.md is not concise ({agents_words} words; maximum 500)")

    workflow = contents.get(".github/workflows/governance.yml", "")
    validate_action_pins(workflow, problems)
    for trigger in ("push:", "pull_request:", "workflow_dispatch:", "schedule:"):
        if trigger not in workflow:
            problems.append(f"governance workflow missing trigger: {trigger}")

    validate_dependency_readiness(problems)

    if problems:
        print("Governance validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Governance validation passed.")
    print("No product build or test commands are defined because no product stack exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
