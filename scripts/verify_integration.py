"""Verify exact governed candidate and authorized integration identities."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime
from validate_gate_records import discover_record_objects, validate_set as validate_gate_record_set

SHA = re.compile(r"^[0-9a-f]{40}$")
TRAILER = "Governance-Authorization"
PR_TRAILER = "Governance-PR"
AUTH_PATH = ".github/governance/authorization.json"

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

def trailer_value(integration: str, key: str) -> str:
    values = git("show", "-s", f"--format=%(trailers:key={key},valueonly)", integration).splitlines()
    if len(values) != 1 or not values[0].strip(): raise ValueError(f"integration must contain exactly one {TRAILER} trailer")
    return values[0].strip()

def canonical_authorization_refs(pr_number: int, candidate: str) -> tuple[str, str]:
    suffix = f"pr-{pr_number}/{candidate}"
    return f"refs/governance/authorizations/{suffix}", f"refs/remotes/origin/governance-authorizations/{suffix}"

def require_exact_authorization_ref(authorization: str, pr_number: int, candidate: str) -> str:
    found = []
    for ref in canonical_authorization_refs(pr_number, candidate):
        result = subprocess.run(("git", "show-ref", "--verify", "--hash", ref), capture_output=True, text=True, check=False)
        if result.returncode == 0: found.append((ref, result.stdout.strip()))
    if not found: raise ValueError("exact canonical authorization ref is missing")
    for ref, value in found:
        if value != authorization: raise ValueError(f"canonical authorization ref was moved or points elsewhere: {ref}")
    return found[0][0]

def load_authorization(authorization: str) -> dict[str, object]:
    require_sha(authorization, "authorization")
    try: record = json.loads(git("show", f"{authorization}:{AUTH_PATH}"))
    except json.JSONDecodeError as error: raise ValueError(f"authorization record is not valid JSON: {error}") from error
    required = {"schema_version", "authorization_id", "pr_number", "base_sha", "candidate_sha", "candidate_tree", "timestamp", "release_agent_id", "release_gate_record_id", "gate_record_commits"}
    if set(record) != required or record.get("schema_version") != 1: raise ValueError("authorization record fields/schema are invalid")
    for field in ("base_sha", "candidate_sha", "candidate_tree"):
        if not isinstance(record[field], str) or not SHA.fullmatch(record[field]): raise ValueError(f"authorization {field} is not a full lowercase SHA")
    if not isinstance(record["pr_number"], int) or record["pr_number"] < 1: raise ValueError("authorization pr_number must be positive")
    for field in ("authorization_id", "release_agent_id", "release_gate_record_id"):
        if not isinstance(record[field], str) or not record[field].strip(): raise ValueError(f"authorization {field} must be non-empty")
    expected_gates = {"Independent Code Review", "QA", "Security Review"}
    if not isinstance(record["gate_record_commits"], dict) or set(record["gate_record_commits"]) != expected_gates: raise ValueError("authorization gate_record_commits are invalid")
    for value in record["gate_record_commits"].values():
        if not isinstance(value, str) or not SHA.fullmatch(value): raise ValueError("authorization Gate Record commit must be a full lowercase SHA")
    try: datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
    except ValueError as error: raise ValueError("authorization timestamp must be ISO-8601") from error
    return record

def verify_integration(integration: str, authorization_arg: str | None = None) -> None:
    require_sha(integration, "integration")
    authorization = trailer_value(integration, TRAILER)
    try: integration_pr = int(trailer_value(integration, PR_TRAILER))
    except ValueError as error: raise ValueError("Governance-PR trailer must be a positive integer") from error
    if integration_pr < 1: raise ValueError("Governance-PR trailer must be a positive integer")
    if authorization_arg is not None and authorization_arg != authorization: raise ValueError("supplied authorization does not equal the integration trailer")
    record = load_authorization(authorization)
    expected_base, expected_candidate, expected_tree = str(record["base_sha"]), str(record["candidate_sha"]), str(record["candidate_tree"])
    require_sha(expected_base, "authorized base"); require_sha(expected_candidate, "authorized candidate")
    if record["pr_number"] != integration_pr: raise ValueError("authorization PR does not equal the exact integration PR trailer")
    canonical_ref = require_exact_authorization_ref(authorization, integration_pr, expected_candidate)
    gate_records,gate_commits=discover_record_objects(integration_pr)
    for expected_gate, authorized_commit in record["gate_record_commits"].items():
        require_sha(authorized_commit,f"{expected_gate} Gate Record commit")
        matches=[r for r in gate_records if r.get("gate_type")==expected_gate and r.get("superseded_by") is None]
        if len(matches)!=1 or gate_commits.get(matches[0].get("gate_record_id"))!=authorized_commit: raise ValueError(f"authorization does not name the exact active {expected_gate} Gate Record commit")
    gate_problems=validate_gate_record_set(gate_records,expected_base,expected_candidate,expected_tree,integration_pr,set(record["gate_record_commits"]),gate_commits)
    if gate_problems: raise ValueError("authorized Gate Records are invalid: "+"; ".join(gate_problems))
    authorization_parents = git("show", "-s", "--format=%P", authorization).split()
    if authorization_parents != [expected_candidate]: raise ValueError("authorization commit must have the exact authorized candidate as its only parent")
    parents = git("show", "-s", "--format=%P", integration).split()
    if len(parents) != 2: raise ValueError(f"integration must have exactly two parents; found {len(parents)}")
    if parents[0] != expected_base: raise ValueError(f"first parent is not the exact authorized base: {parents[0]} != {expected_base}")
    if parents[1] != expected_candidate: raise ValueError(f"second parent is not the exact authorized candidate: {parents[1]} != {expected_candidate}")
    if tree(expected_candidate) != expected_tree: raise ValueError(f"candidate tree is not the exact authorized tree: {tree(expected_candidate)} != {expected_tree}")
    if tree(integration) != expected_tree: raise ValueError(f"integration tree is not the exact authorized tree: {tree(integration)} != {expected_tree}")
    print(f"pr_number={integration_pr}\nauthorization_sha={authorization}\nauthorization_ref={canonical_ref}\nbase_sha={expected_base}\ncandidate_sha={expected_candidate}\ncandidate_tree={expected_tree}\nintegration_sha={integration}\nintegration_tree={tree(integration)}\nexact_authorized_tuple=verified")

def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="mode", required=True)
    candidate = sub.add_parser("candidate"); candidate.add_argument("--base", required=True); candidate.add_argument("--candidate", required=True)
    integration = sub.add_parser("integration"); integration.add_argument("--integration", required=True); integration.add_argument("--authorization")
    args = parser.parse_args()
    try: verify_candidate(args.base, args.candidate) if args.mode == "candidate" else verify_integration(args.integration, args.authorization)
    except ValueError as error: print(f"Integration identity validation failed: {error}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__": sys.exit(main())
