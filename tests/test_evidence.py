import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from validate_evidence import reconcile_selected
from tests.test_gate_records import record
def comment(r,c,i=1):return {"id":i,"body":f"Bootstrap-Gate-Commit: {c}\n\n```bootstrap-gate\n{json.dumps(r)}\n```"}
class SelectedEvidenceTests(unittest.TestCase):
 def setUp(self):self.r=record();self.c="a"*40;self.records={"Independent Code Review":self.r};self.commits={"Independent Code Review":self.c}
 def test_exact_selected_declaration_passes(self):self.assertEqual([],reconcile_selected([comment(self.r,self.c)],self.records,self.commits))
 def test_missing_declaration_fails(self):self.assertTrue(reconcile_selected([],self.records,self.commits))
 def test_changed_visible_json_fails(self):x=copy.deepcopy(self.r);x["scope"]="changed";self.assertTrue(reconcile_selected([comment(x,self.c)],self.records,self.commits))
 def test_duplicate_selected_declaration_fails(self):self.assertTrue(reconcile_selected([comment(self.r,self.c),comment(self.r,self.c,2)],self.records,self.commits))
 def test_lead_transcribed_visible_record_fails(self):x=copy.deepcopy(self.r);x["publisher_agent_id"]="lead";self.assertTrue(reconcile_selected([comment(x,self.c)],{"Independent Code Review":x},self.commits))
 def test_historical_comments_are_ignored(self):old={"id":9,"body":"```gate-record\n{\"schema_version\":1}\n```"};self.assertEqual([],reconcile_selected([old,comment(self.r,self.c)],self.records,self.commits))
if __name__=="__main__":unittest.main()
