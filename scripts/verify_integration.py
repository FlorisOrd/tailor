"""Verify Bootstrap v0 candidate identity, authorization, selected gates, and integration."""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys
from datetime import datetime
from validate_evidence import github_json,validate_ci_run,validate_selected_live
from validate_gate_records import GATES,RECORD_PATH,validate_current_set

SHA=re.compile(r"^[0-9a-f]{40}$");AUTH_PATH=".github/governance/authorization.json";AUTH_TRAILER="Governance-Authorization";PR_TRAILER="Governance-PR";GOVERNED_BASE_BRANCH="main"
AUTH_FIELDS={"schema_version","record_type","authorization_id","pr_number","base_sha","candidate_sha","candidate_tree","timestamp","implementation_agent_id","lead_agent_id","release_agent_id","ci_run_id","ci_candidate_sha","gate_record_commits"}
def git(*args):
    result=subprocess.run(("git",*args),capture_output=True,text=True,check=False)
    if result.returncode:raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def require_commit(value,label):
    if not isinstance(value,str) or not SHA.fullmatch(value) or git("cat-file","-t",value)!="commit":raise ValueError(f"{label} is not a full commit SHA")
def tree(commit):return git("rev-parse",f"{commit}^{{tree}}")
def verify_candidate(base,candidate):
    require_commit(base,"base");require_commit(candidate,"candidate")
    if subprocess.run(("git","merge-base","--is-ancestor",base,candidate),check=False).returncode:raise ValueError("base is not an ancestor of candidate")
    behind,ahead=git("rev-list","--left-right","--count",f"{base}...{candidate}").split()
    if behind!="0":raise ValueError("candidate is behind recorded base")
    print(f"base_sha={base}\ncandidate_sha={candidate}\ncandidate_tree={tree(candidate)}\ncandidate_commits_ahead={ahead}")
def trailer(commit,key):
    values=git("show","-s",f"--format=%(trailers:key={key},valueonly)",commit).splitlines()
    if len(values)!=1 or not values[0].strip():raise ValueError(f"integration must contain exactly one {key} trailer")
    return values[0].strip()
def auth_ref(pr,candidate):return f"refs/governance/authorizations/pr-{pr}/{candidate}"
def remote_ref_sha(ref):
    result=subprocess.run(("git","ls-remote","--exit-code","origin",ref),capture_output=True,text=True,check=False)
    if result.returncode:raise ValueError(f"required live origin ref is unavailable: {ref}")
    lines=[line.split() for line in result.stdout.splitlines() if line.strip()]
    if len(lines)!=1 or len(lines[0])!=2 or lines[0][1]!=ref or not SHA.fullmatch(lines[0][0]):raise ValueError(f"live origin ref is ambiguous or invalid: {ref}")
    return lines[0][0]
def validate_live_authorization(repo,token,a):
    try:pr=github_json(f"https://api.github.com/repos/{repo}/pulls/{a['pr_number']}",token)
    except Exception as error:raise ValueError("live GitHub PR state is unavailable") from error
    problems=[];number=a["pr_number"]
    if pr.get("number")!=number:problems.append("live PR number differs from authorization")
    if pr.get("state")!="open":problems.append("live PR is not open")
    if pr.get("merged") is not False:problems.append("live PR is merged or merge state is unavailable")
    base=pr.get("base") or {};head=pr.get("head") or {}
    if base.get("ref")!=GOVERNED_BASE_BRANCH:problems.append("live PR base branch is not governed main")
    if base.get("sha")!=a["base_sha"]:problems.append("live PR base SHA differs from authorization")
    if head.get("sha")!=a["candidate_sha"]:problems.append("live PR head SHA differs from authorization")
    if (head.get("repo") or {}).get("full_name")!=repo:problems.append("live PR candidate is not an origin branch")
    if problems:return problems
    try:
        live_base=remote_ref_sha(f"refs/heads/{GOVERNED_BASE_BRANCH}")
        live_candidate=remote_ref_sha(f"refs/heads/{head['ref']}")
    except (KeyError,TypeError,ValueError) as error:return [str(error)]
    if live_base!=a["base_sha"]:problems.append("live origin main moved from authorized base")
    if live_candidate!=a["candidate_sha"]:problems.append("live origin candidate branch moved from authorized candidate")
    return problems
def load_authorization(commit):
    require_commit(commit,"authorization")
    try:a=json.loads(git("show",f"{commit}:{AUTH_PATH}"))
    except json.JSONDecodeError as error:raise ValueError("authorization JSON is invalid") from error
    if set(a)!=AUTH_FIELDS or a.get("schema_version")!=1 or a.get("record_type")!="Bootstrap Governance v0 Merge Authorization":raise ValueError("authorization fields/protocol are invalid")
    for field in ("base_sha","candidate_sha","candidate_tree","ci_candidate_sha"):
        if not isinstance(a.get(field),str) or not SHA.fullmatch(a[field]):raise ValueError(f"invalid authorization {field}")
    if a["ci_candidate_sha"]!=a["candidate_sha"]:raise ValueError("CI evidence is stale")
    if not isinstance(a.get("ci_run_id"),int) or a["ci_run_id"]<1:raise ValueError("CI run ID is invalid")
    if not isinstance(a.get("gate_record_commits"),dict) or set(a["gate_record_commits"])!=GATES:raise ValueError("authorization does not select all current gates")
    if not all(isinstance(x,str) and SHA.fullmatch(x) for x in a["gate_record_commits"].values()):raise ValueError("selected Gate Record commit is invalid")
    if any(not isinstance(a.get(x),str) or not a[x].strip() for x in ("authorization_id","implementation_agent_id","lead_agent_id","release_agent_id")):raise ValueError("authorization identities are incomplete")
    try:
        if datetime.fromisoformat(str(a["timestamp"]).replace("Z","+00:00")).tzinfo is None:raise ValueError
    except ValueError as error:raise ValueError("authorization timestamp is invalid") from error
    return a
def verify_authorization(authorization,reconcile_live=False):
    a=load_authorization(authorization)
    pr=a["pr_number"]
    ref=auth_ref(pr,a["candidate_sha"]);result=subprocess.run(("git","show-ref","--verify","--hash",ref),capture_output=True,text=True,check=False)
    if result.returncode or result.stdout.strip()!=authorization:raise ValueError("exact authorization ref is missing or moved")
    if git("show","-s","--format=%P",authorization).split()!=[a["candidate_sha"]]:raise ValueError("authorization parent is not candidate")
    records=[];records_by_type={}
    for gate,commit in a["gate_record_commits"].items():
        require_commit(commit,f"{gate} Gate Record")
        try:record=json.loads(git("show",f"{commit}:{RECORD_PATH}"))
        except json.JSONDecodeError as error:raise ValueError(f"invalid {gate} Gate Record JSON") from error
        records.append(record);records_by_type[gate]=record
    problems=validate_current_set(records,a["gate_record_commits"],a["base_sha"],a["candidate_sha"],a["candidate_tree"],pr,a["implementation_agent_id"],a["lead_agent_id"])
    if records_by_type.get("Release",{}).get("agent_id")!=a["release_agent_id"]:problems.append("Release Gate identity differs from authorization")
    if reconcile_live:
        token=os.environ.get("GITHUB_TOKEN");repo=os.environ.get("GITHUB_REPOSITORY")
        if not token or not repo:raise ValueError("live selected-evidence validation requires GitHub context")
        problems.extend(validate_live_authorization(repo,token,a))
        problems.extend(validate_selected_live(repo,pr,token,records_by_type,a["gate_record_commits"]))
        problems.extend(validate_ci_run(repo,token,a["ci_run_id"],a["candidate_sha"]))
    if problems:raise ValueError("current gate evidence is invalid: "+"; ".join(problems))
    if tree(a["candidate_sha"])!=a["candidate_tree"]:raise ValueError("authorized candidate tree is stale or wrong")
    if subprocess.run(("git","merge-base","--is-ancestor",a["base_sha"],a["candidate_sha"]),check=False).returncode:raise ValueError("authorized base is not an ancestor of candidate")
    print(f"pr_number={pr}\nauthorization_sha={authorization}\nauthorization_ref={ref}\nbase_sha={a['base_sha']}\ncandidate_sha={a['candidate_sha']}\ncandidate_tree={a['candidate_tree']}\ncurrent_gate_evidence=verified")
    return a,ref
def verify_integration(integration,authorization_arg=None,reconcile_live=False):
    require_commit(integration,"integration");authorization=trailer(integration,AUTH_TRAILER);pr=int(trailer(integration,PR_TRAILER))
    if authorization_arg and authorization_arg!=authorization:raise ValueError("supplied authorization differs from integration trailer")
    a,ref=verify_authorization(authorization,False)
    if reconcile_live:
        token=os.environ.get("GITHUB_TOKEN");repo=os.environ.get("GITHUB_REPOSITORY")
        if not token or not repo:raise ValueError("live selected-evidence validation requires GitHub context")
        records_by_type={gate:json.loads(git("show",f"{commit}:{RECORD_PATH}")) for gate,commit in a["gate_record_commits"].items()}
        problems=validate_selected_live(repo,pr,token,records_by_type,a["gate_record_commits"])+validate_ci_run(repo,token,a["ci_run_id"],a["candidate_sha"])
        if problems:raise ValueError("current gate evidence is invalid: "+"; ".join(problems))
    if a["pr_number"]!=pr:raise ValueError("authorization PR differs from integration PR")
    parents=git("show","-s","--format=%P",integration).split()
    if len(parents)!=2 or parents[0]!=a["base_sha"] or parents[1]!=a["candidate_sha"]:raise ValueError("integration parents are not exact authorized base/candidate")
    if tree(a["candidate_sha"])!=a["candidate_tree"] or tree(integration)!=a["candidate_tree"]:raise ValueError("integration tree differs from authorized candidate tree")
    print(f"pr_number={pr}\nauthorization_sha={authorization}\nauthorization_ref={ref}\nbase_sha={a['base_sha']}\ncandidate_sha={a['candidate_sha']}\ncandidate_tree={a['candidate_tree']}\nintegration_sha={integration}\nintegration_tree={tree(integration)}\nexact_authorized_tuple=verified")
def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="mode",required=True);c=sub.add_parser("candidate");c.add_argument("--base",required=True);c.add_argument("--candidate",required=True);z=sub.add_parser("authorization");z.add_argument("--authorization",required=True);z.add_argument("--reconcile-live",action="store_true");i=sub.add_parser("integration");i.add_argument("--integration",required=True);i.add_argument("--authorization");i.add_argument("--reconcile-live",action="store_true");a=parser.parse_args()
    try:
        if a.mode=="candidate":verify_candidate(a.base,a.candidate)
        elif a.mode=="authorization":verify_authorization(a.authorization,a.reconcile_live)
        else:verify_integration(a.integration,a.authorization,a.reconcile_live)
    except (ValueError,TypeError) as error:print(f"Integration identity validation failed: {error}",file=sys.stderr);return 1
    return 0
if __name__=="__main__":sys.exit(main())
