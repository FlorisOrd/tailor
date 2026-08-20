"""Reconcile live GitHub PR comments with the complete canonical remote evidence ledger."""
from __future__ import annotations
import argparse,base64,json,os,re,subprocess,sys,urllib.request
from validate_gate_records import RECORD_PATH,validate_record,validate_set

DECLARATION=re.compile(r"(?m)^Gate-Record-Commit:\s*([0-9a-f]{40})\s*$.*?```gate-record\s*\n(.*?)\n```",re.DOTALL)

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
def parse_visible_declarations(comments):
    declarations=[];problems=[]
    for comment in comments:
        matches=DECLARATION.findall(comment.get("body") or "")
        if not matches:
            if "```gate-record" in (comment.get("body") or ""):problems.append(f"comment {comment.get('id')} has Gate Record JSON without an authoritative commit declaration")
            continue
        if len(matches)!=1:problems.append(f"comment {comment.get('id')} has ambiguous Gate Record declarations");continue
        commit,raw=matches[0]
        try:record=json.loads(raw)
        except json.JSONDecodeError as error:problems.append(f"comment {comment.get('id')} has invalid Gate Record JSON: {error}");continue
        declarations.append({"comment_id":comment.get("id"),"comment_user":comment.get("user",{}).get("login"),"commit":commit,"record":record})
    return declarations,problems
def remote_ref_map(remote,pr,token=None):
    prefix=f"refs/governance/gate-records/pr-{pr}/";output=remote_run(token,"git","ls-remote","--refs",remote,prefix+"*");refs={}
    for line in output.splitlines():
        if not line.strip():continue
        commit,ref=line.split()
        if ref in refs:raise ValueError(f"duplicate remote ref: {ref}")
        refs[ref]=commit
    return refs
def fetch_remote_records(remote,pr,token=None):
    refs=remote_ref_map(remote,pr,token);records=[];commits={};ref_by_id={}
    for ref,commit in refs.items():
        remote_run(token,"git","fetch","--no-tags",remote,f"+{ref}:refs/evidence-validation/{ref}")
        try:record=json.loads(run("git","show",f"{commit}:{RECORD_PATH}"))
        except json.JSONDecodeError as error:raise ValueError(f"remote Gate Record object is invalid JSON: {commit}") from error
        rid=record.get("gate_record_id")
        if not isinstance(rid,str):raise ValueError(f"remote Gate Record lacks ID: {commit}")
        expected=f"refs/governance/gate-records/pr-{record.get('pr_number')}/{record.get('candidate_sha')}/{rid}"
        if ref!=expected:raise ValueError(f"remote Gate Record is under a noncanonical ref: {ref}")
        if run("git","show","-s","--format=%P",commit).split()!=[record.get("candidate_sha")]:raise ValueError(f"remote Gate Record commit parent does not equal candidate: {rid}")
        if rid in commits:raise ValueError(f"duplicate Gate Record ID under remote refs: {rid}")
        records.append(record);commits[rid]=commit;ref_by_id[rid]=ref
    return records,commits,ref_by_id
def reconcile(comments,records,commits,base,candidate,tree,pr,required):
    visible,problems=parse_visible_declarations(comments);visible_by_id={};objects=set()
    for declaration in visible:
        record=declaration["record"];rid=record.get("gate_record_id")
        if rid in visible_by_id:
            problems.append(f"duplicate PR-visible Gate Record ID: {rid}"+(" with different content" if visible_by_id[rid]["record"]!=record else ""))
        else:visible_by_id[rid]=declaration
        if declaration["commit"] in objects:problems.append(f"duplicate PR-visible Gate Record object: {declaration['commit']}")
        objects.add(declaration["commit"])
    remote_by_id={r["gate_record_id"]:r for r in records if isinstance(r,dict) and isinstance(r.get("gate_record_id"),str)}
    if set(visible_by_id)!=set(remote_by_id):
        for rid in set(remote_by_id)-set(visible_by_id):problems.append(f"authoritative remote record has no PR-visible declaration: {rid}")
        for rid in set(visible_by_id)-set(remote_by_id):problems.append(f"PR-visible record has no authoritative remote object: {rid}")
    for rid in set(visible_by_id)&set(remote_by_id):
        declaration=visible_by_id[rid]
        if declaration["commit"]!=commits[rid]:problems.append(f"PR-visible object declaration mismatch: {rid}")
        if declaration["record"]!=remote_by_id[rid]:problems.append(f"PR-visible JSON differs from authoritative object: {rid}")
    problems.extend(validate_set(records,base,candidate,tree,pr,required,None))
    return problems
def validate_live(repo,pr,token,remote,base,candidate,tree,required):
    comments=github_comments(repo,pr,token);records,commits,_=fetch_remote_records(remote,pr,token);return reconcile(comments,records,commits,base,candidate,tree,pr,required)
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--pr",required=True,type=int);p.add_argument("--remote",default="origin");p.add_argument("--base",required=True);p.add_argument("--candidate",required=True);p.add_argument("--tree",required=True);p.add_argument("--require",nargs="+",required=True);p.add_argument("--token-env",default="GITHUB_TOKEN");a=p.parse_args();token=os.environ.get(a.token_env)
    if not token:print(f"Evidence validation failed: missing {a.token_env}",file=sys.stderr);return 1
    try:problems=validate_live(a.repo,a.pr,token,a.remote,a.base,a.candidate,a.tree,set(a.require))
    except (ValueError,OSError) as error:problems=[str(error)]
    if problems:print("Evidence validation failed:");[print(f"- {x}") for x in problems];return 1
    print("Live PR-visible and complete remote evidence reconciliation passed.");return 0
if __name__=="__main__":sys.exit(main())
