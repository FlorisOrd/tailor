import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
import verify_integration as verifier

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.repo=Path(cls.temp.name); cls.old=os.getcwd(); os.chdir(cls.repo)
        cls.git("init","-q"); cls.git("config","user.name","Factory Test"); cls.git("config","user.email","factory@example.invalid")
        cls.write("file.txt","base0\n"); cls.commit("base0"); cls.base0=cls.sha()
        cls.write("file.txt","base1\n"); cls.commit("base1"); cls.base=cls.sha()
        cls.write("feature.txt","candidate\n"); cls.commit("candidate"); cls.candidate=cls.sha(); cls.tree=cls.git("rev-parse",cls.candidate+"^{tree}")
        cls.write("related.txt","related\n"); cls.commit("related candidate"); cls.related_candidate=cls.sha(); cls.related_tree=cls.git("rev-parse",cls.related_candidate+"^{tree}")
        cls.unrelated=cls.git("commit-tree",cls.tree,"-m","unrelated")
        cls.git("checkout","-q",cls.candidate); cls.write(".github/governance/authorization.json",json.dumps({"schema_version":1,"authorization_id":"AUTH-TEST-001","pr_number":1,"base_sha":cls.base,"candidate_sha":cls.candidate,"candidate_tree":cls.tree,"timestamp":"2026-08-20T12:00:00Z","release_agent_id":"release-agent","release_gate_record_id":"GATE-RELEASE-001"})); cls.commit("authorization"); cls.auth=cls.sha()
        cls.git("update-ref",f"refs/governance/authorizations/pr-1/{cls.candidate}",cls.auth)
        cls.integration=cls.merge(cls.tree,cls.base,cls.candidate)
    @classmethod
    def tearDownClass(cls): os.chdir(cls.old); cls.temp.cleanup()
    @classmethod
    def git(cls,*args): return subprocess.run(("git",*args),check=True,capture_output=True,text=True).stdout.strip()
    @classmethod
    def write(cls,path,text): p=cls.repo/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    @classmethod
    def commit(cls,msg): cls.git("add","--all"); cls.git("commit","-q","-m",msg)
    @classmethod
    def sha(cls): return cls.git("rev-parse","HEAD")
    @classmethod
    def merge(cls,tree,base,candidate,auth=None): return cls.git("commit-tree",tree,"-p",base,"-p",candidate,"-m",f"integration\n\nGovernance-Authorization: {auth or cls.auth}")
    def setUp(self): self.git("update-ref",f"refs/governance/authorizations/pr-1/{self.candidate}",self.auth)
    def fails(self,sha):
        with self.assertRaises(ValueError): verifier.verify_integration(sha)
    def test_correct_authorized_tuple_passes(self): verifier.verify_integration(self.integration)
    def test_wrong_base_fails(self): self.fails(self.merge(self.tree,self.unrelated,self.candidate))
    def test_related_but_wrong_base_fails(self): self.fails(self.merge(self.tree,self.base0,self.candidate))
    def test_wrong_candidate_fails(self): self.fails(self.merge(self.tree,self.base,self.unrelated))
    def test_related_but_wrong_candidate_fails(self): self.fails(self.merge(self.tree,self.base,self.related_candidate))
    def test_wrong_tree_fails(self): self.fails(self.merge(self.related_tree,self.base,self.candidate))
    def test_one_parent_fails(self): self.fails(self.git("commit-tree",self.tree,"-p",self.base,"-m",f"integration\n\nGovernance-Authorization: {self.auth}"))
    def test_unpublished_authorization_fails(self):
        self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}"); self.fails(self.integration)

if __name__ == "__main__": unittest.main()
