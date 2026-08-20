"""Validate immutable Gate Records, append-only edges, and finding lifecycles."""
from __future__ import annotations
import argparse,json,re,subprocess,sys
from datetime import datetime
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{40}$"); ID=re.compile(r"^GATE-[A-Z0-9][A-Z0-9-]{2,63}$")
FORMAL_GATES={"Independent Code Review","QA","Security Review","Release"}; GATES=FORMAL_GATES|{"Implementation Repair"}
SEVERITIES={"BLOCKING","MAJOR","MINOR","SUGGESTION"}; RECORD_PATH=".github/governance/gate-record.json"
RECORD_FIELDS={"schema_version","gate_record_id","gate_type","agent_role","agent_id","pr_number","base_sha","candidate_sha","candidate_tree","timestamp","scope","checks","findings","repair_claims","rechecks","disposition","repository_state_changed","supersedes"}
FINDING_FIELDS={"finding_id","severity","summary","status"}; REPAIR_FIELDS={"source_gate_record_id","source_finding_id","repaired_candidate_sha","summary"}; RECHECK_FIELDS={"source_gate_record_id","source_finding_id","repair_gate_record_id","rechecked_candidate_sha","outcome"}
LEGACY_FIELDS={"schema_version","gate_record_id","gate_type","agent_role","agent_id","pr_number","base_sha","candidate_sha","candidate_tree","timestamp","scope","checks","findings","disposition","repository_state_changed","supersedes","superseded_by"}

def parse_time(value):
    try:
        result=datetime.fromisoformat(str(value).replace("Z","+00:00")); return result if result.tzinfo else None
    except ValueError:return None
def nonempty(value):return isinstance(value,str) and bool(value.strip())
def valid_sha(value):return isinstance(value,str) and SHA.fullmatch(value) is not None

def validate_finding(f):
    if not isinstance(f,dict):return ["finding must be an object"]
    p=[]
    if set(f)!=FINDING_FIELDS:p.append("finding fields must exactly match schema")
    if not nonempty(f.get("finding_id")):p.append("finding_id must be non-empty")
    if f.get("severity") not in SEVERITIES:p.append("invalid finding severity")
    if not nonempty(f.get("summary")):p.append("finding summary must be non-empty")
    if f.get("status")!="OPEN":p.append("published findings are append-only OPEN facts; closure belongs in a recheck edge")
    return p
def validate_repair(c):
    if not isinstance(c,dict):return ["repair claim must be an object"]
    p=[]
    if set(c)!=REPAIR_FIELDS:p.append("repair claim fields must exactly match schema")
    for f in ("source_gate_record_id","source_finding_id","summary"):
        if not nonempty(c.get(f)):p.append(f"repair claim {f} must be non-empty")
    if not valid_sha(c.get("repaired_candidate_sha")):p.append("repair claim candidate must be a full SHA")
    return p
def validate_recheck(c):
    if not isinstance(c,dict):return ["recheck must be an object"]
    p=[]
    if set(c)!=RECHECK_FIELDS:p.append("recheck fields must exactly match schema")
    for f in ("source_gate_record_id","source_finding_id","repair_gate_record_id"):
        if not nonempty(c.get(f)):p.append(f"recheck {f} must be non-empty")
    if not valid_sha(c.get("rechecked_candidate_sha")):p.append("recheck candidate must be a full SHA")
    if c.get("outcome") not in {"PASS","FAIL"}:p.append("recheck outcome must be PASS or FAIL")
    return p

def validate_record(r):
    if not isinstance(r,dict):return ["record must be an object"]
    if r.get("schema_version")==1:return validate_legacy_record(r)
    p=[]
    if set(r)!=RECORD_FIELDS:p.append("record fields must exactly match schema")
    if r.get("schema_version")!=2:p.append("schema_version must be 2")
    if not isinstance(r.get("gate_record_id"),str) or not ID.fullmatch(r["gate_record_id"]):p.append("invalid gate_record_id")
    if r.get("gate_type") not in GATES or r.get("agent_role")!=r.get("gate_type"):p.append("invalid or mismatched gate role")
    if not nonempty(r.get("agent_id")) or not nonempty(r.get("scope")):p.append("agent_id and scope must be non-empty")
    if not isinstance(r.get("pr_number"),int) or r["pr_number"]<1:p.append("pr_number must be positive")
    for f in ("base_sha","candidate_sha","candidate_tree"):
        if not valid_sha(r.get(f)):p.append(f"{f} must be a full SHA")
    if parse_time(r.get("timestamp")) is None:p.append("timestamp must be timezone-aware ISO-8601")
    if not isinstance(r.get("checks"),list) or not r["checks"] or not all(nonempty(x) for x in r["checks"]):p.append("checks must be a non-empty string array")
    if r.get("disposition") not in {"PASS","FAIL","PENDING","N/A"}:p.append("invalid disposition")
    if not isinstance(r.get("repository_state_changed"),bool):p.append("repository_state_changed must be boolean")
    for field,validator in (("findings",validate_finding),("repair_claims",validate_repair),("rechecks",validate_recheck)):
        if not isinstance(r.get(field),list):p.append(f"{field} must be an array")
        else:
            for i,item in enumerate(r[field]):p.extend(f"{field}[{i}]: {x}" for x in validator(item))
    if isinstance(r.get("findings"),list):
        ids=[f.get("finding_id") for f in r["findings"] if isinstance(f,dict)]
        if len(ids)!=len(set(ids)):p.append("finding IDs must be unique per record")
    if not isinstance(r.get("supersedes"),list) or len(r["supersedes"])!=len(set(r["supersedes"])) or not all(isinstance(x,str) and ID.fullmatch(x) for x in r.get("supersedes",[])):p.append("supersedes must be a unique Gate Record ID array")
    if r.get("gate_type")=="Implementation Repair" and (not r.get("repository_state_changed") or not r.get("repair_claims")):p.append("Implementation Repair must record a repository change and repair claim")
    if r.get("gate_type")!="Implementation Repair" and r.get("repair_claims"):p.append("only Implementation Repair may publish repair claims")
    if r.get("repository_state_changed") and r.get("gate_type")!="Implementation Repair":p.append("formal review/QA/Security/Release records must not change repository state")
    return p
def validate_legacy_record(r):
    p=[]
    if set(r)!=LEGACY_FIELDS:p.append("legacy record fields are malformed")
    if r.get("gate_type") not in FORMAL_GATES or r.get("agent_role")!=r.get("gate_type"):p.append("invalid legacy gate role")
    if not isinstance(r.get("gate_record_id"),str) or not ID.fullmatch(r["gate_record_id"]):p.append("invalid legacy record ID")
    for f in ("base_sha","candidate_sha","candidate_tree"):
        if not valid_sha(r.get(f)):p.append(f"invalid legacy {f}")
    if parse_time(r.get("timestamp")) is None:p.append("invalid legacy timestamp")
    if not isinstance(r.get("findings"),list):p.append("legacy findings must be an array")
    elif any(not isinstance(f,dict) or not nonempty(f.get("finding_id")) or f.get("severity") not in SEVERITIES or f.get("status") not in {"OPEN","CLOSED"} for f in r["findings"]):p.append("legacy findings are malformed")
    if r.get("supersedes") is not None and not (isinstance(r.get("supersedes"),str) and ID.fullmatch(r["supersedes"])):p.append("legacy supersedes must be null or one Gate Record ID")
    return p

def predecessor_ids(r):
    """Normalize supported historical successor fields into backward edges."""
    value=r.get("supersedes")
    if r.get("schema_version")==1:return [value] if isinstance(value,str) else []
    return value if isinstance(value,list) else []

def finding_key(record,finding):return (record["gate_record_id"],finding["finding_id"])
def validate_graph(records,base,candidate,candidate_tree,pr,required,enforce_gates=True):
    p=[]; by_id={}
    for r in records:
        rid=r["gate_record_id"]
        if rid in by_id:p.append(f"duplicate Gate Record ID: {rid}"+(" with different content" if by_id[rid]!=r else ""))
        else:by_id[rid]=r
    incoming={rid:[] for rid in by_id}
    for r in records:
        for prior_id in predecessor_ids(r):
            prior=by_id.get(prior_id)
            if prior is None:p.append(f"missing predecessor: {prior_id}");continue
            incoming[prior_id].append(r["gate_record_id"])
            if prior_id==r["gate_record_id"]:p.append(f"self-reference: {prior_id}")
            if prior["pr_number"]!=r["pr_number"]:p.append(f"supersession changes PR: {prior_id}")
            if prior["gate_type"]!=r["gate_type"]:p.append(f"supersession changes gate type: {prior_id}")
            if parse_time(r["timestamp"])<=parse_time(prior["timestamp"]):p.append(f"supersession timestamp not ordered: {prior_id}")
    for rid,successors in incoming.items():
        if len(successors)>1:p.append(f"evidence fork at {rid}")
    def visit(rid,path):
        if rid in path:p.append(f"evidence cycle at {rid}");return
        r=by_id[rid]
        for prior in predecessor_ids(r):
            if prior in by_id:visit(prior,path|{rid})
    for rid in by_id:visit(rid,set())
    repairs={}; successful=set()
    for r in records:
        if r.get("schema_version")!=2:continue
        for claim in r["repair_claims"]:
            source=by_id.get(claim["source_gate_record_id"]); key=(claim["source_gate_record_id"],claim["source_finding_id"])
            if source is None or not any(f.get("finding_id")==key[1] for f in source.get("findings",[])):p.append(f"repair references nonexistent finding: {key}")
            if claim["repaired_candidate_sha"]!=r["candidate_sha"]:p.append(f"repair candidate mismatch: {key}")
            repairs[(r["gate_record_id"],*key)]=(r,claim)
    for r in records:
        if r.get("schema_version")!=2:continue
        for recheck in r["rechecks"]:
            valid=True
            source=by_id.get(recheck["source_gate_record_id"]); repair=by_id.get(recheck["repair_gate_record_id"]); key=(recheck["source_gate_record_id"],recheck["source_finding_id"])
            if source is None or not any(f.get("finding_id")==key[1] for f in source.get("findings",[])):p.append(f"recheck references nonexistent finding: {key}");continue
            claim_pair=repairs.get((recheck["repair_gate_record_id"],*key))
            if repair is None or claim_pair is None:p.append(f"recheck lacks exact repair claim: {key}");continue
            if r["gate_record_id"] in {source["gate_record_id"],repair["gate_record_id"]}:p.append(f"same record used as defect/repair/recheck: {key}");valid=False
            if r["agent_id"] in {source["agent_id"],repair["agent_id"]}:p.append(f"rechecker is not a distinct recorded agent: {key}");valid=False
            if r["gate_type"]!=source["gate_type"] or r["gate_type"] not in FORMAL_GATES-{"Release"}:p.append(f"wrong gate type performs recheck: {key}");valid=False
            if recheck["rechecked_candidate_sha"]!=repair["candidate_sha"] or r["candidate_sha"]!=repair["candidate_sha"]:p.append(f"stale-candidate recheck: {key}");valid=False
            if parse_time(r["timestamp"])<=parse_time(repair["timestamp"]):p.append(f"recheck predates repair: {key}");valid=False
            if recheck["outcome"]=="PASS" and valid:successful.add(key)
    if enforce_gates:
        for r in records:
            for f in r.get("findings",[]):
                if f.get("severity") in {"BLOCKING","MAJOR"} and f.get("status")!="CLOSED" and finding_key(r,f) not in successful:p.append(f"OPEN {f['severity']} remains blocking: {r['gate_record_id']}/{f['finding_id']}")
    referenced={x for r in records for x in predecessor_ids(r)}; active=[r for r in records if r["gate_record_id"] not in referenced]
    if not enforce_gates:return p
    for gate in required:
        matches=[r for r in active if r["gate_type"]==gate]
        if len(matches)!=1:p.append(f"gate must have exactly one active record: {gate}");continue
        r=matches[0]
        if r["disposition"]!="PASS":p.append(f"active Gate Record is not PASS: {gate}")
        if (r["base_sha"],r["candidate_sha"],r["candidate_tree"],r["pr_number"])!=(base,candidate,candidate_tree,pr):p.append(f"stale active Gate Record: {gate}")
    agents=[r["agent_id"] for r in active if r["gate_type"] in required]
    if len(agents)!=len(set(agents)):p.append("required active gates must have distinct recorded agent IDs")
    return p

def git(*args):
    result=subprocess.run(("git",*args),capture_output=True,text=True,check=False)
    if result.returncode:raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def gate_refs(r):
    suffix=f"pr-{r['pr_number']}/{r['candidate_sha']}/{r['gate_record_id']}";return f"refs/governance/gate-records/{suffix}",f"refs/remotes/origin/governance-gate-records/{suffix}"
def validate_record_object(r,commit):
    p=[]
    try:
        if not valid_sha(commit) or git("cat-file","-t",commit)!="commit":return ["Gate Record object must be a commit SHA"]
        if git("show","-s","--format=%P",commit).split()!=[r["candidate_sha"]]:p.append("Gate Record commit sole parent must equal candidate")
        if json.loads(git("show",f"{commit}:{RECORD_PATH}"))!=r:p.append("PR-visible JSON does not match authoritative object")
        found=[]
        for ref in gate_refs(r):
            result=subprocess.run(("git","show-ref","--verify","--hash",ref),capture_output=True,text=True,check=False)
            if result.returncode==0:found.append(result.stdout.strip())
        if not found:p.append("exact Gate Record ref missing")
        elif any(x!=commit for x in found):p.append("exact Gate Record ref points elsewhere")
    except (ValueError,json.JSONDecodeError) as e:p.append(f"invalid Gate Record object: {e}")
    return p
def validate_set(records,base,candidate,candidate_tree,pr,required,commits=None,enforce_gates=True):
    p=[]
    for r in records:p.extend(f"{r.get('gate_record_id')}: {x}" for x in validate_record(r))
    if p:return p
    p.extend(validate_graph(records,base,candidate,candidate_tree,pr,required,enforce_gates))
    if commits is not None:
        if set(commits)!=set(r["gate_record_id"] for r in records):p.append("record/object ID sets disagree")
        for r in records:
            if r["gate_record_id"] not in commits:p.append(f"missing record object: {r['gate_record_id']}")
            else:p.extend(f"{r['gate_record_id']}: {x}" for x in validate_record_object(r,commits[r["gate_record_id"]]))
    return p

def main():
    a=argparse.ArgumentParser();a.add_argument("record_files",nargs="+");a.add_argument("--record-commit",action="append",default=[]);a.add_argument("--base",required=True);a.add_argument("--candidate",required=True);a.add_argument("--tree",required=True);a.add_argument("--pr",type=int,required=True);a.add_argument("--require",nargs="+",choices=sorted(FORMAL_GATES),required=True);x=a.parse_args()
    records=[json.loads(Path(f).read_text()) for f in x.record_files];commits=dict(v.split("=",1) for v in x.record_commit);p=validate_set(records,x.base,x.candidate,x.tree,x.pr,set(x.require),commits or None)
    if p:print("Gate Record validation failed:");[print(f"- {e}") for e in p];return 1
    print("Gate Record validation passed.");return 0
if __name__=="__main__":sys.exit(main())
