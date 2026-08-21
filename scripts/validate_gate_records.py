"""Validate fresh, candidate-specific Bootstrap Governance v0 Gate Records."""
from __future__ import annotations
import json,re,subprocess
from datetime import datetime

SHA=re.compile(r"^[0-9a-f]{40}$")
ID=re.compile(r"^BOOTSTRAP-GATE-[A-Z0-9-]+$")
GATES={"Independent Code Review","QA","Security Review","Release"}
SEVERITIES={"BLOCKING","MAJOR","MINOR","SUGGESTION"}
RECORD_PATH=".github/governance/gate-record.json"
FIELDS={"schema_version","record_type","gate_record_id","gate_type","agent_role","agent_id","publisher_agent_id","pr_number","base_sha","candidate_sha","candidate_tree","timestamp","scope","checks","findings","disposition"}
FINDING_FIELDS={"finding_id","severity","summary"}

def nonempty(value):return isinstance(value,str) and bool(value.strip())
def valid_sha(value):return isinstance(value,str) and SHA.fullmatch(value) is not None
def valid_time(value):
    try:return datetime.fromisoformat(str(value).replace("Z","+00:00")).tzinfo is not None
    except (ValueError,AttributeError):return False

def validate_record(record):
    if not isinstance(record,dict):return ["record must be an object"]
    p=[]
    if set(record)!=FIELDS:p.append("Gate Record fields do not match Bootstrap v0")
    if record.get("schema_version")!=1 or record.get("record_type")!="Bootstrap Governance v0 Gate Record":p.append("wrong Gate Record protocol")
    if not isinstance(record.get("gate_record_id"),str) or not ID.fullmatch(record["gate_record_id"]):p.append("invalid gate_record_id")
    if record.get("gate_type") not in GATES or record.get("agent_role")!=record.get("gate_type"):p.append("invalid or mismatched gate role")
    if not nonempty(record.get("agent_id")) or record.get("publisher_agent_id")!=record.get("agent_id"):p.append("gate agent must publish its own evidence")
    if not isinstance(record.get("pr_number"),int) or record.get("pr_number",0)<1:p.append("invalid PR number")
    for field in ("base_sha","candidate_sha","candidate_tree"):
        if not valid_sha(record.get(field)):p.append(f"invalid {field}")
    if not valid_time(record.get("timestamp")):p.append("invalid timestamp")
    if not nonempty(record.get("scope")):p.append("scope must be non-empty")
    if not isinstance(record.get("checks"),list) or not record.get("checks") or not all(nonempty(x) for x in record.get("checks",[])):p.append("checks must be non-empty strings")
    findings=record.get("findings")
    if not isinstance(findings,list):p.append("findings must be an array")
    else:
        ids=[]
        for finding in findings:
            if not isinstance(finding,dict) or set(finding)!=FINDING_FIELDS:p.append("malformed finding");continue
            ids.append(finding.get("finding_id"))
            if not nonempty(finding.get("finding_id")) or finding.get("severity") not in SEVERITIES or not nonempty(finding.get("summary")):p.append("invalid finding")
        if len(ids)!=len(set(ids)):p.append("duplicate finding ID")
    if record.get("disposition") not in {"PASS","FAIL"}:p.append("invalid disposition")
    if record.get("disposition")=="PASS" and isinstance(findings,list) and any(f.get("severity") in {"BLOCKING","MAJOR"} for f in findings if isinstance(f,dict)):p.append("PASS record contains a BLOCKING or MAJOR finding")
    return p

def canonical_ref(record):return f"refs/governance/bootstrap-gates/pr-{record['pr_number']}/{record['candidate_sha']}/{record['gate_type'].lower().replace(' ','-')}/{record['gate_record_id']}"
def git(*args):
    result=subprocess.run(("git",*args),capture_output=True,text=True,check=False)
    if result.returncode:raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def validate_record_object(record,commit,require_ref=True):
    p=[]
    try:
        if not valid_sha(commit) or git("cat-file","-t",commit)!="commit":return ["Gate Record object must be a commit SHA"]
        if git("show","-s","--format=%P",commit).split()!=[record["candidate_sha"]]:p.append("Gate Record commit parent is not the candidate")
        if json.loads(git("show",f"{commit}:{RECORD_PATH}"))!=record:p.append("stored Gate Record differs from selected record")
        if require_ref:
            ref=canonical_ref(record);result=subprocess.run(("git","show-ref","--verify","--hash",ref),capture_output=True,text=True,check=False)
            if result.returncode or result.stdout.strip()!=commit:p.append("canonical current Gate Record ref is missing or moved")
    except (ValueError,json.JSONDecodeError,KeyError) as error:p.append(f"invalid Gate Record object: {error}")
    return p

def validate_current_set(records,commits,base,candidate,tree,pr,implementation_agent_id,lead_agent_id,required=GATES,require_refs=True,validate_objects=True):
    p=[];by_type={}
    for record in records:
        p.extend(f"{record.get('gate_record_id')}: {x}" for x in validate_record(record))
        gate=record.get("gate_type")
        if gate in by_type:p.append(f"duplicate selected gate type: {gate}")
        else:by_type[gate]=record
    if set(by_type)!=set(required):p.append("required current gate types are incomplete")
    if set(commits)!=set(required):p.append("selected Gate Record commit types are incomplete")
    for gate,record in by_type.items():
        if (record.get("pr_number"),record.get("base_sha"),record.get("candidate_sha"),record.get("candidate_tree"))!=(pr,base,candidate,tree):p.append(f"stale or wrong identity for {gate}")
        if record.get("disposition")!="PASS":p.append(f"current {gate} is not PASS")
        commit=commits.get(gate)
        if commit and validate_objects:p.extend(f"{gate}: {x}" for x in validate_record_object(record,commit,require_refs))
    review=by_type.get("Independent Code Review",{}).get("agent_id");qa=by_type.get("QA",{}).get("agent_id");release=by_type.get("Release",{}).get("agent_id");security=by_type.get("Security Review",{}).get("agent_id")
    if len({implementation_agent_id,review,qa,release})!=4:p.append("Implementation, Review, QA, and Release identities must be distinct")
    if security in {implementation_agent_id,lead_agent_id,qa,release}:p.append("Security identity violates required independence")
    return p
