"""Fail-closed validation of the frozen Bootstrap Governance v0 constitution."""
from __future__ import annotations
import json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];POLICY_PATH=".github/governance/policy.json"
REQUIRED_FILES=("AGENTS.md","PRODUCT.md","ARCHITECTURE.md","WORKFLOW.md","QUALITY.md","SECURITY.md","INCIDENT_RESPONSE.md","DECISIONS.md",".github/PULL_REQUEST_TEMPLATE.md",".github/GOVERNANCE_ENFORCEMENT.md",".github/workflows/governance.yml",POLICY_PATH,".github/governance/gate-record.schema.json",".github/governance/authorization.schema.json",".github/governance/GATE_RECORDS.md","scripts/fetch_governance_refs.sh","scripts/validate_governance.py","scripts/validate_gate_records.py","scripts/validate_evidence.py","scripts/verify_integration.py")
TOP={"schema_version","authority","specification_frozen","scope","material_work","roles","current_gate_records","freshness","ci","authorization","integration","future_product_controls","owner_protection","github_free_limits","historical_evidence","factory_v1"}
ROLES={"Implementation","Independent Code Review","QA","Release"};GATES={"Independent Code Review","QA","Security Review","Release"}
AUTH_SCHEMA_PATH=".github/governance/authorization.schema.json"
AUTH_FIXED={
    "schema_version":1,"record_type":"Bootstrap Governance v0 Merge Authorization",
    "repository":"FlorisOrd/tailor","head_repository":"FlorisOrd/tailor",
    "pr_state":"open","merged":False,"base_branch":"main","base_is_ancestor":True,
    "ci_workflow_name":"Governance Baseline","ci_workflow_path":".github/workflows/governance.yml",
    "ci_event":"pull_request","ci_status":"completed","ci_conclusion":"success",
}

def req(value,message,p):
    if not value:p.append(message)
def all_true(section,keys):return isinstance(section,dict) and all(section.get(k) is True for k in keys)
def validate_authorization_schema(schema,p):
    properties=schema.get("properties",{}) if isinstance(schema,dict) else {}
    required=schema.get("required",[]) if isinstance(schema,dict) else []
    req(schema.get("type")=="object" and schema.get("additionalProperties") is False,"authorization schema must be a closed object",p)
    req(isinstance(required,list) and set(required)==set(properties),"authorization schema required fields differ from properties",p)
    for field,value in AUTH_FIXED.items():req(properties.get(field)=={"const":value},f"authorization schema fixed field changed: {field}",p)
    for field in ("pr_number","ci_pr_number"):
        item=properties.get(field,{})
        req(item.get("type")=="integer" and item.get("minimum")==1 and "const" not in item,f"authorization schema dynamic PR field is frozen or weakened: {field}",p)
    branch=properties.get("head_branch",{})
    req(branch.get("type")=="string" and branch.get("minLength")==1 and isinstance(branch.get("pattern"),str) and branch["pattern"] and "const" not in branch,"authorization schema dynamic head branch is frozen or weakened",p)
def validate_policy(x,p):
    req(set(x)==TOP,"policy top-level contract changed",p);req(x.get("schema_version")==1 and x.get("authority")=="Bootstrap Governance v0" and x.get("specification_frozen") is True,"Bootstrap v0 identity/freeze weakened",p)
    req(all_true(x.get("material_work"),{"ambiguity_defaults_to_material","requires_isolated_branch","requires_pull_request"}),"material-work controls weakened",p)
    roles=x.get("roles",{});req(set(roles.get("required",[]))==ROLES and set(roles.get("mutually_distinct",[]))==ROLES and roles.get("security_triggered") is True and set(roles.get("security_distinct_from",[]))=={"Implementation","Lead / Engineering Manager","QA","Release"} and roles.get("lead_transcription_is_gate_evidence") is False,"role separation or publisher ownership weakened",p)
    gates=x.get("current_gate_records",{});req(set(gates.get("required_types",[]))==GATES and gates.get("protocol")=="Bootstrap Governance v0 Gate Record" and gates.get("canonical_ref_prefix")=="refs/governance/bootstrap-gates/" and all_true(gates,{"candidate_specific","immutable_git_object","commit_parent_is_candidate","pr_visible_exact_copy_required","publisher_agent_id_must_equal_agent_id","disposition_must_be_pass","blocking_major_forbid_pass","explicit_release_selection","historical_records_are_not_current_evidence"}),"current Gate Record controls weakened",p)
    req(all_true(x.get("freshness"),{"exact_pr_base_candidate_tree","candidate_change_invalidates","repair_requires_new_candidate","fresh_independent_pass_after_repair"}),"freshness controls weakened",p)
    req(all_true(x.get("ci"),{"fail_closed","governance_validation_required","bootstrap_tests_required","gitleaks_required","candidate_identity_required","current_candidate_success_required"}),"mandatory CI controls weakened",p)
    auth=x.get("authorization",{});req(auth.get("canonical_ref_prefix")=="refs/governance/authorizations/" and all_true(auth,{"release_only","immutable_git_object","binds_exact_pr_base_candidate_tree","binds_exact_current_gate_commits","binds_current_ci","commit_parent_is_candidate"}),"authorization controls weakened",p)
    req(x.get("integration",{}).get("parent_count")==2 and all_true(x.get("integration"),{"merge_commit_only","first_parent_is_authorized_base","second_parent_is_authorized_candidate","tree_equals_authorized_candidate_tree","authorization_identity_exact"}),"integration identity controls weakened",p)
    req(all_true(x.get("future_product_controls"),{"security_triggers_defined","accessibility_browser_gate_defined","high_risk_non_local_staging_defined","rollback_monitoring_defined","incident_response_defined"}),"future product safeguards weakened",p)
    req(all_true(x.get("owner_protection"),{"owner_never_codes_or_debugs","owner_never_operates_git","owner_never_interprets_ci_logs","routine_technical_decisions_are_agents"}),"owner protection weakened",p)
    req(all_true(x.get("github_free_limits"),{"agent_identity_not_cryptographically_proven","distinct_processes_not_hard_enforced","direct_pushes_not_fully_blocked","private_repo_controls_not_overstated"}),"GitHub Free limitations overstated",p)
    req(all_true(x.get("historical_evidence"),{"preserved_unchanged","audit_only_for_superseded_candidates","not_release_prerequisite","no_cross_version_normalization"}),"historical audit boundary weakened",p)
    factory=x.get("factory_v1",{});req(factory.get("repository")=="agent-software-factory" and factory.get("deferred") is True and factory.get("starts_with_uniform_protocol_from_genesis") is True,"Factory v1 handoff changed",p)

def main():
    p=[];contents={}
    for rel in REQUIRED_FILES:
        path=ROOT/rel
        if not path.is_file():p.append(f"missing required file: {rel}");continue
        text=path.read_text(encoding="utf-8");contents[rel]=text
        if not text.strip() or not text.endswith("\n"):p.append(f"invalid text file: {rel}")
        if any(line.rstrip()!=line for line in text.splitlines()):p.append(f"trailing whitespace: {rel}")
    try:policy=json.loads(contents.get(POLICY_PATH,""));validate_policy(policy,p)
    except json.JSONDecodeError as error:p.append(f"invalid policy JSON: {error}")
    for schema in (".github/governance/gate-record.schema.json",AUTH_SCHEMA_PATH):
        try:
            parsed=json.loads(contents.get(schema,"{}"));req(parsed.get("additionalProperties") is False,f"{schema} permits unknown fields",p)
            if schema==AUTH_SCHEMA_PATH:validate_authorization_schema(parsed,p)
        except json.JSONDecodeError:p.append(f"invalid schema: {schema}")
    workflow=contents.get(".github/workflows/governance.yml","")
    for token in ("scripts/validate_governance.py","unittest discover","scripts/verify_integration.py","gitleaks/gitleaks-action") :req(token in workflow,f"workflow missing {token}",p)
    req("governance-ref-auth-smoke:" in workflow and "historical-post-merge-evidence:" in workflow and workflow.count("scripts/fetch_governance_refs.sh")==3,"workflow missing shared pre/post-integration governance-ref authentication",p)
    req(workflow.count("persist-credentials: false")>=5,"workflow persists checkout credentials",p)
    fetcher=contents.get("scripts/fetch_governance_refs.sh","")
    for token in ("GIT_ASKPASS", "GIT_TERMINAL_PROMPT=0", "refs/governance/authorizations/", "refs/governance/bootstrap-gates/", "git cat-file -e") :req(token in fetcher,f"governance-ref fetcher missing {token}",p)
    req("remote set-url" not in fetcher and "credential.helper" not in fetcher and "set -x" not in fetcher,"governance-ref fetcher may persist or expose credentials",p)
    for permission in ("actions: read","contents: read","issues: read","pull-requests: read"):req(permission in workflow,f"workflow missing least-privilege permission {permission}",p)
    req(not re.search(r"permissions:[\s\S]*?\bwrite\b",workflow),"workflow grants write permission",p)
    req("continue-on-error" not in workflow and "|| true" not in workflow,"workflow contains failure suppression",p)
    for use in re.findall(r"^\s*uses:\s*([^\s#]+)",workflow,re.MULTILINE):req(use.startswith("./") or re.search(r"@[0-9a-fA-F]{40}$",use),f"unpinned Action: {use}",p)
    req(len(re.findall(r"\b[\w'-]+\b",contents.get("AGENTS.md","")))<=500,"AGENTS.md exceeds 500 words",p)
    if p:print("Governance validation failed:");[print(f"- {x}") for x in p];return 1
    print("Bootstrap Governance v0 validation passed.");return 0
if __name__=="__main__":sys.exit(main())
