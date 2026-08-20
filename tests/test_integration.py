import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from tests.test_gate_records import record
from verify_integration import verify_authorization,verify_integration
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
if __name__=="__main__":unittest.main()
