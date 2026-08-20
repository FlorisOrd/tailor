import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from validate_gate_records import validate_record,validate_set,validate_record_object
BASE,OLD,NEW,TREE="1"*40,"2"*40,"3"*40,"4"*40
def finding(fid="F-1",severity="MAJOR"):return {"finding_id":fid,"severity":severity,"summary":"defect","status":"OPEN"}
def record(rid="GATE-REVIEW-001",gate="Independent Code Review",agent="reviewer-1",candidate=OLD,when="2026-08-20T10:00:00Z",findings=None,repairs=None,rechecks=None,supersedes=None,disposition="FAIL",changed=False):
 return {"schema_version":2,"gate_record_id":rid,"gate_type":gate,"agent_role":gate,"agent_id":agent,"pr_number":1,"base_sha":BASE,"candidate_sha":candidate,"candidate_tree":TREE,"timestamp":when,"scope":"factory","checks":["checks"],"findings":findings or [],"repair_claims":repairs or [],"rechecks":rechecks or [],"disposition":disposition,"repository_state_changed":changed,"supersedes":supersedes or []}
def repair(source="GATE-REVIEW-001",fid="F-1",candidate=NEW):return {"source_gate_record_id":source,"source_finding_id":fid,"repaired_candidate_sha":candidate,"summary":"repair implemented"}
def recheck(source="GATE-REVIEW-001",fid="F-1",repair_id="GATE-REPAIR-001",candidate=NEW,outcome="PASS"):return {"source_gate_record_id":source,"source_finding_id":fid,"repair_gate_record_id":repair_id,"rechecked_candidate_sha":candidate,"outcome":outcome}
def lifecycle(reviewer="reviewer-2",outcome="PASS",recheck_gate="Independent Code Review",recheck_candidate=NEW,recheck_fid="F-1"):
 source=record(findings=[finding()]);fixed=record("GATE-REPAIR-001","Implementation Repair","implementer",NEW,"2026-08-20T11:00:00Z",repairs=[repair()],disposition="PASS",changed=True);checked=record("GATE-REVIEW-002",recheck_gate,reviewer,recheck_candidate,"2026-08-20T12:00:00Z",rechecks=[recheck(fid=recheck_fid,candidate=recheck_candidate,outcome=outcome)],supersedes=["GATE-REVIEW-001"],disposition="PASS");return [source,fixed,checked]

class AppendOnlyLifecycleTests(unittest.TestCase):
 def test_record_schema_passes(self):self.assertEqual([],validate_record(record(findings=[finding()])))
 def test_malformed_nested_finding_fails(self):r=record(findings=[{"finding_id":"F"}]);self.assertTrue(validate_record(r))
 def test_invalid_severity_fails(self):r=record(findings=[finding(severity="CRITICAL")]);self.assertTrue(validate_record(r))
 def test_invalid_status_fails(self):f=finding();f["status"]="CLOSED";self.assertTrue(validate_record(record(findings=[f])))
 def test_duplicate_finding_ids_fail(self):self.assertTrue(validate_record(record(findings=[finding(),finding()])))
 def test_predecessor_never_needs_forward_mutation(self):self.assertNotIn("superseded_by",record())
 def test_successor_only_backward_link_valid_chain(self):self.assertEqual([],validate_set(lifecycle(),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_missing_predecessor_fails(self):r=record("GATE-REVIEW-002",candidate=NEW,supersedes=["GATE-MISSING"],disposition="PASS");self.assertTrue(validate_set([r],BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_fork_fails(self):
  source=record(findings=[finding()]);a=record("GATE-REVIEW-002",agent="a",candidate=NEW,when="2026-08-20T12:00:00Z",supersedes=[source["gate_record_id"]]);b=record("GATE-REVIEW-003",agent="b",candidate="5"*40,when="2026-08-20T13:00:00Z",supersedes=[source["gate_record_id"]]);self.assertTrue(validate_set([source,a,b],BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_cycle_fails(self):
  a=record(supersedes=["GATE-REVIEW-002"]);b=record("GATE-REVIEW-002",candidate=NEW,when="2026-08-20T09:00:00Z",supersedes=["GATE-REVIEW-001"]);self.assertTrue(validate_set([a,b],BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_self_reference_fails(self):r=record(supersedes=["GATE-REVIEW-001"]);self.assertTrue(validate_set([r],BASE,OLD,TREE,1,{"Independent Code Review"}))
 def test_repair_claim_alone_still_blocks(self):source=record(findings=[finding()]);fixed=lifecycle()[1];self.assertTrue(validate_set([source,fixed],BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_same_agent_recheck_rejected(self):self.assertTrue(validate_set(lifecycle(reviewer="reviewer-1"),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_implementation_rechecks_rejected(self):self.assertTrue(validate_set(lifecycle(reviewer="other",recheck_gate="Implementation Repair"),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_wrong_gate_type_recheck_rejected(self):self.assertTrue(validate_set(lifecycle(recheck_gate="QA"),BASE,NEW,TREE,1,{"QA"}))
 def test_failed_recheck_remains_blocking(self):self.assertTrue(validate_set(lifecycle(outcome="FAIL"),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_unrelated_pass_cannot_close(self):source=record(findings=[finding()]);unrelated=record("GATE-REVIEW-002",agent="other",candidate=NEW,when="2026-08-20T12:00:00Z",supersedes=[source["gate_record_id"]],disposition="PASS");self.assertTrue(validate_set([source,unrelated],BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_stale_candidate_recheck_fails(self):self.assertTrue(validate_set(lifecycle(recheck_candidate="6"*40),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_wrong_finding_id_recheck_fails(self):self.assertTrue(validate_set(lifecycle(recheck_fid="OTHER"),BASE,NEW,TREE,1,{"Independent Code Review"}))
 def test_duplicate_id_different_content_fails(self):a=record();b=copy.deepcopy(a);b["scope"]="different";self.assertTrue(validate_set([a,b],BASE,OLD,TREE,1,{"Independent Code Review"}))

class ContentAddressTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.repo=Path(cls.temp.name);cls.old=os.getcwd();os.chdir(cls.repo);cls.git("init","-q");cls.git("config","user.name","Factory");cls.git("config","user.email","factory@example.invalid");cls.write("x","x");cls.git("add","--all");cls.git("commit","-q","-m","candidate");cls.candidate=cls.git("rev-parse","HEAD");cls.tree=cls.git("rev-parse","HEAD^{tree}")
 @classmethod
 def tearDownClass(cls):os.chdir(cls.old);cls.temp.cleanup()
 @classmethod
 def git(cls,*a):return subprocess.run(("git",*a),check=True,capture_output=True,text=True).stdout.strip()
 @classmethod
 def write(cls,path,text):p=cls.repo/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 def make(self,r):self.git("checkout","-q",self.candidate);self.write(".github/governance/gate-record.json",json.dumps(r));self.git("add","--all");self.git("commit","-q","-m","record");c=self.git("rev-parse","HEAD");self.git("update-ref",f"refs/governance/gate-records/pr-1/{self.candidate}/{r['gate_record_id']}",c);return c
 def current(self):return record(candidate=self.candidate,findings=[],disposition="PASS")|{"candidate_tree":self.tree}
 def test_exact_object_passes(self):r=self.current();c=self.make(r);self.assertEqual([],validate_record_object(r,c))
 def test_visible_json_mutation_fails(self):r=self.current();c=self.make(r);r["scope"]="changed";self.assertTrue(validate_record_object(r,c))
 def test_wrong_object_fails(self):r=self.current();c=self.make(r);wrong=self.git("commit-tree",self.tree,"-p",self.candidate,"-m","wrong");self.assertTrue(validate_record_object(r,wrong))
 def test_other_candidate_fails(self):r=self.current();c=self.make(r);r["candidate_sha"]="9"*40;self.assertTrue(validate_record_object(r,c))
if __name__=="__main__":unittest.main()
