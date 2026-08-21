"""Verify Bootstrap v0 release identity, authorization, and integration."""
from __future__ import annotations

import argparse, json, os, re, subprocess, sys
from dataclasses import asdict, dataclass
from datetime import datetime
from validate_evidence import github_json, validate_selected_live
from validate_gate_records import GATES, RECORD_PATH, validate_current_set

SHA = re.compile(r"^[0-9a-f]{40}$")
AUTH_PATH = ".github/governance/authorization.json"
AUTH_TRAILER = "Governance-Authorization"
PR_TRAILER = "Governance-PR"
GOVERNED_REPOSITORY = "FlorisOrd/tailor"
GOVERNED_BASE_BRANCH = "main"
GOVERNED_WORKFLOW_NAME = "Governance Baseline"
GOVERNED_WORKFLOW_PATH = ".github/workflows/governance.yml"

CONTEXT_FIELDS = (
    "repository", "head_repository", "pr_number", "pr_state", "merged",
    "base_branch", "base_sha", "head_branch", "head_sha", "candidate_tree",
    "remote_base_sha", "remote_head_sha", "base_is_ancestor", "ci_workflow_name",
    "ci_workflow_path", "ci_event", "ci_pr_number", "ci_head_sha", "ci_status",
    "ci_conclusion",
)
AUTH_CONTEXT_MAP = {
    "repository":"repository", "head_repository":"head_repository", "pr_number":"pr_number",
    "pr_state":"pr_state", "merged":"merged", "base_branch":"base_branch", "base_sha":"base_sha",
    "head_branch":"head_branch", "candidate_sha":"head_sha", "candidate_tree":"candidate_tree",
    "remote_base_sha":"remote_base_sha", "remote_candidate_sha":"remote_head_sha",
    "base_is_ancestor":"base_is_ancestor", "ci_workflow_name":"ci_workflow_name",
    "ci_workflow_path":"ci_workflow_path", "ci_event":"ci_event", "ci_pr_number":"ci_pr_number",
    "ci_candidate_sha":"ci_head_sha", "ci_status":"ci_status", "ci_conclusion":"ci_conclusion",
}
AUTH_FIELDS = {
    "schema_version", "record_type", "authorization_id", "timestamp",
    "implementation_agent_id", "lead_agent_id", "release_agent_id", "ci_run_id",
    "gate_record_commits", *AUTH_CONTEXT_MAP,
}

@dataclass(frozen=True)
class LiveReleaseContext:
    repository: str
    head_repository: str
    pr_number: int
    pr_state: str
    merged: bool
    base_branch: str
    base_sha: str
    head_branch: str
    head_sha: str
    candidate_tree: str
    remote_base_sha: str
    remote_head_sha: str
    base_is_ancestor: bool
    ci_workflow_name: str
    ci_workflow_path: str
    ci_event: str
    ci_pr_number: int
    ci_head_sha: str
    ci_status: str
    ci_conclusion: str

def git(*args):
    result = subprocess.run(("git", *args), capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()

def require_commit(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value) or git("cat-file", "-t", value) != "commit":
        raise ValueError(f"{label} is not a full commit SHA")

def tree(commit): return git("rev-parse", f"{commit}^{{tree}}")
def is_ancestor(base, candidate): return subprocess.run(("git", "merge-base", "--is-ancestor", base, candidate), check=False).returncode == 0

def verify_candidate(base, candidate):
    require_commit(base, "base"); require_commit(candidate, "candidate")
    if not is_ancestor(base, candidate): raise ValueError("base is not an ancestor of candidate")
    behind, ahead = git("rev-list", "--left-right", "--count", f"{base}...{candidate}").split()
    if behind != "0": raise ValueError("candidate is behind recorded base")
    print(f"base_sha={base}\ncandidate_sha={candidate}\ncandidate_tree={tree(candidate)}\ncandidate_commits_ahead={ahead}")

def trailer(commit, key):
    values = git("show", "-s", f"--format=%(trailers:key={key},valueonly)", commit).splitlines()
    if len(values) != 1 or not values[0].strip(): raise ValueError(f"integration must contain exactly one {key} trailer")
    return values[0].strip()

def auth_ref(pr, candidate): return f"refs/governance/authorizations/pr-{pr}/{candidate}"

def remote_ref_sha(ref):
    result = subprocess.run(("git", "ls-remote", "--exit-code", "origin", ref), capture_output=True, text=True, check=False)
    if result.returncode: raise ValueError(f"required live origin ref is unavailable: {ref}")
    lines = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1 or len(lines[0]) != 2 or lines[0][1] != ref or not SHA.fullmatch(lines[0][0]):
        raise ValueError(f"live origin ref is ambiguous or invalid: {ref}")
    return lines[0][0]

def ci_identity(run):
    associations = run.get("pull_requests")
    if not isinstance(associations, list) or len(associations) != 1: raise ValueError("CI run must have exactly one PR association")
    association = associations[0]
    if not isinstance(association, dict) or not isinstance(association.get("number"), int): raise ValueError("CI PR association is malformed")
    return {
        "ci_workflow_name": run.get("name"), "ci_workflow_path": run.get("path"),
        "ci_event": run.get("event"), "ci_pr_number": association["number"],
        "ci_head_sha": run.get("head_sha"), "ci_status": run.get("status"),
        "ci_conclusion": run.get("conclusion"),
    }

def require_expected_identity(expected_pr_number, expected_head_branch):
    if not isinstance(expected_pr_number, int) or expected_pr_number < 1:
        raise ValueError("expected PR number is required")
    if not isinstance(expected_head_branch, str) or not expected_head_branch.strip():
        raise ValueError("expected head branch is required")

def build_live_release_context(token, ci_run_id, expected_pr_number, expected_head_branch):
    require_expected_identity(expected_pr_number, expected_head_branch)
    if not token: raise ValueError("live release context requires GitHub authentication")
    try:
        pr = github_json(f"https://api.github.com/repos/{GOVERNED_REPOSITORY}/pulls/{expected_pr_number}", token)
        run = github_json(f"https://api.github.com/repos/{GOVERNED_REPOSITORY}/actions/runs/{ci_run_id}", token)
    except Exception as error:
        raise ValueError("required live GitHub release state is unavailable") from error
    try:
        base, head = pr["base"], pr["head"]
        base_sha, head_sha = base["sha"], head["sha"]
        require_commit(base_sha, "live PR base"); require_commit(head_sha, "live PR candidate")
        return LiveReleaseContext(
            repository=base["repo"]["full_name"], head_repository=head["repo"]["full_name"],
            pr_number=pr["number"], pr_state=pr["state"], merged=pr["merged"],
            base_branch=base["ref"], base_sha=base_sha, head_branch=head["ref"], head_sha=head_sha,
            candidate_tree=tree(head_sha), remote_base_sha=remote_ref_sha(f"refs/heads/{GOVERNED_BASE_BRANCH}"),
            remote_head_sha=remote_ref_sha(f"refs/heads/{expected_head_branch}"),
            base_is_ancestor=is_ancestor(base_sha, head_sha), **ci_identity(run),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"live release context is incomplete or invalid: {error}") from error

def context_from_authorization(a): return LiveReleaseContext(**{context_field:a[auth_field] for auth_field, context_field in AUTH_CONTEXT_MAP.items()})

def validate_release_context(context, authorization, expected_pr_number, expected_head_branch):
    require_expected_identity(expected_pr_number, expected_head_branch)
    expected = {
        "repository": GOVERNED_REPOSITORY, "head_repository": GOVERNED_REPOSITORY,
        "pr_number": expected_pr_number, "pr_state": "open", "merged": False,
        "base_branch": GOVERNED_BASE_BRANCH, "head_branch": expected_head_branch,
        "base_is_ancestor": True, "ci_workflow_name": GOVERNED_WORKFLOW_NAME,
        "ci_workflow_path": GOVERNED_WORKFLOW_PATH, "ci_event": "pull_request",
        "ci_pr_number": expected_pr_number, "ci_status": "completed", "ci_conclusion": "success",
    }
    actual, problems = asdict(context), []
    for field, value in expected.items():
        if actual[field] != value: problems.append(f"live release context {field} is not the governed value")
    for field, value in {"remote_base_sha": context.base_sha, "remote_head_sha": context.head_sha, "ci_head_sha": context.head_sha}.items():
        if actual[field] != value: problems.append(f"live release context {field} does not match its canonical SHA")
    for auth_field, context_field in AUTH_CONTEXT_MAP.items():
        if authorization.get(auth_field) != actual[context_field]: problems.append(f"authorization {auth_field} differs from live release context")
    return problems

def validate_ci_against_context(run, context):
    try: identity = ci_identity(run)
    except ValueError as error: return [str(error)]
    return [f"CI {field} differs from authorized release context" for field, value in identity.items() if value != getattr(context, field)]

def load_authorization(commit):
    require_commit(commit, "authorization")
    try: a = json.loads(git("show", f"{commit}:{AUTH_PATH}"))
    except json.JSONDecodeError as error: raise ValueError("authorization JSON is invalid") from error
    if set(a) != AUTH_FIELDS or a.get("schema_version") != 1 or a.get("record_type") != "Bootstrap Governance v0 Merge Authorization": raise ValueError("authorization fields/protocol are invalid")
    for field in ("base_sha", "candidate_sha", "candidate_tree", "remote_base_sha", "remote_candidate_sha", "ci_candidate_sha"):
        if not isinstance(a.get(field), str) or not SHA.fullmatch(a[field]): raise ValueError(f"invalid authorization {field}")
    for field in ("pr_number", "ci_pr_number", "ci_run_id"):
        if not isinstance(a.get(field), int) or a[field] < 1: raise ValueError(f"invalid authorization {field}")
    if not isinstance(a.get("merged"), bool) or not isinstance(a.get("base_is_ancestor"), bool): raise ValueError("authorization boolean identity fields are invalid")
    if not isinstance(a.get("gate_record_commits"), dict) or set(a["gate_record_commits"]) != GATES: raise ValueError("authorization does not select all current gates")
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in a["gate_record_commits"].values()): raise ValueError("selected Gate Record commit is invalid")
    strings = set(AUTH_CONTEXT_MAP) - {"pr_number", "merged", "base_is_ancestor", "ci_pr_number"}
    strings |= {"authorization_id", "implementation_agent_id", "lead_agent_id", "release_agent_id"}
    if any(not isinstance(a.get(field), str) or not a[field].strip() for field in strings): raise ValueError("authorization string identity fields are incomplete")
    try:
        if datetime.fromisoformat(str(a["timestamp"]).replace("Z", "+00:00")).tzinfo is None: raise ValueError
    except ValueError as error: raise ValueError("authorization timestamp is invalid") from error
    return a

def load_gate_records(a):
    records, by_type = [], {}
    for gate, commit in a["gate_record_commits"].items():
        require_commit(commit, f"{gate} Gate Record")
        try: record = json.loads(git("show", f"{commit}:{RECORD_PATH}"))
        except json.JSONDecodeError as error: raise ValueError(f"invalid {gate} Gate Record JSON") from error
        records.append(record); by_type[gate] = record
    return records, by_type

def verify_authorization(authorization, reconcile_live=False, expected_pr_number=None, expected_head_branch=None):
    a = load_authorization(authorization)
    ref = auth_ref(a["pr_number"], a["candidate_sha"])
    result = subprocess.run(("git", "show-ref", "--verify", "--hash", ref), capture_output=True, text=True, check=False)
    if result.returncode or result.stdout.strip() != authorization: raise ValueError("exact authorization ref is missing or moved")
    if git("show", "-s", "--format=%P", authorization).split() != [a["candidate_sha"]]: raise ValueError("authorization parent is not candidate")
    if reconcile_live:
        require_expected_identity(expected_pr_number, expected_head_branch)
        context = build_live_release_context(os.environ.get("GITHUB_TOKEN"), a["ci_run_id"], expected_pr_number, expected_head_branch)
    else:
        context = context_from_authorization(a)
        expected_pr_number, expected_head_branch = context.pr_number, context.head_branch
    problems = validate_release_context(context, a, expected_pr_number, expected_head_branch)
    records, records_by_type = load_gate_records(a)
    problems.extend(validate_current_set(records, a["gate_record_commits"], context.base_sha, context.head_sha, context.candidate_tree, context.pr_number, a["implementation_agent_id"], a["lead_agent_id"]))
    if records_by_type.get("Release", {}).get("agent_id") != a["release_agent_id"]: problems.append("Release Gate identity differs from authorization")
    if reconcile_live: problems.extend(validate_selected_live(context.repository, context.pr_number, os.environ["GITHUB_TOKEN"], records_by_type, a["gate_record_commits"]))
    if problems: raise ValueError("current release evidence is invalid: " + "; ".join(problems))
    context_label = "live_release_context" if reconcile_live else "authorized_release_context"
    print(f"pr_number={context.pr_number}\nauthorization_sha={authorization}\nauthorization_ref={ref}\nbase_sha={context.base_sha}\ncandidate_sha={context.head_sha}\ncandidate_tree={context.candidate_tree}\n{context_label}=verified")
    return a, ref, context

def verify_integration(integration, authorization_arg=None, reconcile_live=False):
    require_commit(integration, "integration"); authorization = trailer(integration, AUTH_TRAILER); pr = int(trailer(integration, PR_TRAILER))
    if authorization_arg and authorization_arg != authorization: raise ValueError("supplied authorization differs from integration trailer")
    a, ref, context = verify_authorization(authorization, False)
    if reconcile_live:
        token = os.environ.get("GITHUB_TOKEN")
        if not token: raise ValueError("live selected-evidence validation requires GitHub context")
        _, records_by_type = load_gate_records(a)
        problems = validate_selected_live(context.repository, context.pr_number, token, records_by_type, a["gate_record_commits"])
        try: run = github_json(f"https://api.github.com/repos/{context.repository}/actions/runs/{a['ci_run_id']}", token)
        except Exception as error: raise ValueError("required integration CI evidence is unavailable") from error
        problems.extend(validate_ci_against_context(run, context))
        if problems: raise ValueError("current release evidence is invalid: " + "; ".join(problems))
    if context.pr_number != pr: raise ValueError("authorization PR differs from integration PR")
    parents = git("show", "-s", "--format=%P", integration).split()
    if len(parents) != 2 or parents[0] != context.base_sha or parents[1] != context.head_sha: raise ValueError("integration parents are not exact authorized base/candidate")
    if tree(context.head_sha) != context.candidate_tree or tree(integration) != context.candidate_tree: raise ValueError("integration tree differs from authorized candidate tree")
    print(f"pr_number={pr}\nauthorization_sha={authorization}\nauthorization_ref={ref}\nbase_sha={context.base_sha}\ncandidate_sha={context.head_sha}\ncandidate_tree={context.candidate_tree}\nintegration_sha={integration}\nintegration_tree={tree(integration)}\nexact_authorized_context=verified")

def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="mode", required=True)
    candidate = sub.add_parser("candidate"); candidate.add_argument("--base", required=True); candidate.add_argument("--candidate", required=True)
    authorization = sub.add_parser("authorization"); authorization.add_argument("--authorization", required=True); authorization.add_argument("--reconcile-live", action="store_true", required=True); authorization.add_argument("--pr-number", type=int, required=True); authorization.add_argument("--head-branch", required=True)
    integration = sub.add_parser("integration"); integration.add_argument("--integration", required=True); integration.add_argument("--authorization"); integration.add_argument("--reconcile-live", action="store_true")
    args = parser.parse_args()
    try:
        if args.mode == "candidate": verify_candidate(args.base, args.candidate)
        elif args.mode == "authorization": verify_authorization(args.authorization, True, args.pr_number, args.head_branch)
        else: verify_integration(args.integration, args.authorization, args.reconcile_live)
    except (ValueError, TypeError) as error:
        print(f"Integration identity validation failed: {error}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__": sys.exit(main())
