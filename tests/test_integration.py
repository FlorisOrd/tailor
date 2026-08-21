import json, os, re, subprocess, sys, tempfile, unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_SCHEMA = json.loads((ROOT / ".github/governance/authorization.schema.json").read_text())
sys.path.insert(0, str(ROOT / "scripts"))
from tests.test_gate_records import record
from verify_integration import (
    AUTH_CONTEXT_MAP, CONTEXT_FIELDS, LiveReleaseContext, build_live_release_context, ci_identity,
    remote_ref_sha, validate_ci_against_context, validate_release_context, verify_authorization,
    verify_integration,
)

def schema_problems(value, schema, path="authorization"):
    problems=[]
    if "const" in schema and value != schema["const"]: problems.append(f"{path} differs from const")
    kind=schema.get("type")
    valid_type={"object":isinstance(value,dict),"string":isinstance(value,str),"integer":isinstance(value,int) and not isinstance(value,bool)}.get(kind,True)
    if not valid_type:return problems+[f"{path} has wrong type"]
    if kind=="object":
        properties=schema.get("properties",{});required=schema.get("required",[])
        problems.extend(f"{path}.{field} is missing" for field in required if field not in value)
        if schema.get("additionalProperties") is False:problems.extend(f"{path}.{field} is unknown" for field in value if field not in properties)
        for field in value.keys() & properties.keys():problems.extend(schema_problems(value[field],properties[field],f"{path}.{field}"))
    if kind=="string":
        if len(value)<schema.get("minLength",0):problems.append(f"{path} is too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"],value) is None:problems.append(f"{path} has invalid format")
    if kind=="integer" and value<schema.get("minimum",value):problems.append(f"{path} is below minimum")
    return problems

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.repo = Path(self.temp.name)
        self.old = os.getcwd(); os.chdir(self.repo)
        self.git("init", "-q"); self.git("config", "user.name", "Bootstrap"); self.git("config", "user.email", "bootstrap@example.invalid")
        self.write("base.txt", "base"); self.git("add", "--all"); self.git("commit", "-q", "-m", "base"); self.base = self.git("rev-parse", "HEAD")
        self.write("change.txt", "candidate"); self.git("add", "--all"); self.git("commit", "-q", "-m", "candidate"); self.candidate = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}"); self.context = self.release_context(); self.records = {}; self.commits = {}
        for gate, agent in {"Independent Code Review":"review", "QA":"qa", "Security Review":"security", "Release":"release"}.items():
            item = record(gate, agent, base_sha=self.base, candidate_sha=self.candidate, candidate_tree=self.tree)
            commit = self.object_commit(".github/governance/gate-record.json", item, self.candidate, "gate" + gate.replace(" ", ""))
            self.git("update-ref", f"refs/governance/bootstrap-gates/pr-1/{self.candidate}/{gate.lower().replace(' ','-')}/{item['gate_record_id']}", commit)
            self.records[gate], self.commits[gate] = item, commit
        self.auth, self.auth_payload = self.authorization(); self.integration = self.merge(self.base, self.candidate, self.tree, self.auth)

    def tearDown(self): os.chdir(self.old); self.temp.cleanup()
    def git(self, *args, input=None): return subprocess.run(("git", *args), input=input, check=True, capture_output=True, text=True).stdout.strip()
    def write(self, path, text):
        item = Path(path); item.parent.mkdir(parents=True, exist_ok=True); item.write_text(text)
    def object_commit(self, path, obj, parent, message):
        index = self.repo / (message + str(len(list(self.repo.glob("*.index")))) + ".index"); env = os.environ | {"GIT_INDEX_FILE":str(index)}
        subprocess.run(("git", "read-tree", parent), check=True, env=env)
        blob = subprocess.run(("git", "hash-object", "-w", "--stdin"), input=json.dumps(obj), text=True, capture_output=True, check=True).stdout.strip()
        subprocess.run(("git", "update-index", "--add", "--cacheinfo", "100644", blob, path), check=True, env=env)
        object_tree = subprocess.run(("git", "write-tree"), capture_output=True, text=True, check=True, env=env).stdout.strip()
        return self.git("commit-tree", object_tree, "-p", parent, "-m", message)
    def release_context(self, **changes):
        value = LiveReleaseContext(
            repository="FlorisOrd/tailor", head_repository="FlorisOrd/tailor", pr_number=1,
            pr_state="open", merged=False, base_branch="main", base_sha=self.base,
            head_branch="bootstrap/agent-company", head_sha=self.candidate, candidate_tree=self.tree,
            remote_base_sha=self.base, remote_head_sha=self.candidate, base_is_ancestor=True,
            ci_workflow_name="Governance Baseline", ci_workflow_path=".github/workflows/governance.yml",
            ci_event="pull_request", ci_pr_number=1, ci_head_sha=self.candidate,
            ci_status="completed", ci_conclusion="success",
        )
        return replace(value, **changes)
    def authorization(self, context=None, **changes):
        context = context or self.context
        identity = {auth_field:getattr(context, context_field) for auth_field, context_field in AUTH_CONTEXT_MAP.items()}
        value = {"schema_version":1, "record_type":"Bootstrap Governance v0 Merge Authorization", "authorization_id":"AUTH-1", "timestamp":"2026-08-20T12:00:00Z", "implementation_agent_id":"implementation", "lead_agent_id":"lead", "release_agent_id":"release", "ci_run_id":123, "gate_record_commits":self.commits, **identity}
        value.update(changes); commit = self.object_commit(".github/governance/authorization.json", value, value["candidate_sha"], "auth")
        self.git("update-ref", f"refs/governance/authorizations/pr-{value['pr_number']}/{value['candidate_sha']}", commit)
        return commit, value
    def merge(self, first, second, object_tree, authorization): return self.git("commit-tree", object_tree, "-p", first, "-p", second, "-m", f"merge\n\nGovernance-PR: 1\nGovernance-Authorization: {authorization}")
    def pr_payload(self, **changes):
        value = {"number":1, "state":"open", "merged":False, "base":{"ref":"main", "sha":self.base, "repo":{"full_name":"FlorisOrd/tailor"}}, "head":{"ref":"bootstrap/agent-company", "sha":self.candidate, "repo":{"full_name":"FlorisOrd/tailor"}}}
        value.update(changes); return value
    def run_payload(self, **changes):
        value = {"name":"Governance Baseline", "path":".github/workflows/governance.yml", "event":"pull_request", "pull_requests":[{"number":1}], "head_sha":self.candidate, "status":"completed", "conclusion":"success"}
        value.update(changes); return value

    def test_exact_authorization_passes_before_merge(self): verify_authorization(self.auth)
    def test_exact_integration_passes(self): verify_integration(self.integration)
    def test_exact_live_context_passes(self): self.assertEqual([], validate_release_context(self.context, self.auth_payload, 1, "bootstrap/agent-company"))
    def test_arbitrary_explicit_pr_and_head_identity_passes(self):
        context = self.release_context(pr_number=17, head_branch="fix/corrective", ci_pr_number=17)
        _, authorization = self.authorization(context)
        self.assertEqual([], validate_release_context(context, authorization, 17, "fix/corrective"))

    def test_pr_2_release_authorization_is_schema_valid_and_exact_context_valid(self):
        context = self.release_context(pr_number=2, head_branch="fix/bootstrap-post-integration-ci-auth", ci_pr_number=2)
        _, authorization = self.authorization(context)
        self.assertEqual([], schema_problems(authorization, AUTHORIZATION_SCHEMA))
        self.assertEqual([], validate_release_context(context, authorization, 2, "fix/bootstrap-post-integration-ci-auth"))

    def test_arbitrary_future_authorization_is_schema_valid(self):
        context = self.release_context(pr_number=314, head_branch="repair/future-314", ci_pr_number=314)
        _, authorization = self.authorization(context)
        self.assertEqual([], schema_problems(authorization, AUTHORIZATION_SCHEMA))

    def test_authorization_schema_rejects_missing_zero_and_empty_dynamic_identity(self):
        cases={
            "zero_pr":{"pr_number":0},"zero_ci_pr":{"ci_pr_number":0},"empty_head":{"head_branch":""},
            "missing_pr":{"pr_number":None},"missing_ci_pr":{"ci_pr_number":None},"missing_head":{"head_branch":None},
        }
        for name,change in cases.items():
            authorization=dict(self.auth_payload);field,value=next(iter(change.items()))
            if value is None:authorization.pop(field)
            else:authorization[field]=value
            with self.subTest(name=name):self.assertTrue(schema_problems(authorization,AUTHORIZATION_SCHEMA))

    def test_expected_pr_must_match_live_authorization_and_ci(self):
        cases = (
            self.release_context(pr_number=18),
            (self.context, self.authorization(self.release_context(pr_number=18))[1]),
            self.release_context(ci_pr_number=18),
        )
        for live, authorization in ((cases[0], self.auth_payload), cases[1], (cases[2], self.auth_payload)):
            with self.subTest(live=live.pr_number, authorization=authorization["pr_number"], ci=live.ci_pr_number):
                self.assertTrue(validate_release_context(live, authorization, 17, "bootstrap/agent-company"))

    def test_expected_head_must_match_live_authorization_and_remote(self):
        alternate = self.release_context(head_branch="other")
        _, alternate_authorization = self.authorization(alternate)
        cases = (
            (alternate, self.auth_payload),
            (self.context, alternate_authorization),
            (self.release_context(remote_head_sha=self.base), self.auth_payload),
        )
        for live, authorization in cases:
            with self.subTest(live=live.head_branch, authorization=authorization["head_branch"], remote=live.remote_head_sha):
                self.assertTrue(validate_release_context(live, authorization, 1, "bootstrap/agent-company"))

    def test_expected_identity_inputs_are_required(self):
        for pr, branch in ((None, "branch"), (1, None), (1, "")):
            with self.subTest(pr=pr, branch=branch):
                self.assertRaises(ValueError, validate_release_context, self.context, self.auth_payload, pr, branch)
    def test_build_exact_live_context_passes(self):
        refs = {"refs/heads/main":self.base, "refs/heads/bootstrap/agent-company":self.candidate}
        with patch("verify_integration.github_json", side_effect=[self.pr_payload(), self.run_payload()]), patch("verify_integration.remote_ref_sha", side_effect=lambda ref:refs[ref]):
            self.assertEqual(self.context, build_live_release_context("token", 123, 1, "bootstrap/agent-company"))
    def test_build_arbitrary_live_context_from_explicit_identity_passes(self):
        expected = self.release_context(pr_number=17, head_branch="fix/corrective", ci_pr_number=17)
        refs = {"refs/heads/main":self.base, "refs/heads/fix/corrective":self.candidate}
        with patch("verify_integration.github_json", side_effect=[self.pr_payload(number=17, head={"ref":"fix/corrective", "sha":self.candidate, "repo":{"full_name":"FlorisOrd/tailor"}}), self.run_payload(pull_requests=[{"number":17}])]), patch("verify_integration.remote_ref_sha", side_effect=lambda ref:refs[ref]):
            self.assertEqual(expected, build_live_release_context("token", 123, 17, "fix/corrective"))

    def test_every_context_field_mutation_fails(self):
        mutations = {
            "repository":"Other/repo", "head_repository":"Other/repo", "pr_number":2,
            "pr_state":"closed", "merged":True, "base_branch":"trunk", "base_sha":"9"*40,
            "head_branch":"alternate", "head_sha":"8"*40, "candidate_tree":"7"*40,
            "remote_base_sha":"6"*40, "remote_head_sha":"5"*40, "base_is_ancestor":False,
            "ci_workflow_name":"Other", "ci_workflow_path":".github/workflows/other.yml",
            "ci_event":"push", "ci_pr_number":2, "ci_head_sha":"4"*40,
            "ci_status":"queued", "ci_conclusion":"failure",
        }
        self.assertEqual(set(CONTEXT_FIELDS), set(mutations))
        for field, value in mutations.items():
            with self.subTest(source="live", field=field): self.assertTrue(validate_release_context(replace(self.context, **{field:value}), self.auth_payload, 1, "bootstrap/agent-company"))
        for auth_field, context_field in AUTH_CONTEXT_MAP.items():
            changed = dict(self.auth_payload); changed[auth_field] = mutations[context_field]
            with self.subTest(source="authorization", field=auth_field): self.assertTrue(validate_release_context(self.context, changed, 1, "bootstrap/agent-company"))

    def test_ci_association_missing_malformed_or_ambiguous_fails(self):
        for associations in (None, [], [{"number":"1"}], [{"number":1}, {"number":2}]):
            with self.subTest(associations=associations): self.assertRaises(ValueError, ci_identity, self.run_payload(pull_requests=associations))
    def test_wrong_pr_ci_attack_fails(self): self.assertTrue(validate_ci_against_context(self.run_payload(pull_requests=[{"number":2}]), self.context))
    def test_same_sha_alternate_head_attack_fails(self): self.assertTrue(validate_release_context(replace(self.context, head_branch="alternate"), self.auth_payload, 1, "bootstrap/agent-company"))
    def test_builder_does_not_trust_alternate_pr_head_branch(self):
        refs = {"refs/heads/main":self.base, "refs/heads/bootstrap/agent-company":self.candidate}
        with patch("verify_integration.github_json", side_effect=[self.pr_payload(head={"ref":"alternate", "sha":self.candidate, "repo":{"full_name":"FlorisOrd/tailor"}}), self.run_payload()]), patch("verify_integration.remote_ref_sha", side_effect=lambda ref:refs[ref]):
            self.assertTrue(validate_release_context(build_live_release_context("token", 123, 1, "bootstrap/agent-company"), self.auth_payload, 1, "bootstrap/agent-company"))
    def test_missing_live_github_source_fails(self):
        with patch("verify_integration.github_json", side_effect=OSError("offline")): self.assertRaises(ValueError, build_live_release_context, "token", 123, 1, "bootstrap/agent-company")
    def test_missing_live_remote_source_fails(self):
        with patch("verify_integration.github_json", side_effect=[self.pr_payload(), self.run_payload()]), patch("verify_integration.remote_ref_sha", side_effect=ValueError("missing")): self.assertRaises(ValueError, build_live_release_context, "token", 123, 1, "bootstrap/agent-company")
    def test_incomplete_pr_or_ambiguous_remote_state_fails(self):
        with patch("verify_integration.github_json", side_effect=[{}, self.run_payload()]): self.assertRaises(ValueError, build_live_release_context, "token", 123, 1, "bootstrap/agent-company")
        result = SimpleNamespace(returncode=0, stdout=f"{self.base}\trefs/heads/main\n{self.candidate}\trefs/heads/main\n", stderr="")
        with patch("verify_integration.subprocess.run", return_value=result): self.assertRaises(ValueError, remote_ref_sha, "refs/heads/main")
    def test_original_self_consistent_base_equals_candidate_attack_fails(self):
        fake = self.release_context(base_sha=self.candidate, remote_base_sha=self.candidate)
        bad, _ = self.authorization(fake)
        with patch.dict(os.environ, {"GITHUB_TOKEN":"token"}), patch("verify_integration.build_live_release_context", return_value=self.context), patch("verify_integration.validate_current_set", return_value=[]), patch("verify_integration.validate_selected_live", return_value=[]):
            self.assertRaises(ValueError, verify_authorization, bad, True)
    def test_stale_gate_record_fails(self):
        self.records["QA"]["candidate_sha"] = "9"*40
        bad_gate = self.object_commit(".github/governance/gate-record.json", self.records["QA"], self.candidate, "badgate")
        bad, _ = self.authorization(gate_record_commits=self.commits | {"QA":bad_gate})
        self.assertRaises(ValueError, verify_authorization, bad)
    def test_missing_or_moved_authorization_ref_fails(self):
        self.git("update-ref", "-d", f"refs/governance/authorizations/pr-1/{self.candidate}")
        self.assertRaises(ValueError, verify_integration, self.integration)
    def test_wrong_integration_parents_or_tree_fail(self):
        for item in (self.merge(self.candidate, self.candidate, self.tree, self.auth), self.merge(self.base, self.base, self.tree, self.auth), self.merge(self.base, self.candidate, self.git("rev-parse", f"{self.base}^{{tree}}"), self.auth)):
            with self.subTest(item=item): self.assertRaises(ValueError, verify_integration, item)

if __name__ == "__main__": unittest.main()
