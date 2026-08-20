import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
from validate_gate_records import validate_record, validate_set

SHA1, SHA2, TREE = "1"*40, "2"*40, "3"*40
def record(gate="Independent Code Review", agent="reviewer", candidate=SHA2, disposition="PASS"):
    return {"schema_version":1,"gate_record_id":"GATE-TEST-001-"+gate.replace(" ","-").upper(),"gate_type":gate,"agent_role":gate,"agent_id":agent,"pr_number":1,"base_sha":SHA1,"candidate_sha":candidate,"candidate_tree":TREE,"timestamp":"2026-08-20T12:00:00Z","scope":"complete candidate","checks":["diff and tests"],"findings":[],"disposition":disposition,"repository_state_changed":False,"supersedes":None,"superseded_by":None}

class GateRecordTests(unittest.TestCase):
    def test_schema_valid(self): self.assertEqual([], validate_record(record()))
    def test_missing_field_fails(self): r=record(); del r["agent_id"]; self.assertTrue(validate_record(r))
    def test_stale_candidate_fails(self): self.assertTrue(validate_set([record(candidate="4"*40)], SHA1, SHA2, TREE, 1, {"Independent Code Review"}))
    def test_distinct_gate_agents_required(self):
        records=[record(),record("QA","reviewer")]
        self.assertTrue(validate_set(records,SHA1,SHA2,TREE,1,{"Independent Code Review","QA"}))
    def test_current_distinct_records_pass(self):
        records=[record(),record("QA","qa")]
        self.assertEqual([],validate_set(records,SHA1,SHA2,TREE,1,{"Independent Code Review","QA"}))
    def test_open_major_in_fail_record_blocks(self):
        failed=record("QA","qa",disposition="FAIL"); failed["findings"]=[{"finding_id":"F-1","severity":"MAJOR","summary":"broken","status":"OPEN"}]
        self.assertTrue(validate_set([record(),failed],SHA1,SHA2,TREE,1,{"Independent Code Review","QA"}))
    def test_closed_major_requires_recheck_record(self):
        reviewed=record(); reviewed["findings"]=[{"finding_id":"F-1","severity":"MAJOR","summary":"fixed","status":"CLOSED","rechecked_by_gate_record_id":"GATE-MISSING"}]
        self.assertTrue(validate_set([reviewed],SHA1,SHA2,TREE,1,{"Independent Code Review"}))

if __name__ == "__main__": unittest.main()
