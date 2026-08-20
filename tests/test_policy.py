import copy, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_governance as validator

class PolicyTests(unittest.TestCase):
    def setUp(self): self.policy = json.loads((ROOT / ".github/governance/policy.json").read_text())
    def problems(self, mutate):
        policy = copy.deepcopy(self.policy); mutate(policy); problems = []; validator.validate_policy(policy, problems); return problems
    def test_valid_policy(self):
        problems = []; validator.validate_policy(self.policy, problems); self.assertEqual([], problems)
    def test_implementation_cannot_perform_qa(self): self.assertTrue(self.problems(lambda p: p["roles"]["mutually_distinct"].remove("QA")))
    def test_implementation_cannot_review(self): self.assertTrue(self.problems(lambda p: p["roles"]["mutually_distinct"].remove("Independent Code Review")))
    def test_release_cannot_implement(self): self.assertTrue(self.problems(lambda p: p["roles"]["mutually_distinct"].remove("Release")))
    def test_nonwaivable_gate_cannot_be_removed(self): self.assertTrue(self.problems(lambda p: p["non_waivable_controls"].remove("GOV-EXACT-INTEGRATION")))
    def test_lead_only_exception_fails(self): self.assertTrue(self.problems(lambda p: p["exceptions"].update(lead_alone_may_approve=True)))
    def test_security_independence_fails(self): self.assertTrue(self.problems(lambda p: p["roles"]["security_distinct_from"].remove("Implementation")))
    def test_exact_revision_weakening_fails(self): self.assertTrue(self.problems(lambda p: p["integration"].update(exact_first_parent_is_authorized_base=False)))
    def test_high_risk_staging_removal_fails(self): self.assertTrue(self.problems(lambda p: p["high_risk_staging"].update(required=False)))
    def test_owner_protection_removal_fails(self): self.assertTrue(self.problems(lambda p: p["owner_boundaries"]["owner_does_not"].remove("debug")))

if __name__ == "__main__": unittest.main()
