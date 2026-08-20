"""Verify exact governed candidate and authorized integration identities."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime

SHA = re.compile(r"^[0-9a-f]{40}$")
TRAILER = "Governance-Authorization"
AUTH_PATH = ".github/governance/authorization.json"
AUTH_REF_PREFIXES = ("refs/governance/authorizations/", "refs/remotes/origin/governance-authorizations/")

def git(*args: str) -> str:
    result = subprocess.run(("git", *args), capture_output=True, text=True, check=False)
    if result.returncode: raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()

def require_sha(value: str, label: str, object_type: str = "commit") -> None:
    if not SHA.fullmatch(value): raise ValueError(f"{label} must be a lowercase full 40-character Git SHA")
    if git("cat-file", "-t", value) != object_type: raise ValueError(f"{label} does not identify a {object_type}: {value}")

def tree(commit: str) -> str: return git("rev-parse", f"{commit}^{{tree}}")

def verify_candidate(base: str, candidate: str) -> None:
    require_sha(base, "base"); require_sha(candidate, "candidate")
    if subprocess.run(("git", "merge-base", "--is-ancestor", base, candidate), check=False).returncode:
        raise ValueError("recorded base is not an ancestor of candidate")
    behind, ahead = git("rev-list", "--left-right", "--count", f"{base}...{candidate}").split()
    if behind != "0": raise ValueError(f"candidate is behind recorded base by {behind} commit(s)")
    print(f"base_sha={base}\ncandidate_sha={candidate}\ncandidate_tree={tree(candidate)}\ncandidate_commits_ahead={ahead}")

def authorization_from_trailer(integration: str) -> str:
    values = git("show", "-s", f"--format=%(trailers:key={TRAILER},valueonly)", integration).splitlines()
    if len(values) != 1 or not values[0].strip(): raise ValueError(f"integration must contain exactly one {TRAILER} trailer")
    return values[0].strip()

def authorization_is_published(authorization: str) -> bool:
    refs = git("for-each-ref", "--format=%(refname) %(objectname)", *AUTH_REF_PREFIXES)
    return any(line.split()[-1] == authorization for line in refs.splitlines() if line.strip())

def load_authorization(authorization: str) -> dict[str, object]:
    require_sha(authorization, "authorization")
    if not authorization_is_published(authorization): raise ValueError("authorization commit is not published under the governed authorization ref namespace")
    try: record = json.loads(git("show", f"{authorization}:{AUTH_PATH}"))
    except json.JSONDecodeError as error: raise ValueError(f"authorization record is not valid JSON: {error}") from error
    required = {"schema_version", "authorization_id", "pr_number", "base_sha", "candidate_sha", "candidate_tree", "timestamp", "release_agent_id", "release_gate_record_id"}
    if set(record) != required or record.get("schema_version") != 1: raise ValueError("authorization record fields/schema are invalid")
    for field in ("base_sha", "candidate_sha", "candidate_tree"):
        if not isinstance(record[field], str) or not SHA.fullmatch(record[field]): raise ValueError(f"authorization {field} is not a full lowercase SHA")
    if not isinstance(record["pr_number"], int) or record["pr_number"] < 1: raise ValueError("authorization pr_number must be positive")
    for field in ("authorization_id", "release_agent_id", "release_gate_record_id"):
        if not isinstance(record[field], str) or not record[field].strip(): raise ValueError(f"authorization {field} must be non-empty")
    try: datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
    except ValueError as error: raise ValueError("authorization timestamp must be ISO-8601") from error
    return record

def verify_integration(integration: str, authorization_arg: str | None = None) -> None:
    require_sha(integration, "integration")
    authorization = authorization_from_trailer(integration)
    if authorization_arg is not None and authorization_arg != authorization: raise ValueError("supplied authorization does not equal the integration trailer")
    record = load_authorization(authorization)
    expected_base, expected_candidate, expected_tree = str(record["base_sha"]), str(record["candidate_sha"]), str(record["candidate_tree"])
    require_sha(expected_base, "authorized base"); require_sha(expected_candidate, "authorized candidate")
    authorization_parents = git("show", "-s", "--format=%P", authorization).split()
    if authorization_parents != [expected_candidate]: raise ValueError("authorization commit must have the exact authorized candidate as its only parent")
    parents = git("show", "-s", "--format=%P", integration).split()
    if len(parents) != 2: raise ValueError(f"integration must have exactly two parents; found {len(parents)}")
    if parents[0] != expected_base: raise ValueError(f"first parent is not the exact authorized base: {parents[0]} != {expected_base}")
    if parents[1] != expected_candidate: raise ValueError(f"second parent is not the exact authorized candidate: {parents[1]} != {expected_candidate}")
    if tree(expected_candidate) != expected_tree: raise ValueError(f"candidate tree is not the exact authorized tree: {tree(expected_candidate)} != {expected_tree}")
    if tree(integration) != expected_tree: raise ValueError(f"integration tree is not the exact authorized tree: {tree(integration)} != {expected_tree}")
    print(f"authorization_sha={authorization}\nbase_sha={expected_base}\ncandidate_sha={expected_candidate}\ncandidate_tree={expected_tree}\nintegration_sha={integration}\nintegration_tree={tree(integration)}\nexact_authorized_tuple=verified")

def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="mode", required=True)
    candidate = sub.add_parser("candidate"); candidate.add_argument("--base", required=True); candidate.add_argument("--candidate", required=True)
    integration = sub.add_parser("integration"); integration.add_argument("--integration", required=True); integration.add_argument("--authorization")
    args = parser.parse_args()
    try: verify_candidate(args.base, args.candidate) if args.mode == "candidate" else verify_integration(args.integration, args.authorization)
    except ValueError as error: print(f"Integration identity validation failed: {error}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__": sys.exit(main())
