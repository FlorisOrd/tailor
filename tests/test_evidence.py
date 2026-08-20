import copy,json,os,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from validate_evidence import fetch_remote_records,reconcile
BASE,CANDIDATE,TREE="1"*40,"2"*40,"3"*40
def record(rid,gate,agent):return {"schema_version":2,"gate_record_id":rid,"gate_type":gate,"agent_role":gate,"agent_id":agent,"pr_number":1,"base_sha":BASE,"candidate_sha":CANDIDATE,"candidate_tree":TREE,"timestamp":"2026-08-20T12:00:00Z","scope":"gate","checks":["checks"],"findings":[],"repair_claims":[],"rechecks":[],"disposition":"PASS","repository_state_changed":False,"supersedes":[]}
def comment(record,commit,cid=1):return {"id":cid,"user":{"login":"agent"},"body":f"Gate-Record-Commit: {commit}\n\n```gate-record\n{json.dumps(record,sort_keys=True)}\n```"}
def fixture():
 records=[record("GATE-REVIEW-001","Independent Code Review","r"),record("GATE-QA-001","QA","q"),record("GATE-SECURITY-001","Security Review","s")];commits={r["gate_record_id"]:str(i)*40 for i,r in enumerate(records,1)};comments=[comment(r,commits[r["gate_record_id"]],i) for i,r in enumerate(records,1)];return records,commits,comments
class VisibleReconciliationTests(unittest.TestCase):
 def check(self,comments,records,commits):return reconcile(comments,records,commits,BASE,CANDIDATE,TREE,1,{"Independent Code Review","QA","Security Review"})
 def test_exact_visible_equals_object_passes(self):r,c,v=fixture();self.assertEqual([],self.check(v,r,c))
 def test_changed_comment_json_fails(self):r,c,v=fixture();changed=copy.deepcopy(r[0]);changed["scope"]="mutated";v[0]=comment(changed,c[r[0]["gate_record_id"]]);self.assertTrue(self.check(v,r,c))
 def test_deleted_comment_fails(self):r,c,v=fixture();self.assertTrue(self.check(v[1:],r,c))
 def test_wrong_commit_declaration_fails(self):r,c,v=fixture();v[0]=comment(r[0],"9"*40);self.assertTrue(self.check(v,r,c))
 def test_visible_json_without_commit_declaration_fails(self):r,c,v=fixture();v[0]={"id":1,"body":f"```gate-record\n{json.dumps(r[0])}\n```"};self.assertTrue(self.check(v,r,c))
 def test_duplicate_id_different_content_fails(self):r,c,v=fixture();changed=copy.deepcopy(r[0]);changed["scope"]="different";v.append(comment(changed,c[r[0]["gate_record_id"]],99));self.assertTrue(self.check(v,r,c))
 def test_authoritative_record_missing_visible_fails(self):r,c,v=fixture();self.assertTrue(self.check(v[:-1],r,c))
 def test_visible_record_missing_authoritative_fails(self):r,c,v=fixture();self.assertTrue(self.check(v,r[:-1],{k:x for k,x in c.items() if k!=r[-1]["gate_record_id"]}))
 def test_another_candidate_visible_object_fails(self):r,c,v=fixture();changed=copy.deepcopy(r[0]);changed["candidate_sha"]="8"*40;v[0]=comment(changed,c[r[0]["gate_record_id"]]);self.assertTrue(self.check(v,r,c))

class RemoteDiscoveryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=os.getcwd();self.source=self.root/"source";self.remote=self.root/"remote.git";self.clone=self.root/"clone";self.source.mkdir();os.chdir(self.source);self.git("init","-q");self.git("config","user.name","Factory");self.git("config","user.email","factory@example.invalid");self.write("base","x");self.git("add","--all");self.git("commit","-q","-m","candidate");self.candidate=self.git("rev-parse","HEAD");self.tree=self.git("rev-parse","HEAD^{tree}");subprocess.run(("git","init","--bare","-q",str(self.remote)),check=True);self.git("remote","add","origin",str(self.remote))
 def tearDown(self):os.chdir(self.old);self.temp.cleanup()
 def git(self,*a):return subprocess.run(("git",*a),check=True,capture_output=True,text=True).stdout.strip()
 def write(self,path,text):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 def publish(self,r,ref_candidate=None):
  self.git("checkout","-q",self.candidate);self.write(".github/governance/gate-record.json",json.dumps(r));self.git("add","--all");self.git("commit","-q","-m",r["gate_record_id"]);commit=self.git("rev-parse","HEAD");ref=f"refs/governance/gate-records/pr-1/{ref_candidate or r['candidate_sha']}/{r['gate_record_id']}";self.git("push","-q","origin",f"{commit}:{ref}");return commit
 def setup_clone(self):subprocess.run(("git","clone","-q",str(self.remote),str(self.clone)),check=True);os.chdir(self.clone)
 def remote_record(self,rid):return record(rid,"Independent Code Review",rid)|{"base_sha":self.candidate,"candidate_sha":self.candidate,"candidate_tree":self.tree}
 def test_incomplete_local_refs_are_refetched_completely(self):
  self.publish(self.remote_record("GATE-REMOTE-001"));self.publish(self.remote_record("GATE-REMOTE-002"));self.setup_clone();records,commits,_=fetch_remote_records("origin",1);self.assertEqual(2,len(records));self.assertEqual(2,len(commits))
 def test_only_newest_locally_present_does_not_omit_history(self):
  a=self.publish(self.remote_record("GATE-REMOTE-001"));b=self.publish(self.remote_record("GATE-REMOTE-002"));self.setup_clone();self.git("fetch","-q","origin",b);records,_,_=fetch_remote_records("origin",1);self.assertEqual({"GATE-REMOTE-001","GATE-REMOTE-002"},{r["gate_record_id"] for r in records})
 def test_duplicate_ids_under_multiple_remote_refs_fail(self):
  r=self.remote_record("GATE-DUPLICATE-001");self.publish(r);changed=copy.deepcopy(r);changed["candidate_sha"]="9"*40;self.publish(changed);self.setup_clone();
  with self.assertRaises(ValueError):fetch_remote_records("origin",1)
 def test_record_for_another_pr_under_namespace_fails(self):
  r=self.remote_record("GATE-WRONG-PR");r["pr_number"]=2;self.publish(r);self.setup_clone();
  with self.assertRaises(ValueError):fetch_remote_records("origin",1)
 def test_missing_remote_object_fails(self):
  line=f"{'a'*40}\trefs/governance/gate-records/pr-1/{'b'*40}/GATE-MISSING-001"
  with patch("validate_evidence.remote_run",side_effect=[line,ValueError("missing remote object")]):
   with self.assertRaises(ValueError):fetch_remote_records("origin",1)
if __name__=="__main__":unittest.main()
