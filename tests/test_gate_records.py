import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from validate_gate_records import validate_current_set,validate_record
BASE,CANDIDATE,TREE="1"*40,"2"*40,"3"*40
def finding(severity="MINOR"):return {"finding_id":"F-1","severity":severity,"summary":"finding"}
def record(gate="Independent Code Review",agent="review",**kw):
 r={"schema_version":1,"record_type":"Bootstrap Governance v0 Gate Record","gate_record_id":"BOOTSTRAP-GATE-"+gate.upper().replace(" ","-"),"gate_type":gate,"agent_role":gate,"agent_id":agent,"publisher_agent_id":agent,"pr_number":1,"base_sha":BASE,"candidate_sha":CANDIDATE,"candidate_tree":TREE,"timestamp":"2026-08-20T12:00:00Z","scope":"current candidate","checks":["verified"],"findings":[],"disposition":"PASS"};r.update(kw);return r
def current():
 rs=[record(),record("QA","qa"),record("Security Review","security"),record("Release","release")];return rs,{r["gate_type"]:str(i+4)*40 for i,r in enumerate(rs)}
class BootstrapGateTests(unittest.TestCase):
 def validate(self,rs=None,cs=None,**kw):
  rs0,cs0=current();return validate_current_set(rs or rs0,cs or cs0,BASE,CANDIDATE,TREE,1,"implementation","lead",require_refs=False,validate_objects=False,**kw)
 def test_current_set_passes(self):self.assertEqual([],self.validate())
 def test_missing_review_fails(self):rs,cs=current();rs=rs[1:];cs.pop("Independent Code Review");self.assertTrue(self.validate(rs,cs))
 def test_missing_qa_fails(self):rs,cs=current();rs=[x for x in rs if x["gate_type"]!="QA"];cs.pop("QA");self.assertTrue(self.validate(rs,cs))
 def test_missing_security_fails(self):rs,cs=current();rs=[x for x in rs if x["gate_type"]!="Security Review"];cs.pop("Security Review");self.assertTrue(self.validate(rs,cs))
 def test_missing_release_fails(self):rs,cs=current();rs=rs[:-1];cs.pop("Release");self.assertTrue(self.validate(rs,cs))
 def test_implementation_cannot_review(self):rs,cs=current();rs[0]["agent_id"]=rs[0]["publisher_agent_id"]="implementation";self.assertTrue(self.validate(rs,cs))
 def test_implementation_cannot_qa(self):rs,cs=current();rs[1]["agent_id"]=rs[1]["publisher_agent_id"]="implementation";self.assertTrue(self.validate(rs,cs))
 def test_implementation_cannot_release(self):rs,cs=current();rs[3]["agent_id"]=rs[3]["publisher_agent_id"]="implementation";self.assertTrue(self.validate(rs,cs))
 def test_duplicate_roles_fail(self):rs,cs=current();rs[1]["agent_id"]=rs[1]["publisher_agent_id"]="review";self.assertTrue(self.validate(rs,cs))
 def test_security_independence_fails(self):rs,cs=current();rs[2]["agent_id"]=rs[2]["publisher_agent_id"]="lead";self.assertTrue(self.validate(rs,cs))
 def test_wrong_base_fails(self):rs,cs=current();rs[0]["base_sha"]="9"*40;self.assertTrue(self.validate(rs,cs))
 def test_wrong_candidate_fails(self):rs,cs=current();rs[0]["candidate_sha"]="9"*40;self.assertTrue(self.validate(rs,cs))
 def test_wrong_tree_fails(self):rs,cs=current();rs[0]["candidate_tree"]="9"*40;self.assertTrue(self.validate(rs,cs))
 def test_stale_evidence_fails(self):self.assertTrue(validate_current_set(*current(),BASE,"9"*40,TREE,1,"implementation","lead",require_refs=False,validate_objects=False))
 def test_blocking_cannot_pass(self):self.assertTrue(validate_record(record(findings=[finding("BLOCKING")])))
 def test_major_cannot_pass(self):self.assertTrue(validate_record(record(findings=[finding("MAJOR")])))
 def test_fail_cannot_satisfy_gate(self):rs,cs=current();rs[0]["disposition"]="FAIL";self.assertTrue(self.validate(rs,cs))
 def test_malformed_record_fails(self):r=record();r.pop("scope");self.assertTrue(validate_record(r))
 def test_lead_transcription_fails(self):r=record();r["publisher_agent_id"]="lead";self.assertTrue(validate_record(r))
 def test_historical_schema_is_not_current(self):r=record();r["record_type"]="old";self.assertTrue(validate_record(r))
if __name__=="__main__":unittest.main()
