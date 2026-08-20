import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from tests.test_gate_records import record
from verify_integration import validate_live_authorization,verify_authorization,verify_integration
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name);self.old=os.getcwd();os.chdir(self.repo);self.git("init","-q");self.git("config","user.name","Factory");self.git("config","user.email","factory@example.invalid");self.write("base.txt","base");self.git("add","--all");self.git("commit","-q","-m","base");self.base=self.git("rev-parse","HEAD");self.write("change.txt","candidate");self.git("add","--all");self.git("commit","-q","-m","candidate");self.candidate=self.git("rev-parse","HEAD");self.tree=self.git("rev-parse","HEAD^{tree}");self.records={};self.commits={}
  agents={"Independent Code Review":"review","QA":"qa","Security Review":"security","Release":"release"}
  for gate,agent in agents.items():
   r=record(gate,agent,base_sha=self.base,candidate_sha=self.candidate,candidate_tree=self.tree);c=self.object_commit(".github/governance/gate-record.json",r,self.candidate,"gate");self.git("update-ref",f"refs/governance/bootstrap-gates/pr-1/{self.candidate}/{gate.lower().replace(' ','-')}/{r['gate_record_id']}",c);self.records[gate]=r;self.commits[gate]=c
  self.auth=self.authorization();self.integration=self.merge(self.base,self.candidate,self.tree,self.auth)
 def tearDown(self):os.chdir(self.old);self.temp.cleanup()
 def git(self,*a,input=None):return subprocess.run(("git",*a),input=input,check=True,capture_output=True,text=True).stdout.strip()
 def write(self,path,text):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 def object_commit(self,path,obj,parent,message):
  index=self.repo/(message+".index");env=os.environ|{"GIT_INDEX_FILE":str(index)};subprocess.run(("git","read-tree",parent),check=True,env=env);blob=subprocess.run(("git","hash-object","-w","--stdin"),input=json.dumps(obj),text=True,capture_output=True,check=True).stdout.strip();subprocess.run(("git","update-index","--add","--cacheinfo","100644",blob,path),check=True,env=env);tree=subprocess.run(("git","write-tree"),capture_output=True,text=True,check=True,env=env).stdout.strip();return self.git("commit-tree",tree,"-p",parent,"-m",message)
 def authorization(self,**changes):
  a={"schema_version":1,"record_type":"Bootstrap Governance v0 Merge Authorization","authorization_id":"AUTH-1","pr_number":1,"base_sha":self.base,"candidate_sha":self.candidate,"candidate_tree":self.tree,"timestamp":"2026-08-20T12:00:00Z","implementation_agent_id":"implementation","lead_agent_id":"lead","release_agent_id":"release","ci_run_id":123,"ci_candidate_sha":self.candidate,"gate_record_commits":self.commits};a.update(changes);c=self.object_commit(".github/governance/authorization.json",a,self.candidate,"auth"+str(len(list(self.repo.glob('auth*.index')))));self.git("update-ref",f"refs/governance/authorizations/pr-1/{a['candidate_sha']}",c);return c
 def merge(self,first,second,tree,auth):return self.git("commit-tree",tree,"-p",first,"-p",second,"-m",f"merge\n\nGovernance-PR: 1\nGovernance-Authorization: {auth}")
 def test_exact_integration_passes(self):verify_integration(self.integration)
 def test_exact_authorization_passes_before_merge(self):verify_authorization(self.auth)
 def test_missing_authorization_ref_fails(self):self.git("update-ref","-d",f"refs/governance/authorizations/pr-1/{self.candidate}");self.assertRaises(ValueError,verify_integration,self.integration)
 def test_moved_authorization_ref_fails(self):wrong=self.git("commit-tree",self.tree,"-p",self.candidate,"-m","wrong");self.git("update-ref",f"refs/governance/authorizations/pr-1/{self.candidate}",wrong);self.assertRaises(ValueError,verify_integration,self.integration)
 def test_wrong_authorization_candidate_fails(self):a=self.authorization(ci_candidate_sha="9"*40);m=self.merge(self.base,self.candidate,self.tree,a);self.assertRaises(ValueError,verify_integration,m)
 def test_wrong_first_parent_fails(self):m=self.merge(self.candidate,self.candidate,self.tree,self.auth);self.assertRaises(ValueError,verify_integration,m)
 def test_wrong_second_parent_fails(self):m=self.merge(self.base,self.base,self.tree,self.auth);self.assertRaises(ValueError,verify_integration,m)
 def test_wrong_integration_tree_fails(self):wrong=self.git("rev-parse",f"{self.base}^{{tree}}");m=self.merge(self.base,self.candidate,wrong,self.auth);self.assertRaises(ValueError,verify_integration,m)
 def test_missing_gate_ref_fails(self):r=self.records["QA"];self.git("update-ref","-d",f"refs/governance/bootstrap-gates/pr-1/{self.candidate}/qa/{r['gate_record_id']}");self.assertRaises(ValueError,verify_integration,self.integration)
 def test_wrong_gate_candidate_fails(self):self.records["QA"]["candidate_sha"]="9"*40;bad=self.object_commit(".github/governance/gate-record.json",self.records["QA"],self.candidate,"badgate");commits=self.commits|{"QA":bad};a=self.authorization(gate_record_commits=commits);m=self.merge(self.base,self.candidate,self.tree,a);self.assertRaises(ValueError,verify_integration,m)
 def live_pr(self,**changes):
  value={"number":1,"state":"open","merged":False,"base":{"ref":"main","sha":self.base},"head":{"ref":"candidate","sha":self.candidate,"repo":{"full_name":"owner/repo"}}};value.update(changes);return value
 def live_problems(self,pr=None,refs=None,auth=None):
  refs=refs or {"refs/heads/main":self.base,"refs/heads/candidate":self.candidate};auth=auth or {"pr_number":1,"base_sha":self.base,"candidate_sha":self.candidate,"candidate_tree":self.tree}
  with patch("verify_integration.github_json",return_value=pr or self.live_pr()),patch("verify_integration.remote_ref_sha",side_effect=lambda ref:refs[ref]):return validate_live_authorization("owner/repo","token",auth)
 def test_live_authorization_exact_tuple_passes(self):self.assertEqual([],self.live_problems())
 def test_live_authorization_self_consistent_base_equals_candidate_fails(self):self.assertTrue(self.live_problems(auth={"pr_number":1,"base_sha":self.candidate,"candidate_sha":self.candidate,"candidate_tree":self.tree}))
 def test_live_authorization_wrong_pr_base_sha_fails(self):self.assertTrue(self.live_problems(self.live_pr(base={"ref":"main","sha":"9"*40})))
 def test_live_authorization_wrong_pr_head_sha_fails(self):self.assertTrue(self.live_problems(self.live_pr(head={"ref":"candidate","sha":"9"*40,"repo":{"full_name":"owner/repo"}})))
 def test_live_authorization_related_wrong_candidate_fails(self):self.assertTrue(self.live_problems(auth={"pr_number":1,"base_sha":self.base,"candidate_sha":self.base,"candidate_tree":self.git("rev-parse",f"{self.base}^{{tree}}")}))
 def test_live_authorization_related_wrong_base_fails(self):self.assertTrue(self.live_problems(auth={"pr_number":1,"base_sha":self.candidate,"candidate_sha":self.candidate,"candidate_tree":self.tree}))
 def test_live_authorization_remote_main_moved_fails(self):self.assertTrue(self.live_problems(refs={"refs/heads/main":"9"*40,"refs/heads/candidate":self.candidate}))
 def test_live_authorization_remote_candidate_moved_fails(self):self.assertTrue(self.live_problems(refs={"refs/heads/main":self.base,"refs/heads/candidate":"9"*40}))
 def test_live_authorization_closed_pr_fails(self):self.assertTrue(self.live_problems(self.live_pr(state="closed")))
 def test_live_authorization_merged_pr_fails(self):self.assertTrue(self.live_problems(self.live_pr(merged=True)))
 def test_live_authorization_wrong_pr_number_fails(self):self.assertTrue(self.live_problems(self.live_pr(number=2)))
 def test_live_authorization_unavailable_pr_fails(self):
  with patch("verify_integration.github_json",side_effect=OSError("offline")):self.assertRaises(ValueError,validate_live_authorization,"owner/repo","token",{"pr_number":1})
 def test_live_authorization_unavailable_remote_ref_fails(self):
  with patch("verify_integration.github_json",return_value=self.live_pr()),patch("verify_integration.remote_ref_sha",side_effect=ValueError("missing")):self.assertTrue(validate_live_authorization("owner/repo","token",{"pr_number":1,"base_sha":self.base,"candidate_sha":self.candidate,"candidate_tree":self.tree}))
 def test_live_authorization_wrong_candidate_tree_fails(self):
  bad=self.authorization(candidate_tree="9"*40)
  with self.assertRaises(ValueError):verify_authorization(bad)
 def test_reconciled_authorization_rejects_matching_fake_base_candidate_tuple(self):
  fake_records={};fake_commits={}
  for gate,agent in {"Independent Code Review":"review","QA":"qa","Security Review":"security","Release":"release"}.items():
   item=record(gate,agent,base_sha=self.candidate,candidate_sha=self.candidate,candidate_tree=self.tree);commit=self.object_commit(".github/governance/gate-record.json",item,self.candidate,"fakegate"+gate.replace(" ",""));self.git("update-ref",f"refs/governance/bootstrap-gates/pr-1/{self.candidate}/{gate.lower().replace(' ','-')}/{item['gate_record_id']}",commit);fake_records[gate]=item;fake_commits[gate]=commit
  bad=self.authorization(base_sha=self.candidate,gate_record_commits=fake_commits)
  with patch.dict(os.environ,{"GITHUB_TOKEN":"token","GITHUB_REPOSITORY":"owner/repo"}),patch("verify_integration.validate_live_authorization",return_value=["live PR base SHA differs from authorization"]),patch("verify_integration.validate_selected_live",return_value=[]),patch("verify_integration.validate_ci_run",return_value=[]):self.assertRaises(ValueError,verify_authorization,bad,True)
 def test_reconciled_authorization_rejects_gate_not_matching_live_pr(self):
  with patch.dict(os.environ,{"GITHUB_TOKEN":"token","GITHUB_REPOSITORY":"owner/repo"}),patch("verify_integration.validate_live_authorization",return_value=[]),patch("verify_integration.validate_selected_live",return_value=["selected gate differs from live PR"]),patch("verify_integration.validate_ci_run",return_value=[]):self.assertRaises(ValueError,verify_authorization,self.auth,True)
 def test_reconciled_authorization_rejects_ci_for_another_sha(self):
  with patch.dict(os.environ,{"GITHUB_TOKEN":"token","GITHUB_REPOSITORY":"owner/repo"}),patch("verify_integration.validate_live_authorization",return_value=[]),patch("verify_integration.validate_selected_live",return_value=[]),patch("verify_integration.validate_ci_run",return_value=["selected CI run is stale or for another candidate"]):self.assertRaises(ValueError,verify_authorization,self.auth,True)
 def test_authorization_rejects_nonancestor_base(self):
  unrelated=self.git("commit-tree",self.git("rev-parse",f"{self.base}^{{tree}}"),"-m","unrelated");bad=self.authorization(base_sha=unrelated)
  with patch("verify_integration.validate_current_set",return_value=[]):self.assertRaises(ValueError,verify_authorization,bad)
if __name__=="__main__":unittest.main()
