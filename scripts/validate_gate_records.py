"""Fail-closed validation for agent-published, content-addressed Gate Records."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{40}$"); ID=re.compile(r"^GATE-[A-Z0-9][A-Z0-9-]{2,63}$")
GATES={"Independent Code Review","QA","Security Review","Release"}; SEVERITIES={"BLOCKING","MAJOR","MINOR","SUGGESTION"}; STATUSES={"OPEN","CLOSED"}
RECORD_FIELDS={"schema_version","gate_record_id","gate_type","agent_role","agent_id","pr_number","base_sha","candidate_sha","candidate_tree","timestamp","scope","checks","findings","disposition","repository_state_changed","supersedes","superseded_by"}
FINDING_FIELDS={"finding_id","severity","summary","status","rechecked_by_gate_record_id"}; RECORD_PATH=".github/governance/gate-record.json"

def timestamp(value: object) -> datetime | None:
    try:
        parsed=datetime.fromisoformat(str(value).replace("Z","+00:00")); return parsed if parsed.tzinfo else None
    except ValueError: return None

def validate_finding(finding: object) -> list[str]:
    if not isinstance(finding,dict): return ["finding must be an object"]
    p=[]
    if set(finding)!=FINDING_FIELDS: p.append("finding fields must exactly match schema")
    if not isinstance(finding.get("finding_id"),str) or not finding["finding_id"].strip(): p.append("finding_id must be non-empty")
    if finding.get("severity") not in SEVERITIES: p.append("invalid finding severity")
    if not isinstance(finding.get("summary"),str) or not finding["summary"].strip(): p.append("finding summary must be non-empty")
    if finding.get("status") not in STATUSES: p.append("invalid finding status")
    recheck=finding.get("rechecked_by_gate_record_id")
    if recheck is not None and (not isinstance(recheck,str) or not ID.fullmatch(recheck)): p.append("invalid finding recheck record ID")
    if finding.get("status")=="OPEN" and recheck is not None: p.append("open finding cannot claim a recheck")
    if finding.get("status")=="CLOSED" and recheck is None: p.append("closed finding requires a recheck record ID")
    return p

def validate_record(record: object) -> list[str]:
    if not isinstance(record,dict): return ["record must be an object"]
    p=[]
    if set(record)!=RECORD_FIELDS: p.append("record fields must exactly match schema")
    if record.get("schema_version")!=1: p.append("schema_version must be 1")
    if not isinstance(record.get("gate_record_id"),str) or not ID.fullmatch(record["gate_record_id"]): p.append("invalid gate_record_id")
    if record.get("gate_type") not in GATES: p.append("invalid gate_type")
    if record.get("agent_role")!=record.get("gate_type"): p.append("agent_role must equal gate_type")
    for field in ("agent_id","scope"):
        if not isinstance(record.get(field),str) or not record[field].strip(): p.append(f"{field} must be non-empty")
    if not isinstance(record.get("pr_number"),int) or record["pr_number"]<1: p.append("pr_number must be positive")
    for field in ("base_sha","candidate_sha","candidate_tree"):
        if not isinstance(record.get(field),str) or not SHA.fullmatch(record[field]): p.append(f"{field} must be a lowercase full SHA")
    if timestamp(record.get("timestamp")) is None: p.append("timestamp must be timezone-aware ISO-8601")
    if not isinstance(record.get("checks"),list) or not record["checks"] or not all(isinstance(x,str) and x.strip() for x in record["checks"]): p.append("checks must be a non-empty string array")
    if record.get("disposition") not in {"PASS","FAIL","PENDING","N/A"}: p.append("invalid disposition")
    if not isinstance(record.get("repository_state_changed"),bool): p.append("repository_state_changed must be boolean")
    for field in ("supersedes","superseded_by"):
        value=record.get(field)
        if value is not None and (not isinstance(value,str) or not ID.fullmatch(value)): p.append(f"invalid {field}")
    if not isinstance(record.get("findings"),list): p.append("findings must be an array")
    else:
        ids=[]
        for i,finding in enumerate(record["findings"]):
            p.extend(f"finding[{i}]: {x}" for x in validate_finding(finding))
            if isinstance(finding,dict): ids.append(finding.get("finding_id"))
        if len(ids)!=len(set(ids)): p.append("finding_id values must be unique within a record")
    return p

def validate_graph(records: list[dict[str,object]]) -> list[str]:
    p=[]; by_id={}
    for record in records:
        rid=record.get("gate_record_id")
        if rid in by_id:
            if record!=by_id[rid]: p.append(f"duplicate Gate Record ID has different content: {rid}")
            else: p.append(f"duplicate Gate Record ID: {rid}")
        else: by_id[rid]=record
    for record in records:
        rid=record["gate_record_id"]
        successor_id=record["superseded_by"]
        predecessor_id=record["supersedes"]
        if successor_id:
            successor=by_id.get(successor_id)
            if successor is None: p.append(f"missing successor for {rid}: {successor_id}")
            else:
                if successor["supersedes"]!=rid: p.append(f"non-reciprocal supersession: {rid} -> {successor_id}")
                if successor["gate_type"]!=record["gate_type"]: p.append(f"supersession changes gate type: {rid}")
                if successor["pr_number"]!=record["pr_number"]: p.append(f"supersession changes PR: {rid}")
                if successor["candidate_sha"]==record["candidate_sha"]: p.append(f"supersession must transition candidate: {rid}")
                if timestamp(successor["timestamp"])<=timestamp(record["timestamp"]): p.append(f"supersession timestamp is not ordered: {rid}")
        if predecessor_id:
            predecessor=by_id.get(predecessor_id)
            if predecessor is None: p.append(f"missing predecessor for {rid}: {predecessor_id}")
            elif predecessor["superseded_by"]!=rid: p.append(f"non-reciprocal predecessor: {predecessor_id} -> {rid}")
        seen=set(); cursor=record
        while cursor.get("superseded_by"):
            if cursor["gate_record_id"] in seen: p.append(f"supersession cycle at {rid}"); break
            seen.add(cursor["gate_record_id"]); cursor=by_id.get(cursor["superseded_by"])
            if cursor is None: break
    for record in records:
        for finding in record["findings"]:
            if finding["severity"] not in {"BLOCKING","MAJOR"} or finding["status"]!="OPEN": continue
            cursor=record; closed=False; seen=set()
            while cursor.get("superseded_by") and cursor["gate_record_id"] not in seen:
                seen.add(cursor["gate_record_id"]); cursor=by_id.get(cursor["superseded_by"])
                if cursor is None: break
                for later in cursor["findings"]:
                    if later["finding_id"]==finding["finding_id"] and later["severity"]==finding["severity"] and later["status"]=="CLOSED" and later["rechecked_by_gate_record_id"]==cursor["gate_record_id"]: closed=True
            if not closed: p.append(f"OPEN {finding['severity']} remains unrepaired/unrechecked: {finding['finding_id']}")
    return p

def git(*args:str)->str:
    result=subprocess.run(("git",*args),capture_output=True,text=True,check=False)
    if result.returncode: raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()

def gate_refs(record:dict[str,object])->tuple[str,str]:
    suffix=f"pr-{record['pr_number']}/{record['candidate_sha']}/{record['gate_record_id']}"
    return f"refs/governance/gate-records/{suffix}",f"refs/remotes/origin/governance-gate-records/{suffix}"

def discover_record_objects(pr:int)->tuple[list[dict[str,object]],dict[str,str]]:
    prefixes=(f"refs/governance/gate-records/pr-{pr}/",f"refs/remotes/origin/governance-gate-records/pr-{pr}/")
    output=git("for-each-ref","--format=%(refname) %(objectname)",*prefixes); records=[]; commits={}; seen=set()
    for line in output.splitlines():
        if not line.strip(): continue
        _,commit=line.split()
        if commit in seen: continue
        seen.add(commit)
        try: record=json.loads(git("show",f"{commit}:{RECORD_PATH}"))
        except json.JSONDecodeError as error: raise ValueError(f"Gate Record ref contains invalid JSON: {commit}") from error
        rid=record.get("gate_record_id")
        if not isinstance(rid,str): raise ValueError(f"Gate Record ref has no valid ID: {commit}")
        records.append(record); commits[rid]=commit
    return records,commits

def validate_record_object(record:dict[str,object],commit:str)->list[str]:
    p=[]
    if not SHA.fullmatch(commit): return ["Gate Record commit must be a full lowercase SHA"]
    try:
        if git("cat-file","-t",commit)!="commit": return ["Gate Record object must be a commit"]
        if git("show","-s","--format=%P",commit).split()!=[record["candidate_sha"]]: p.append("Gate Record commit sole parent must equal candidate")
        stored=json.loads(git("show",f"{commit}:{RECORD_PATH}"))
        if stored!=record: p.append("PR/comment Gate Record content does not match stored content-addressed record")
        found=[]
        for ref in gate_refs(record):
            result=subprocess.run(("git","show-ref","--verify","--hash",ref),capture_output=True,text=True,check=False)
            if result.returncode==0: found.append((ref,result.stdout.strip()))
        if not found: p.append("exact canonical Gate Record ref is missing")
        elif any(value!=commit for _,value in found): p.append("canonical Gate Record ref points to the wrong object")
    except (ValueError,json.JSONDecodeError) as error: p.append(f"invalid Gate Record object: {error}")
    return p

def validate_set(records:list[dict[str,object]],base:str,candidate:str,candidate_tree:str,pr:int,required:set[str],commits:dict[str,str]|None=None)->list[str]:
    p=[]
    for record in records: p.extend(f"{record.get('gate_record_id')}: {x}" for x in validate_record(record))
    if p: return p
    p.extend(validate_graph(records)); active=[r for r in records if r["superseded_by"] is None]
    for gate in required:
        matches=[r for r in active if r["gate_type"]==gate]
        if len(matches)!=1: p.append(f"gate must have exactly one active record: {gate}"); continue
        record=matches[0]
        if record["disposition"]!="PASS": p.append(f"active Gate Record is not PASS: {gate}")
        if (record["base_sha"],record["candidate_sha"],record["candidate_tree"],record["pr_number"])!=(base,candidate,candidate_tree,pr): p.append(f"stale or mismatched Gate Record: {gate}")
    agents=[r["agent_id"] for r in active if r["gate_type"] in required]
    if len(agents)!=len(set(agents)): p.append("required gates must use distinct agent identities")
    if commits is not None:
        for record in records:
            commit=commits.get(record["gate_record_id"])
            if commit is None: p.append(f"missing content-addressed Gate Record commit: {record['gate_record_id']}")
            else: p.extend(f"{record['gate_record_id']}: {x}" for x in validate_record_object(record,commit))
        if set(commits)!=set(r["gate_record_id"] for r in records): p.append("Gate Record commit map contains unknown IDs")
    return p

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("record_files",nargs="+"); parser.add_argument("--record-commit",action="append",default=[],metavar="ID=SHA")
    parser.add_argument("--base",required=True); parser.add_argument("--candidate",required=True); parser.add_argument("--tree",required=True); parser.add_argument("--pr",required=True,type=int); parser.add_argument("--require",nargs="+",choices=sorted(GATES),required=True); args=parser.parse_args()
    records=[json.loads(Path(path).read_text(encoding="utf-8")) for path in args.record_files]; commits=dict(item.split("=",1) for item in args.record_commit)
    p=validate_set(records,args.base,args.candidate,args.tree,args.pr,set(args.require),commits or None)
    if p: print("Gate Record validation failed:"); [print(f"- {x}") for x in p]; return 1
    print("Gate Record validation passed."); return 0

if __name__=="__main__": sys.exit(main())
