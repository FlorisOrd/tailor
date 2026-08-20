import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts")); import validate_governance as validator
POLICY=json.loads((ROOT/".github/governance/policy.json").read_text())

def remove(path,value):
    def mutate(p):
        target=p
        for key in path: target=target[key]
        target.remove(value)
    return mutate
def set_value(path,value):
    def mutate(p):
        target=p
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value
    return mutate

class PolicyContractTests(unittest.TestCase):
    def test_canonical_policy_passes(self):
        problems=[]; validator.validate_policy(POLICY,problems); self.assertEqual([],problems)

def add_case(name,mutate):
    def test(self):
        policy=copy.deepcopy(POLICY); mutate(policy); problems=[]; validator.validate_policy(policy,problems); self.assertTrue(problems,name)
    setattr(PolicyContractTests,"test_mutation_"+name,test)

cases={
"implementation_may_qa":remove(("roles","mutually_distinct"),"QA"),
"implementation_may_review":remove(("roles","mutually_distinct"),"Independent Code Review"),
"release_may_implement":remove(("roles","mutually_distinct"),"Release"),
"security_not_distinct":remove(("roles","security_distinct_from"),"Implementation"),
"release_loses_merge_authority":remove(("roles","release_only_authorities"),"Authorization to Merge"),
"lead_only_exception":set_value(("exceptions","lead_alone_may_approve"),True),
"nonwaivable_exception":set_value(("exceptions","non_waivable_controls_may_be_excepted"),True),
"pr_body_authoritative":set_value(("evidence","pr_body_is_authoritative"),True),
"publisher_not_gate_agent":set_value(("evidence","publisher_must_be_performing_agent"),False),
"content_addressing_removed":set_value(("evidence","content_addressing","required"),False),
"comment_mismatch_allowed":set_value(("evidence","content_addressing","comment_must_match_stored_json"),False),
"gate_parent_not_candidate":set_value(("evidence","content_addressing","commit_parent_is_candidate"),False),
"wrong_gate_ref_prefix":set_value(("evidence","content_addressing","canonical_ref_prefix"),"refs/anything/"),
"forward_mutation_allowed":set_value(("evidence","append_only_graph","predecessor_never_mutated"),False),
"supersession_cycles_allowed":set_value(("evidence","append_only_graph","acyclic"),False),
"supersession_forks_allowed":set_value(("evidence","append_only_graph","no_forks"),False),
"supersession_changes_role":set_value(("evidence","append_only_graph","same_gate_type_for_supersession"),False),
"supersession_changes_pr":set_value(("evidence","append_only_graph","same_pr"),False),
"supersession_unordered":set_value(("evidence","append_only_graph","ordered_timestamp"),False),
"repair_claim_closes":set_value(("evidence","finding_lifecycle","repair_claim_does_not_close"),False),
"same_agent_rechecks":set_value(("evidence","finding_lifecycle","closure_requires_distinct_rechecker"),False),
"github_comments_ignored":set_value(("evidence","live_reconciliation","github_pr_comments_required"),False),
"local_subset_trusted":set_value(("evidence","live_reconciliation","local_ref_subset_not_authoritative"),False),
"source_disagreement_allowed":set_value(("evidence","live_reconciliation","source_disagreement_fails"),False),
"missing_history_allowed":set_value(("evidence","live_reconciliation","missing_history_fails"),False),
"candidate_change_not_stale":set_value(("stale_evidence","candidate_change_invalidates"),False),
"repair_not_new_candidate":set_value(("stale_evidence","repair_creates_new_candidate"),False),
"unaffected_self_attested":set_value(("stale_evidence","unaffected_requires_independent_gate_owner_record"),False),
"merge_commit_not_required":set_value(("integration","merge_commit_only"),False),
"wrong_parent_count":set_value(("integration","parent_count"),1),
"base_ancestry_substitutes":set_value(("integration","exact_first_parent_is_authorized_base"),False),
"candidate_ancestry_substitutes":set_value(("integration","exact_second_parent_is_authorized_candidate"),False),
"candidate_tree_not_exact":set_value(("integration","candidate_tree_equals_authorized_tree"),False),
"integration_tree_not_exact":set_value(("integration","integration_tree_equals_authorized_tree"),False),
"authorization_ref_not_exact":set_value(("integration","canonical_ref_must_equal_authorization"),False),
"authorization_parent_not_candidate":set_value(("integration","authorization_commit_parent_is_candidate"),False),
"authorization_not_immutable":set_value(("integration","authorization_source"),"caller_arguments"),
"wrong_auth_ref_prefix":set_value(("integration","authorization_ref_prefix"),"refs/anything/"),
"wrong_integration_trailer":set_value(("integration","integration_trailer"),"Anything"),
"wrong_pr_trailer":set_value(("integration","pr_trailer"),"Anything"),
"staging_not_required":set_value(("high_risk_staging","required"),False),
"staging_local":set_value(("high_risk_staging","non_local"),False),
"staging_not_isolated":set_value(("high_risk_staging","isolated"),False),
"local_substitute_allowed":set_value(("high_risk_staging","local_substitute_allowed"),True),
"owner_not_autonomous":set_value(("owner_boundaries","routine_technical_autonomy"),"owner"),
"blocking_approves":remove(("finding_policy","approval_blocking_severities"),"BLOCKING"),
"major_no_repair":remove(("finding_policy","repair_required_severities"),"MAJOR"),
"major_no_recheck":remove(("finding_policy","independent_recheck_required_severities"),"MAJOR"),
"minor_no_debt":set_value(("finding_policy","minor_requires_debt_owner_and_target"),False),
"suggestion_no_disposition":set_value(("finding_policy","suggestion_requires_disposition"),False),
"release_not_candidate_specific":set_value(("release","authorization_is_candidate_specific"),False),
"release_ignores_records":set_value(("release","authorization_requires_current_gate_records"),False),
"merge_deploy_combined":set_value(("release","merge_and_deploy_authorizations_are_separate"),False)
}
for field in validator.RECORD_FIELDS: cases["missing_record_field_"+field]=remove(("evidence","required_gate_record_fields"),field)
for field in validator.FINDING_FIELDS: cases["missing_finding_field_"+field]=remove(("evidence","required_finding_fields"),field)
for field in validator.REPAIR_FIELDS: cases["missing_repair_field_"+field]=remove(("evidence","required_repair_claim_fields"),field)
for field in validator.RECHECK_FIELDS: cases["missing_recheck_field_"+field]=remove(("evidence","required_recheck_fields"),field)
for field in validator.AUTH_FIELDS: cases["missing_auth_field_"+field]=remove(("integration","authorization_required_fields"),field)
for field in validator.RELEASE_IDENTITY: cases["missing_release_identity_"+field]=remove(("integration","release_identity_fields"),field)
for field in ("base_sha","candidate_sha","candidate_tree"): cases["missing_candidate_identity_"+field]=remove(("evidence","candidate_identity_fields"),field)
for value in ("BLOCKING","MAJOR","MINOR","SUGGESTION"): cases["missing_finding_severity_"+value]=remove(("evidence","finding_severities"),value)
for value in ("OPEN",): cases["missing_finding_status_"+value]=remove(("evidence","finding_statuses"),value)
for gate in ("Independent Code Review","QA","Security Review","Release"): cases["missing_gate_"+gate.replace(" ","_")]=remove(("evidence","formal_gate_types"),gate)
for category in validator.HIGH_RISK: cases["missing_high_risk_"+category]=remove(("high_risk_staging","categories"),category)
for action in validator.OWNER_DOES_NOT: cases["owner_must_"+action]=remove(("owner_boundaries","owner_does_not"),action)
for section in ("append_only_graph","finding_lifecycle","live_reconciliation"):
 for key in POLICY["evidence"][section]: cases[f"weaken_{section}_{key}"]=set_value(("evidence",section,key),False)
for name,mutate in cases.items(): add_case(name,mutate)

if __name__=="__main__": unittest.main()
