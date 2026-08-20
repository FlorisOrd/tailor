import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts")); import verify_integration as verifier

class AuthorizationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.repo=Path(cls.temp.name); cls.old=os.getcwd(); os.chdir(cls.repo)
        cls.git("init","-q"); cls.git("config","user.name","Factory"); cls.git("config","user.email","factory@example.invalid")
        cls.write("file.txt","base0\n"); cls.commit("base0"); cls.base0=cls.sha(); cls.write("file.txt","base1\n"); cls.commit("base1"); cls.base=cls.sha()
        cls.write("feature.txt","candidate\n"); cls.commit("candidate"); cls.candidate=cls.sha(); cls.tree=cls.git("rev-parse",cls.candidate+"^{tree}")
        cls.write("related.txt","related\n"); cls.commit("related"); cls.related=cls.sha(); cls.related_tree=cls.git("rev-parse",cls.related+"^{tree}"); cls.unrelated=cls.git("commit-tree",cls.tree,"-m","unrelated")
        cls.gate_commits={gate:cls.make_gate(gate,index) for index,gate in enumerate(("Independent Code Review","QA","Security Review"),1)}
        cls.auth=cls.make_auth(1,cls.candidate,cls.tree); cls.integration=cls.merge(cls.tree,cls.base,cls.candidate,cls.auth,1)
    @classmethod
    def tearDownClass(cls): os.chdir(cls.old); cls.temp.cleanup()
    @classmethod
    def git(cls,*a): return subprocess.run(("git",*a),check=True,capture_output=True,text=True).stdout.strip()
    @classmethod
    def write(cls,path,text): p=cls.repo/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    @classmethod
    def commit(cls,msg): cls.git("add","--all"); cls.git("commit","-q","-m",msg)
    @classmethod
    def sha(cls): return cls.git("rev-parse","HEAD")
    @classmethod
    def make_gate(cls,gate,index):
        rid=f"GATE-TEST-{index:03d}"; record={"schema_version":2,"gate_record_id":rid,"gate_type":gate,"agent_role":gate,"agent_id":f"agent-{index}","pr_number":1,"base_sha":cls.base,"candidate_sha":cls.candidate,"candidate_tree":cls.tree,"timestamp":f"2026-08-20T1{index}:00:00Z","scope":"factory","checks":["tests"],"findings":[],"repair_claims":[],"rechecks":[],"disposition":"PASS","repository_state_changed":False,"supersedes":[]}
        cls.git("checkout","-q",cls.candidate); cls.write(".github/governance/gate-record.json",json.dumps(record)); cls.git("add","--all"); cls.git("commit","-q","-m",f"gate {index}"); commit=cls.sha(); cls.git("update-ref",f"refs/governance/gate-records/pr-1/{cls.candidate}/{rid}",commit); return commit
    @classmethod
    def auth_record(cls,pr,candidate,tree): return {"schema_version":1,"authorization_id":f"AUTH-TEST-{pr:03d}","pr_number":pr,"base_sha":cls.base,"candidate_sha":candidate,"candidate_tree":tree,"timestamp":"2026-08-20T12:00:00Z","release_agent_id":"release-agent","release_gate_record_id":"GATE-RELEASE-001","gate_record_commits":cls.gate_commits}
    @classmethod
    def make_auth(cls,pr,candidate,tree,publish=True,ref_pr=None,ref_candidate=None,ref_tail=None):
        cls.git("checkout","-q",candidate); cls.write(".github/governance/authorization.json",json.dumps(cls.auth_record(pr,candidate,tree))); cls.git("add","--all"); cls.git("commit","-q","-m","authorization"); auth=cls.sha()
        if publish:
            tail=ref_tail or f"pr-{ref_pr or pr}/{ref_candidate or candidate}"; cls.git("update-ref",f"refs/governance/authorizations/{tail}",auth)
        return auth
    @classmethod
    def merge(cls,tree,base,candidate,auth,pr=1): return cls.git("commit-tree",tree,"-p",base,"-p",candidate,"-m",f"integration\n\nGovernance-PR: {pr}\nGovernance-Authorization: {auth}")
    def setUp(self): self.git("update-ref",f"refs/governance/authorizations/pr-1/{self.candidate}",self.auth)
    def fails(self,sha):
        with self.assertRaises(ValueError): verifier.verify_integration(sha)
    def test_exact_canonical_ref_and_authorization_pass(self): verifier.verify_integration(self.integration)
    def test_wrong_base_fails(self): self.fails(self.merge(self.tree,self.unrelated,self.candidate,self.auth))
    def test_related_wrong_base_fails(self): self.fails(self.merge(self.tree,self.base0,self.candidate,self.auth))
    def test_wrong_candidate_fails(self): self.fails(self.merge(self.tree,self.base,self.unrelated,self.auth))
    def test_related_wrong_candidate_fails(self): self.fails(self.merge(self.tree,self.base,self.related,self.auth))
    def test_wrong_tree_fails(self): self.fails(self.merge(self.related_tree,self.base,self.candidate,self.auth))
    def test_one_parent_fails(self): self.fails(self.git("commit-tree",self.tree,"-p",self.base,"-m",f"integration\n\nGovernance-PR: 1\nGovernance-Authorization: {self.auth}"))
    def test_correct_commit_under_wrong_pr_ref_fails(self):
        self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.git("update-ref",f"refs/governance/authorizations/pr-2/{self.candidate}",self.auth); self.fails(self.integration)
    def test_correct_commit_under_wrong_candidate_ref_fails(self):
        self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.git("update-ref",f"refs/governance/authorizations/pr-1/{self.related}",self.auth); self.fails(self.integration)
    def test_correct_commit_under_arbitrary_governed_ref_fails(self):
        self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.git("update-ref","refs/governance/authorizations/arbitrary",self.auth); self.fails(self.integration)
    def test_canonical_ref_moved_fails(self): self.git("update-ref",f"refs/governance/authorizations/pr-1/{self.candidate}",self.unrelated); self.fails(self.integration)
    def test_another_pr_authorization_fails(self):
        auth=self.make_auth(2,self.candidate,self.tree); self.fails(self.merge(self.tree,self.base,self.candidate,auth,1))
    def test_another_candidate_authorization_fails(self):
        auth=self.make_auth(1,self.related,self.related_tree); self.fails(self.merge(self.tree,self.base,self.candidate,auth,1))
    def test_malformed_ref_fails(self):
        self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.git("update-ref",f"refs/governance/authorizations/1/{self.candidate}",self.auth); self.fails(self.integration)
    def test_missing_canonical_ref_fails(self): self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.fails(self.integration)
    def test_ambiguous_metadata_fails(self):
        bad=self.git("commit-tree",self.tree,"-p",self.base,"-p",self.candidate,"-m",f"integration\n\nGovernance-PR: 1\nGovernance-PR: 2\nGovernance-Authorization: {self.auth}"); self.fails(bad)

if __name__=="__main__": unittest.main()
