import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from validate_gate_records import validate_record,validate_set,validate_record_object
BASE,CANDIDATE,TREE="1"*40,"2"*40,"3"*40

def finding(fid="F-1",severity="MAJOR",status="OPEN",recheck=None): return {"finding_id":fid,"severity":severity,"summary":"factory defect","status":status,"rechecked_by_gate_record_id":recheck}
def record(rid="GATE-REVIEW-001",gate="Independent Code Review",agent="reviewer",candidate=CANDIDATE,when="2026-08-20T12:00:00Z",disposition="PASS",findings=None,supersedes=None,superseded_by=None):
    return {"schema_version":1,"gate_record_id":rid,"gate_type":gate,"agent_role":gate,"agent_id":agent,"pr_number":1,"base_sha":BASE,"candidate_sha":candidate,"candidate_tree":TREE,"timestamp":when,"scope":"complete candidate","checks":["factory suite"],"findings":findings or [],"disposition":disposition,"repository_state_changed":False,"supersedes":supersedes,"superseded_by":superseded_by}

class GateSchemaAndGraphTests(unittest.TestCase):
    def assert_invalid(self,r): self.assertTrue(validate_record(r))
    def test_valid_record(self): self.assertEqual([],validate_record(record()))
    def test_malformed_nested_finding(self): r=record(findings=[{"finding_id":"F"}]); self.assert_invalid(r)
    def test_invalid_severity(self): r=record(findings=[finding(severity="CRITICAL")]); self.assert_invalid(r)
    def test_invalid_status(self): r=record(findings=[finding(status="DONE")]); self.assert_invalid(r)
    def test_duplicate_finding_ids(self): r=record(findings=[finding(),finding()]); self.assert_invalid(r)
    def test_extra_finding_field(self): f=finding(); f["extra"]=True; self.assert_invalid(record(findings=[f]))
    def test_fake_superseded_by_missing_successor(self): self.assertTrue(validate_set([record(superseded_by="GATE-REVIEW-002")],BASE,CANDIDATE,TREE,1,{"Independent Code Review"}))
    def test_nonreciprocal_supersession(self):
        a=record(superseded_by="GATE-REVIEW-002",findings=[finding()]); b=record("GATE-REVIEW-002",candidate="4"*40,when="2026-08-20T13:00:00Z")
        self.assertTrue(validate_set([a,b],BASE,"4"*40,TREE,1,{"Independent Code Review"}))
    def test_supersession_cycle(self):
        a=record(supersedes="GATE-REVIEW-002",superseded_by="GATE-REVIEW-002"); b=record("GATE-REVIEW-002",candidate="4"*40,when="2026-08-20T13:00:00Z",supersedes="GATE-REVIEW-001",superseded_by="GATE-REVIEW-001")
        self.assertTrue(validate_set([a,b],BASE,CANDIDATE,TREE,1,{"Independent Code Review"}))
    def test_wrong_gate_type_successor(self):
        a=record(superseded_by="GATE-QA-002",findings=[finding()]); b=record("GATE-QA-002","QA","qa","4"*40,"2026-08-20T13:00:00Z",supersedes="GATE-REVIEW-001")
        self.assertTrue(validate_set([a,b],BASE,"4"*40,TREE,1,{"QA"}))
    def test_stale_candidate_successor(self):
        a=record(superseded_by="GATE-REVIEW-002",findings=[finding()]); b=record("GATE-REVIEW-002",candidate="4"*40,when="2026-08-20T13:00:00Z",supersedes="GATE-REVIEW-001",findings=[finding(status="CLOSED",recheck="GATE-REVIEW-002")])
        self.assertTrue(validate_set([a,b],BASE,CANDIDATE,TREE,1,{"Independent Code Review"}))
    def test_open_major_hidden_by_supersession_fails(self):
        a=record(disposition="FAIL",findings=[finding()],superseded_by="GATE-REVIEW-002"); b=record("GATE-REVIEW-002",candidate="4"*40,when="2026-08-20T13:00:00Z",supersedes="GATE-REVIEW-001")
        self.assertTrue(validate_set([a,b],BASE,"4"*40,TREE,1,{"Independent Code Review"}))
    def test_valid_repaired_independently_rechecked_chain(self):
        a=record(disposition="FAIL",findings=[finding()],superseded_by="GATE-REVIEW-002"); b=record("GATE-REVIEW-002",candidate="4"*40,when="2026-08-20T13:00:00Z",supersedes="GATE-REVIEW-001",findings=[finding(status="CLOSED",recheck="GATE-REVIEW-002")])
        self.assertEqual([],validate_set([a,b],BASE,"4"*40,TREE,1,{"Independent Code Review"}))
    def test_duplicate_id_different_content_fails(self):
        a=record(); b=copy.deepcopy(a); b["scope"]="different"; self.assertTrue(validate_set([a,b],BASE,CANDIDATE,TREE,1,{"Independent Code Review"}))
    def test_role_separation_across_active_records(self):
        self.assertTrue(validate_set([record(),record("GATE-QA-001","QA","reviewer")],BASE,CANDIDATE,TREE,1,{"Independent Code Review","QA"}))

class GateRecordObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.repo=Path(cls.temp.name); cls.old=os.getcwd(); os.chdir(cls.repo)
        cls.git("init","-q"); cls.git("config","user.name","Factory"); cls.git("config","user.email","factory@example.invalid")
        cls.write("candidate.txt","candidate"); cls.git("add","--all"); cls.git("commit","-q","-m","candidate"); cls.candidate=cls.git("rev-parse","HEAD"); cls.tree=cls.git("rev-parse","HEAD^{tree}")
    @classmethod
    def tearDownClass(cls): os.chdir(cls.old); cls.temp.cleanup()
    @classmethod
    def git(cls,*a): return subprocess.run(("git",*a),check=True,capture_output=True,text=True).stdout.strip()
    @classmethod
    def write(cls,path,text): p=cls.repo/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    def make_object(self,r):
        self.git("checkout","-q",self.candidate); self.write(".github/governance/gate-record.json",json.dumps(r,sort_keys=True)); self.git("add","--all"); self.git("commit","-q","-m","gate record"); commit=self.git("rev-parse","HEAD")
        ref=f"refs/governance/gate-records/pr-{r['pr_number']}/{r['candidate_sha']}/{r['gate_record_id']}"; self.git("update-ref",ref,commit); return commit,ref
    def current(self): return record(candidate=self.candidate)|{"base_sha":BASE,"candidate_tree":self.tree}
    def test_exact_content_addressed_record_passes(self): r=self.current(); commit,_=self.make_object(r); self.assertEqual([],validate_record_object(r,commit))
    def test_comment_and_stored_record_mismatch_fails(self): r=self.current(); commit,_=self.make_object(r); changed=copy.deepcopy(r); changed["scope"]="mutated"; self.assertTrue(validate_record_object(changed,commit))
    def test_mutated_stored_record_fails(self): r=self.current(); commit,_=self.make_object(r); original=copy.deepcopy(r); r["checks"]=["mutated"]; self.assertTrue(validate_record_object(r,commit)); self.assertFalse(validate_record_object(original,commit))
    def test_wrong_record_object_hash_fails(self): r=self.current(); commit,_=self.make_object(r); wrong=self.git("commit-tree",self.tree,"-p",self.candidate,"-m","wrong"); self.assertTrue(validate_record_object(r,wrong))
    def test_record_from_another_candidate_fails(self): r=self.current(); commit,_=self.make_object(r); changed=copy.deepcopy(r); changed["candidate_sha"]="9"*40; self.assertTrue(validate_record_object(changed,commit))

if __name__=="__main__": unittest.main()
