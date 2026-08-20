"""Validate the canonical structured governance policy and repository wiring."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ".github/governance/policy.json"
REQUIRED_FILES = ("AGENTS.md", "PRODUCT.md", "ARCHITECTURE.md", "WORKFLOW.md", "QUALITY.md", "SECURITY.md", "INCIDENT_RESPONSE.md", "DECISIONS.md", ".github/PULL_REQUEST_TEMPLATE.md", ".github/GOVERNANCE_ENFORCEMENT.md", ".github/dependabot.yml", ".github/workflows/governance.yml", POLICY_PATH, ".github/governance/gate-record.schema.json", ".github/governance/authorization.schema.json", ".github/governance/GATE_RECORDS.md", "scripts/verify_integration.py", "scripts/validate_gate_records.py")
ROLES = {"Implementation", "Independent Code Review", "QA", "Release"}
NON_WAIVABLE = {"GOV-ROLE-SEPARATION", "GOV-SECURITY-INDEPENDENCE", "GOV-EXACT-INTEGRATION", "GOV-GATE-RECORDS", "GOV-STALE-EVIDENCE", "GOV-HIGH-RISK-STAGING", "GOV-OWNER-PROTECTION", "GOV-RELEASE-AUTHORITY", "secret_protection", "blocking_major_recheck"}
OWNER_DOES_NOT = {"edit_code", "run_commands", "resolve_conflicts", "inspect_logs", "debug", "maintain_code"}
HIGH_RISK = {"authentication", "authorization", "billing", "personal_data", "persisted_data_migration", "infrastructure", "deployment_security_boundary", "security_sensitive_behavior"}

def text_file(relative: str, problems: list[str]) -> str:
    path = ROOT / relative
    if not path.is_file(): problems.append(f"missing required file: {relative}"); return ""
    try: text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError: problems.append(f"not valid UTF-8: {relative}"); return ""
    if not text.strip(): problems.append(f"empty required file: {relative}")
    if not text.endswith("\n"): problems.append(f"missing final newline: {relative}")
    for number, line in enumerate(text.splitlines(), 1):
        if line.rstrip() != line: problems.append(f"trailing whitespace: {relative}:{number}")
        if line.startswith(("<<<<<<<", "=======", ">>>>>>>")): problems.append(f"merge marker: {relative}:{number}")
    return text

def require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition: problems.append(message)

def validate_policy(policy: dict[str, object], problems: list[str]) -> None:
    require(policy.get("schema_version") == 1 and policy.get("authority") == "canonical", "policy must be canonical schema version 1", problems)
    material = policy.get("material_work", {}); require(material.get("ambiguity_defaults_to_material") is True and len(material.get("categories", [])) >= 10, "material-work policy is weakened", problems)
    roles = policy.get("roles", {}); require(set(roles.get("required", [])) == ROLES and set(roles.get("mutually_distinct", [])) == ROLES, "Implementation, Review, QA, and Release must be mutually distinct", problems)
    require(set(roles.get("security_distinct_from", [])) == {"Implementation", "Lead / Engineering Manager", "QA", "Release"}, "Security independence is weakened", problems)
    require(set(roles.get("release_only_authorities", [])) == {"Authorization to Merge", "Authorization to Deploy"}, "Release authority is weakened", problems)
    require(NON_WAIVABLE <= set(policy.get("non_waivable_controls", [])), "a required non-waivable control is missing", problems)
    severity = policy.get("severity", {})
    require(set(severity) == {"BLOCKING", "MAJOR", "MINOR", "SUGGESTION"}, "severity taxonomy is incomplete", problems)
    for level in ("BLOCKING", "MAJOR"): require(severity.get(level, {}).get("blocks") is True and severity.get(level, {}).get("requires_independent_recheck") is True, f"{level} disposition is weakened", problems)
    evidence = policy.get("evidence", {}); require(set(evidence.get("formal_gate_types", [])) == {"Independent Code Review", "QA", "Security Review", "Release"} and evidence.get("publisher_must_be_performing_agent") is True and evidence.get("pr_body_is_authoritative") is False, "Gate Record authority is weakened", problems)
    stale = policy.get("stale_evidence", {}); require(all(stale.get(key) is True for key in ("candidate_change_invalidates", "repair_creates_new_candidate", "unaffected_requires_independent_gate_owner_record")), "stale-evidence policy is weakened", problems)
    integration = policy.get("integration", {}); require(integration.get("merge_commit_only") is True and integration.get("parent_count") == 2 and all(integration.get(key) is True for key in ("exact_first_parent_is_authorized_base", "exact_second_parent_is_authorized_candidate", "candidate_tree_equals_authorized_tree", "integration_tree_equals_authorized_tree")) and integration.get("authorization_source") == "immutable_git_authorization_commit", "exact authorized integration policy is weakened", problems)
    staging = policy.get("high_risk_staging", {}); require(staging.get("required") is True and staging.get("non_local") is True and staging.get("isolated") is True and staging.get("local_substitute_allowed") is False and HIGH_RISK <= set(staging.get("categories", [])), "high-risk staging policy is weakened", problems)
    owner = policy.get("owner_boundaries", {}); require(OWNER_DOES_NOT <= set(owner.get("owner_does_not", [])), "owner protection is weakened", problems)
    exceptions = policy.get("exceptions", {}); require(exceptions.get("lead_alone_may_approve") is False and exceptions.get("non_waivable_controls_may_be_excepted") is False, "exception authority is weakened", problems)
    release = policy.get("release", {}); require(all(release.get(key) is True for key in ("release_role_issues_authorization", "authorization_is_candidate_specific", "authorization_requires_current_gate_records", "merge_and_deploy_authorizations_are_separate")), "Release authority is weakened", problems)

def main() -> int:
    problems = []; contents = {path: text_file(path, problems) for path in REQUIRED_FILES}
    try: policy = json.loads(contents.get(POLICY_PATH, ""))
    except json.JSONDecodeError as error: problems.append(f"invalid canonical policy JSON: {error}"); policy = {}
    if isinstance(policy, dict): validate_policy(policy, problems)
    else: problems.append("canonical policy must be a JSON object")
    for schema in (".github/governance/gate-record.schema.json", ".github/governance/authorization.schema.json"):
        try: parsed = json.loads(contents.get(schema, "")); require(parsed.get("additionalProperties") is False, f"{schema} must reject unknown properties", problems)
        except (json.JSONDecodeError, AttributeError) as error: problems.append(f"invalid schema {schema}: {error}")
    for document in ("AGENTS.md", "WORKFLOW.md", "QUALITY.md", "SECURITY.md"):
        require(POLICY_PATH in contents.get(document, ""), f"{document} must identify the canonical policy", problems)
    workflow = contents.get(".github/workflows/governance.yml", "")
    for reference in re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE): require(reference.startswith("./") or re.search(r"@[0-9a-fA-F]{40}$", reference) is not None, f"Action is not pinned: {reference}", problems)
    for command in ("scripts/validate_governance.py", "unittest discover", "scripts/verify_integration.py"): require(command in workflow, f"workflow missing required factory check: {command}", problems)
    words = len(re.findall(r"\b[\w'-]+\b", contents.get("AGENTS.md", ""))); require(words <= 500, f"AGENTS.md exceeds 500 words ({words})", problems)
    if problems: print("Governance validation failed:"); [print(f"- {problem}") for problem in problems]; return 1
    print("Governance validation passed.\nCanonical policy relationships and factory wiring verified."); return 0

if __name__ == "__main__": sys.exit(main())
