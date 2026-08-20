"""Reconcile only explicitly selected current Bootstrap v0 Gate Records with PR comments."""
from __future__ import annotations
import json,re,urllib.request

DECLARATION=re.compile(r"(?m)^Bootstrap-Gate-Commit:\s*([0-9a-f]{40})\s*$.*?```bootstrap-gate\s*\n(.*?)\n```",re.DOTALL)

def github_json(url,token):
    request=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28","User-Agent":"bootstrap-governance-validator"})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
def github_comments(repo,pr,token):
    comments=[];page=1
    while True:
        data=github_json(f"https://api.github.com/repos/{repo}/issues/{pr}/comments?per_page=100&page={page}",token)
        comments.extend(data)
        if len(data)<100:return comments
        page+=1

def parse_current_declarations(comments):
    declarations=[];problems=[]
    for comment in comments:
        matches=DECLARATION.findall(comment.get("body") or "")
        if not matches:continue
        if len(matches)!=1:problems.append(f"comment {comment.get('id')} has ambiguous Bootstrap Gate declarations");continue
        commit,raw=matches[0]
        try:record=json.loads(raw)
        except json.JSONDecodeError as error:problems.append(f"comment {comment.get('id')} has invalid Bootstrap Gate JSON: {error}");continue
        declarations.append({"comment_id":comment.get("id"),"commit":commit,"record":record})
    return declarations,problems

def reconcile_selected(comments,records_by_type,commits_by_type):
    declarations,problems=parse_current_declarations(comments);selected=set(commits_by_type.values());by_commit={}
    for declaration in declarations:
        commit=declaration["commit"]
        if commit in by_commit:problems.append(f"duplicate PR-visible declaration for selected object: {commit}")
        else:by_commit[commit]=declaration
    for gate,commit in commits_by_type.items():
        declaration=by_commit.get(commit)
        if declaration is None:problems.append(f"selected {gate} has no gate-agent-published PR declaration");continue
        if declaration["record"]!=records_by_type.get(gate):problems.append(f"selected {gate} PR JSON differs from immutable object")
        if declaration["record"].get("publisher_agent_id")!=declaration["record"].get("agent_id"):problems.append(f"selected {gate} is not recorded as agent-published")
    for commit in selected:
        if not any(d["commit"]==commit for d in declarations):continue
    return problems

def validate_selected_live(repo,pr,token,records_by_type,commits_by_type):return reconcile_selected(github_comments(repo,pr,token),records_by_type,commits_by_type)
def validate_ci_run(repo,token,run_id,candidate):
    run=github_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}",token);p=[]
    if run.get("name")!="Governance Baseline":p.append("selected CI run is not Governance Baseline")
    if run.get("head_sha")!=candidate:p.append("selected CI run is stale or for another candidate")
    if run.get("status")!="completed" or run.get("conclusion")!="success":p.append("selected current CI run did not succeed")
    if run.get("event")!="pull_request":p.append("selected CI run is not a pull-request run")
    return p
