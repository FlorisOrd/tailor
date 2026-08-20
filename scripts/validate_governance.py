"""Validate the canonical structured governance policy and repository wiring."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ".github/governance/policy.json"
REQUIRED_FILES = ("AGENTS.md", "PRODUCT.md", "ARCHITECTURE.md", "WORKFLOW.md", "QUALITY.md", "SECURITY.md", "INCIDENT_RESPONSE.md", "DECISIONS.md", ".github/PULL_REQUEST_TEMPLATE.md", ".github/GOVERNANCE_ENFORCEMENT.md", ".github/dependabot.yml", ".github/workflows/governance.yml", POLICY_PATH, ".github/governance/gate-record.schema.json", ".github/governance/authorization.schema.json", ".github/governance/GATE_RECORDS.md", "scripts/verify_integration.py", "scripts/validate_gate_records.py", "scripts/validate_evidence.py")
ROLES = {"Implementation", "Independent Code Review", "QA", "Release"}
NON_WAIVABLE = {"GOV-ROLE-SEPARATION", "GOV-SECURITY-INDEPENDENCE", "GOV-EXACT-INTEGRATION", "GOV-GATE-RECORDS", "GOV-STALE-EVIDENCE", "GOV-HIGH-RISK-STAGING", "GOV-OWNER-PROTECTION", "GOV-RELEASE-AUTHORITY", "secret_protection", "blocking_major_recheck"}
OWNER_DOES_NOT = {"edit_code", "run_commands", "perform_git_operations", "resolve_conflicts", "inspect_logs", "interpret_logs", "debug", "maintain_code"}
HIGH_RISK = {"authentication", "authorization", "billing", "personal_data", "persisted_data_migration", "infrastructure", "deployment_security_boundary", "security_sensitive_behavior"}
RECORD_FIELDS = {"schema_version", "gate_record_id", "gate_type", "agent_role", "agent_id", "pr_number", "base_sha", "candidate_sha", "candidate_tree", "timestamp", "scope", "checks", "findings", "repair_claims", "rechecks", "disposition", "repository_state_changed", "supersedes"}
FINDING_FIELDS = {"finding_id", "severity", "summary", "status"}
REPAIR_FIELDS = {"source_gate_record_id", "source_finding_id", "repaired_candidate_sha", "summary"}
RECHECK_FIELDS = {"source_gate_record_id", "source_finding_id", "repair_gate_record_id", "rechecked_candidate_sha", "outcome"}
AUTH_FIELDS = {"schema_version", "authorization_id", "pr_number", "base_sha", "candidate_sha", "candidate_tree", "timestamp", "release_agent_id", "release_gate_record_id", "gate_record_commits"}
RELEASE_IDENTITY = {"base_sha", "candidate_sha", "candidate_tree", "authorization_commit_sha", "canonical_authorization_ref", "integration_sha", "integration_tree"}
POLICY_KEYS = {"schema_version", "authority", "control_ids", "material_work", "roles", "non_waivable_controls", "severity", "evidence", "stale_evidence", "integration", "high_risk_staging", "owner_boundaries", "exceptions", "release", "finding_policy"}

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
    require(set(policy) == POLICY_KEYS, "policy top-level fields do not match the fail-closed contract", problems)
    require(policy.get("schema_version") == 1 and policy.get("authority") == "canonical", "policy must be canonical schema version 1", problems)
    controls=policy.get("control_ids",{}); require(set(controls.values()) >= {item for item in NON_WAIVABLE if item.startswith("GOV-")}, "stable critical control IDs are incomplete", problems)
    material = policy.get("material_work", {}); require(set(material)=={"ambiguity_defaults_to_material","categories"} and material.get("ambiguity_defaults_to_material") is True and len(material.get("categories", [])) >= 10, "material-work policy is weakened", problems)
    roles = policy.get("roles", {}); require(set(roles)=={"required","mutually_distinct","security_distinct_from","release_only_authorities"} and set(roles.get("required", [])) == ROLES and set(roles.get("mutually_distinct", [])) == ROLES, "Implementation, Review, QA, and Release must be mutually distinct", problems)
    require(set(roles.get("security_distinct_from", [])) == {"Implementation", "Lead / Engineering Manager", "QA", "Release"}, "Security independence is weakened", problems)
    require(set(roles.get("release_only_authorities", [])) == {"Authorization to Merge", "Authorization to Deploy"}, "Release authority is weakened", problems)
    require(NON_WAIVABLE <= set(policy.get("non_waivable_controls", [])), "a required non-waivable control is missing", problems)
    severity = policy.get("severity", {})
    require(set(severity) == {"BLOCKING", "MAJOR", "MINOR", "SUGGESTION"}, "severity taxonomy is incomplete", problems)
    for level in ("BLOCKING", "MAJOR"): require(severity.get(level, {}).get("blocks") is True and severity.get(level, {}).get("requires_independent_recheck") is True, f"{level} disposition is weakened", problems)
    require(severity.get("MINOR",{}).get("requires_debt_owner_and_target") is True and severity.get("SUGGESTION",{}).get("requires_disposition") is True, "lower-severity disposition is weakened", problems)
    evidence = policy.get("evidence", {}); require(set(evidence)=={"formal_gate_types","publisher_must_be_performing_agent","pr_body_is_authoritative","candidate_identity_fields","required_gate_record_fields","required_finding_fields","required_repair_claim_fields","required_recheck_fields","finding_severities","finding_statuses","append_only_graph","finding_lifecycle","content_addressing","live_reconciliation"} and set(evidence.get("formal_gate_types", [])) == {"Independent Code Review", "QA", "Security Review", "Release"} and evidence.get("publisher_must_be_performing_agent") is True and evidence.get("pr_body_is_authoritative") is False, "Gate Record authority is weakened", problems)
    require(set(evidence.get("candidate_identity_fields",[]))=={"base_sha","candidate_sha","candidate_tree"}, "Gate Record candidate identity fields are incomplete", problems)
    require(set(evidence.get("required_gate_record_fields",[]))==RECORD_FIELDS, "required Gate Record fields are incomplete", problems)
    require(set(evidence.get("required_finding_fields",[]))==FINDING_FIELDS and set(evidence.get("required_repair_claim_fields",[]))==REPAIR_FIELDS and set(evidence.get("required_recheck_fields",[]))==RECHECK_FIELDS and set(evidence.get("finding_severities",[]))=={"BLOCKING","MAJOR","MINOR","SUGGESTION"} and set(evidence.get("finding_statuses",[]))=={"OPEN"}, "finding schema contract is incomplete", problems)
    graph=evidence.get("append_only_graph",{}); require(all(graph.get(key) is True for key in ("backward_edges_only","predecessor_never_mutated","acyclic","no_forks","same_gate_type_for_supersession","same_pr","ordered_timestamp","missing_predecessor_fails")), "append-only evidence graph is weakened", problems)
    lifecycle=evidence.get("finding_lifecycle",{}); require(all(lifecycle.get(key) is True for key in ("repair_claim_does_not_close","closure_requires_distinct_rechecker","closure_requires_exact_source_finding","closure_requires_repaired_candidate","failed_recheck_remains_open","wrong_role_cannot_recheck")), "finding lifecycle is weakened", problems)
    addressing=evidence.get("content_addressing",{}); require(addressing.get("required") is True and addressing.get("storage")=="immutable_git_commit" and addressing.get("canonical_ref_prefix")=="refs/governance/gate-records/" and addressing.get("comment_must_match_stored_json") is True and addressing.get("commit_parent_is_candidate") is True, "Gate Record content-addressing is weakened", problems)
    live=evidence.get("live_reconciliation",{}); require(all(live.get(key) is True for key in ("github_pr_comments_required","complete_remote_ref_discovery","origin_queried_at_validation_time","local_ref_subset_not_authoritative","source_disagreement_fails","missing_history_fails")), "live evidence reconciliation is weakened", problems)
    stale = policy.get("stale_evidence", {}); require(set(stale)=={"candidate_change_invalidates","repair_creates_new_candidate","unaffected_requires_independent_gate_owner_record"} and all(stale.get(key) is True for key in stale), "stale-evidence policy is weakened", problems)
    integration = policy.get("integration", {}); require(set(integration)=={"merge_commit_only","parent_count","exact_first_parent_is_authorized_base","exact_second_parent_is_authorized_candidate","candidate_tree_equals_authorized_tree","integration_tree_equals_authorized_tree","authorization_source","authorization_ref_prefix","integration_trailer","pr_trailer","authorization_required_fields","canonical_ref_must_equal_authorization","authorization_commit_parent_is_candidate","release_identity_fields"} and integration.get("merge_commit_only") is True and integration.get("parent_count") == 2 and all(integration.get(key) is True for key in ("exact_first_parent_is_authorized_base", "exact_second_parent_is_authorized_candidate", "candidate_tree_equals_authorized_tree", "integration_tree_equals_authorized_tree", "canonical_ref_must_equal_authorization", "authorization_commit_parent_is_candidate")) and integration.get("authorization_source") == "immutable_git_authorization_commit", "exact authorized integration policy is weakened", problems)
    require(set(integration.get("authorization_required_fields",[]))==AUTH_FIELDS and set(integration.get("release_identity_fields",[]))==RELEASE_IDENTITY and integration.get("authorization_ref_prefix")=="refs/governance/authorizations/" and integration.get("integration_trailer")=="Governance-Authorization" and integration.get("pr_trailer")=="Governance-PR", "release identity contract is incomplete", problems)
    staging = policy.get("high_risk_staging", {}); require(set(staging)=={"required","non_local","isolated","local_substitute_allowed","categories"} and staging.get("required") is True and staging.get("non_local") is True and staging.get("isolated") is True and staging.get("local_substitute_allowed") is False and HIGH_RISK <= set(staging.get("categories", [])), "high-risk staging policy is weakened", problems)
    owner = policy.get("owner_boundaries", {}); require(set(owner)=={"owner_does_not","ask_only_for","routine_technical_autonomy"} and OWNER_DOES_NOT <= set(owner.get("owner_does_not", [])) and owner.get("routine_technical_autonomy")=="agents", "owner protection or agent autonomy is weakened", problems)
    exceptions = policy.get("exceptions", {}); require(set(exceptions)=={"lead_alone_may_approve","non_waivable_controls_may_be_excepted"} and exceptions.get("lead_alone_may_approve") is False and exceptions.get("non_waivable_controls_may_be_excepted") is False, "exception authority is weakened", problems)
    release = policy.get("release", {}); require(set(release)=={"release_role_issues_authorization","authorization_is_candidate_specific","authorization_requires_current_gate_records","merge_and_deploy_authorizations_are_separate","required_gate_record_types"} and all(release.get(key) is True for key in ("release_role_issues_authorization", "authorization_is_candidate_specific", "authorization_requires_current_gate_records", "merge_and_deploy_authorizations_are_separate")) and set(release.get("required_gate_record_types",[]))=={"Independent Code Review","QA","Security Review"}, "Release authority is weakened", problems)
    findings=policy.get("finding_policy",{}); require(set(findings)=={"approval_blocking_severities","repair_required_severities","independent_recheck_required_severities","minor_requires_debt_owner_and_target","suggestion_requires_disposition"} and set(findings.get("approval_blocking_severities",[]))=={"BLOCKING","MAJOR"} and set(findings.get("repair_required_severities",[]))=={"BLOCKING","MAJOR"} and set(findings.get("independent_recheck_required_severities",[]))=={"BLOCKING","MAJOR"} and findings.get("minor_requires_debt_owner_and_target") is True and findings.get("suggestion_requires_disposition") is True, "finding policy is weakened", problems)

def main() -> int:
    problems = []; contents = {path: text_file(path, problems) for path in REQUIRED_FILES}
    try: policy = json.loads(contents.get(POLICY_PATH, ""))
    except json.JSONDecodeError as error: problems.append(f"invalid canonical policy JSON: {error}"); policy = {}
    if isinstance(policy, dict): validate_policy(policy, problems)
    else: problems.append("canonical policy must be a JSON object")
    parsed_schemas={}
    for schema in (".github/governance/gate-record.schema.json", ".github/governance/authorization.schema.json"):
        try: parsed = json.loads(contents.get(schema, "")); parsed_schemas[schema]=parsed; require(parsed.get("additionalProperties") is False, f"{schema} must reject unknown properties", problems)
        except (json.JSONDecodeError, AttributeError) as error: problems.append(f"invalid schema {schema}: {error}")
    gate_schema=parsed_schemas.get(".github/governance/gate-record.schema.json",{}); props=gate_schema.get("properties",{}); finding_schema=props.get("findings",{}).get("items",{});repair_schema=props.get("repair_claims",{}).get("items",{});recheck_schema=props.get("rechecks",{}).get("items",{})
    require(set(gate_schema.get("required",[]))==RECORD_FIELDS and props.get("schema_version",{}).get("const")==2 and set(finding_schema.get("required",[]))==FINDING_FIELDS and finding_schema.get("properties",{}).get("status",{}).get("const")=="OPEN" and set(repair_schema.get("required",[]))==REPAIR_FIELDS and set(recheck_schema.get("required",[]))==RECHECK_FIELDS and all(x.get("additionalProperties") is False for x in (finding_schema,repair_schema,recheck_schema)), "Gate Record JSON Schema does not match canonical recursive contract", problems)
    auth_schema=parsed_schemas.get(".github/governance/authorization.schema.json",{}); commits_schema=auth_schema.get("properties",{}).get("gate_record_commits",{})
    require(set(auth_schema.get("required",[]))==AUTH_FIELDS and set(commits_schema.get("required",[]))=={"Independent Code Review","QA","Security Review"} and commits_schema.get("additionalProperties") is False, "authorization JSON Schema does not match canonical contract", problems)
    for document in ("AGENTS.md", "WORKFLOW.md", "QUALITY.md", "SECURITY.md"):
        require(POLICY_PATH in contents.get(document, ""), f"{document} must identify the canonical policy", problems)
    workflow = contents.get(".github/workflows/governance.yml", "")
    for reference in re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE): require(reference.startswith("./") or re.search(r"@[0-9a-fA-F]{40}$", reference) is not None, f"Action is not pinned: {reference}", problems)
    for command in ("scripts/validate_governance.py", "unittest discover", "scripts/verify_integration.py", "--reconcile-live"): require(command in workflow, f"workflow missing required factory check: {command}", problems)
    words = len(re.findall(r"\b[\w'-]+\b", contents.get("AGENTS.md", ""))); require(words <= 500, f"AGENTS.md exceeds 500 words ({words})", problems)
    if problems: print("Governance validation failed:"); [print(f"- {problem}") for problem in problems]; return 1
    print("Governance validation passed.\nCanonical policy relationships and factory wiring verified."); return 0

if __name__ == "__main__": sys.exit(main())
