"""Reconcile live PR evidence with modern objects and provenance-only legacy bindings."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,re,subprocess,sys,urllib.request
from pathlib import Path
from validate_gate_records import RECORD_PATH,validate_set,valid_sha

ROOT=Path(__file__).resolve().parents[1]
POLICY=json.loads((ROOT/".github/governance/policy.json").read_text())
BINDING_PATH=".github/governance/legacy-evidence-binding.json"
MODERN=re.compile(r"(?m)^Gate-Record-Commit:\s*([0-9a-f]{40})\s*$.*?```gate-record\s*\n(.*?)\n```",re.DOTALL)
FENCED=re.compile(r"```gate-record\s*\n(.*?)\n```",re.DOTALL)
SHA256=re.compile(r"^[0-9a-f]{64}$")
BINDING_FIELDS={"schema_version","binding_id","record_type","pr_number","legacy_gate_record_id","legacy_schema_version","legacy_comment_id","legacy_comment_url","legacy_agent_id","legacy_gate_type","legacy_base_sha","legacy_candidate_sha","legacy_candidate_tree","legacy_disposition","legacy_record","canonical_json_sha256","raw_comment_sha256","observed_at","migration_agent_id","migration_candidate_sha","migration_candidate_tree","provenance_only","not_approval"}

def canonical_json(value):return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha256_text(value):return hashlib.sha256(value.encode()).hexdigest()
def run(*args):
    result=subprocess.run(args,capture_output=True,text=True,check=False)
    if result.returncode:raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def remote_run(token,*args):
    env=os.environ.copy()
    if token:
        credential=base64.b64encode(f"x-access-token:{token}".encode()).decode();env.update({"GIT_CONFIG_COUNT":"1","GIT_CONFIG_KEY_0":"http.https://github.com/.extraheader","GIT_CONFIG_VALUE_0":f"AUTHORIZATION: basic {credential}"})
    result=subprocess.run(args,capture_output=True,text=True,check=False,env=env)
    if result.returncode:raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def github_comments(repo,pr,token):
    comments=[];page=1
    while True:
        url=f"https://api.github.com/repos/{repo}/issues/{pr}/comments?per_page=100&page={page}"
        request=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28","User-Agent":"governance-evidence-validator"})
        with urllib.request.urlopen(request,timeout=30) as response:data=json.load(response)
        comments.extend(data)
        if len(data)<100:return comments
        page+=1

def parse_visible(comments):
    modern=[];legacy=[];problems=[];eligible=POLICY["evidence"]["legacy_migration"]["eligible_records"]
    for comment in comments:
        body=comment.get("body") or "";modern_matches=MODERN.findall(body);fenced=FENCED.findall(body)
        if modern_matches:
            if len(modern_matches)!=1 or len(fenced)!=1:problems.append(f"comment {comment.get('id')} has ambiguous Gate Record declarations");continue
            commit,raw=modern_matches[0]
            try:record=json.loads(raw)
            except json.JSONDecodeError as error:problems.append(f"comment {comment.get('id')} has invalid Gate Record JSON: {error}");continue
            modern.append({"comment":comment,"commit":commit,"record":record});continue
        for raw in fenced:
            try:record=json.loads(raw)
            except json.JSONDecodeError as error:problems.append(f"comment {comment.get('id')} has invalid legacy Gate Record JSON: {error}");continue
            rid=record.get("gate_record_id");rule=eligible.get(rid)
            if not rule or rule.get("comment_id")!=comment.get("id") or record.get("schema_version") not in rule.get("schema_versions",[]):problems.append(f"comment {comment.get('id')} has an unauthorized unbound Gate Record declaration");continue
            legacy.append({"comment":comment,"record":record})
    return modern,legacy,problems

def remote_ref_map(remote,prefix,token=None):
    output=remote_run(token,"git","ls-remote","--refs",remote,prefix+"*");refs={}
    for line in output.splitlines():
        if not line.strip():continue
        commit,ref=line.split()
        if ref in refs:raise ValueError(f"duplicate remote ref: {ref}")
        refs[ref]=commit
    return refs
def fetch_object(remote,ref,commit,token):
    local=f"refs/evidence-validation/{ref}";remote_run(token,"git","fetch","--no-tags",remote,f"+{ref}:{local}")
    if run("git","rev-parse",local)!=commit:raise ValueError(f"fetched ref does not equal advertised object: {ref}")
def fetch_remote_records(remote,pr,token=None):
    refs=remote_ref_map(remote,f"refs/governance/gate-records/pr-{pr}/",token);records=[];commits={};ref_by_id={}
    for ref,commit in refs.items():
        fetch_object(remote,ref,commit,token)
        try:record=json.loads(run("git","show",f"{commit}:{RECORD_PATH}"))
        except json.JSONDecodeError as error:raise ValueError(f"remote Gate Record object is invalid JSON: {commit}") from error
        rid=record.get("gate_record_id");expected=f"refs/governance/gate-records/pr-{record.get('pr_number')}/{record.get('candidate_sha')}/{rid}"
        if ref!=expected:raise ValueError(f"remote Gate Record is under a noncanonical ref: {ref}")
        if run("git","show","-s","--format=%P",commit).split()!=[record.get("candidate_sha")]:raise ValueError(f"remote Gate Record commit parent does not equal candidate: {rid}")
        if rid in commits:raise ValueError(f"duplicate Gate Record ID under remote refs: {rid}")
        records.append(record);commits[rid]=commit;ref_by_id[rid]=ref
    return records,commits,ref_by_id

def validate_binding(binding,legacy):
    p=[];record=legacy["record"];comment=legacy["comment"]
    if set(binding)!=BINDING_FIELDS:p.append("legacy binding fields do not match schema")
    if binding.get("schema_version")!=1 or binding.get("record_type")!="Legacy Evidence Binding" or binding.get("provenance_only") is not True or binding.get("not_approval") is not True:p.append("legacy binding must be provenance-only and not approval")
    pairs={"pr_number":"pr_number","legacy_gate_record_id":"gate_record_id","legacy_schema_version":"schema_version","legacy_agent_id":"agent_id","legacy_gate_type":"gate_type","legacy_base_sha":"base_sha","legacy_candidate_sha":"candidate_sha","legacy_candidate_tree":"candidate_tree","legacy_disposition":"disposition"}
    for target,source in pairs.items():
        if binding.get(target)!=record.get(source):p.append(f"legacy binding identity mismatch: {target}")
    if binding.get("legacy_comment_id")!=comment.get("id") or binding.get("legacy_comment_url")!=(comment.get("html_url") or comment.get("url")):p.append("legacy binding comment identity mismatch")
    if binding.get("legacy_record")!=record:p.append("migrated legacy JSON differs from live historical comment")
    if binding.get("canonical_json_sha256")!=sha256_text(canonical_json(record)):p.append("legacy canonical JSON hash mismatch")
    if binding.get("raw_comment_sha256")!=sha256_text(comment.get("body") or ""):p.append("legacy raw comment hash mismatch")
    if not valid_sha(binding.get("migration_candidate_sha")) or not valid_sha(binding.get("migration_candidate_tree")):p.append("invalid migration candidate identity")
    return p
def fetch_migrations(remote,pr,token=None):
    refs=remote_ref_map(remote,f"refs/governance/evidence-migrations/pr-{pr}/",token);result={}
    for ref,commit in refs.items():
        fetch_object(remote,ref,commit,token)
        try:b=json.loads(run("git","show",f"{commit}:{BINDING_PATH}"))
        except (ValueError,json.JSONDecodeError) as error:raise ValueError(f"invalid legacy migration object: {commit}") from error
        rid=b.get("legacy_gate_record_id");h=b.get("canonical_json_sha256");expected=f"refs/governance/evidence-migrations/pr-{pr}/{rid}/{h}"
        if ref!=expected or not SHA256.fullmatch(str(h)):raise ValueError(f"noncanonical legacy migration ref: {ref}")
        if run("git","show","-s","--format=%P",commit).split()!=[b.get("migration_candidate_sha")]:raise ValueError(f"legacy migration parent mismatch: {rid}")
        if rid in result:raise ValueError(f"duplicate legacy migration binding: {rid}")
        result[rid]={"binding":b,"commit":commit,"ref":ref}
    return result

def reconcile(comments,records,commits,base,candidate,tree,pr,required,migrations=None,enforce_gates=True):
    modern,legacy,problems=parse_visible(comments);migrations=migrations or {};visible={};objects=set()
    for d in modern:
        rid=d["record"].get("gate_record_id")
        if rid in visible:problems.append(f"duplicate PR-visible Gate Record ID: {rid}"+(" with different content" if visible[rid]["record"]!=d["record"] else ""))
        else:visible[rid]=d
        if d["commit"] in objects:problems.append(f"duplicate PR-visible Gate Record object: {d['commit']}")
        objects.add(d["commit"])
    remote_by_id={r["gate_record_id"]:r for r in records};legacy_by_id={d["record"].get("gate_record_id"):d for d in legacy}
    for rid in set(remote_by_id)-set(visible)-set(legacy_by_id):problems.append(f"authoritative remote record has no PR-visible declaration: {rid}")
    for rid in set(visible)-set(remote_by_id):problems.append(f"PR-visible record has no authoritative remote object: {rid}")
    for rid in set(visible)&set(remote_by_id):
        if visible[rid]["commit"]!=commits[rid]:problems.append(f"PR-visible object declaration mismatch: {rid}")
        if visible[rid]["record"]!=remote_by_id[rid]:problems.append(f"PR-visible JSON differs from authoritative object: {rid}")
    for rid,d in legacy_by_id.items():
        migrated=migrations.get(rid)
        if not migrated:problems.append(f"legacy PR-visible record lacks migration binding: {rid}")
        else:problems.extend(f"{rid}: {x}" for x in validate_binding(migrated["binding"],d))
    for rid in set(migrations)-set(legacy_by_id):problems.append(f"legacy migration has no matching live historical comment: {rid}")
    all_records=records+[d["record"] for rid,d in legacy_by_id.items() if rid not in remote_by_id]
    problems.extend(validate_set(all_records,base,candidate,tree,pr,required,None,enforce_gates=enforce_gates))
    return problems
def validate_live(repo,pr,token,remote,base,candidate,tree,required,enforce_gates=True):
    comments=github_comments(repo,pr,token);records,commits,_=fetch_remote_records(remote,pr,token);migrations=fetch_migrations(remote,pr,token);return reconcile(comments,records,commits,base,candidate,tree,pr,required,migrations,enforce_gates)
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--pr",required=True,type=int);p.add_argument("--remote",default="origin");p.add_argument("--base",required=True);p.add_argument("--candidate",required=True);p.add_argument("--tree",required=True);p.add_argument("--require",nargs="+",required=True);p.add_argument("--token-env",default="GITHUB_TOKEN");p.add_argument("--integrity-only",action="store_true");a=p.parse_args();token=os.environ.get(a.token_env)
    if not token:print(f"Evidence validation failed: missing {a.token_env}",file=sys.stderr);return 1
    try:problems=validate_live(a.repo,a.pr,token,a.remote,a.base,a.candidate,a.tree,set(a.require),not a.integrity_only)
    except (ValueError,OSError) as error:problems=[str(error)]
    if problems:print("Evidence validation failed:");[print(f"- {x}") for x in problems];return 1
    print("Live PR, modern objects, legacy bindings, and complete remote ledger integrity passed.");return 0
if __name__=="__main__":sys.exit(main())
