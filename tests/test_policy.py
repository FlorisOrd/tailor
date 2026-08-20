import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"));import validate_governance as v
POLICY=json.loads((ROOT/".github/governance/policy.json").read_text())
class PolicyTests(unittest.TestCase):
 def test_policy_passes(self):p=[];v.validate_policy(POLICY,p);self.assertEqual([],p)
def add(name,path,value):
 def test(self):
  x=copy.deepcopy(POLICY);target=x
  for key in path[:-1]:target=target[key]
  target[path[-1]]=value;p=[];v.validate_policy(x,p);self.assertTrue(p,name)
 setattr(PolicyTests,"test_weaken_"+name,test)
for section,data in POLICY.items():
 if isinstance(data,dict):
  for key,value in data.items():
   if value is True:add(section+"_"+key,(section,key),False)
add("specification_frozen",("specification_frozen",),False)
add("lead_transcription",("roles","lead_transcription_is_gate_evidence"),True)
add("required_review",("roles","required"),["Implementation","QA","Release"])
add("required_security_gate",("current_gate_records","required_types"),["Independent Code Review","QA","Release"])
add("wrong_gate_namespace",("current_gate_records","canonical_ref_prefix"),"refs/wrong/")
add("wrong_authorization_namespace",("authorization","canonical_ref_prefix"),"refs/wrong/")
add("wrong_parent_count",("integration","parent_count"),1)
add("legacy_becomes_required",("historical_evidence","not_release_prerequisite"),False)
if __name__=="__main__":unittest.main()
