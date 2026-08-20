"""Report and verify governed candidate/integration Git identities."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def require_commit(sha: str, label: str) -> None:
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError(f"{label} must be a full 40-character Git SHA")
    if git("cat-file", "-t", sha) != "commit":
        raise ValueError(f"{label} does not identify a commit: {sha}")


def tree(sha: str) -> str:
    return git("rev-parse", f"{sha}^{{tree}}")


def verify_candidate(base: str, candidate: str) -> None:
    require_commit(base, "base")
    require_commit(candidate, "candidate")
    if subprocess.run(
        ("git", "merge-base", "--is-ancestor", base, candidate), check=False
    ).returncode:
        raise ValueError("recorded base is not an ancestor of candidate")
    behind, ahead = git("rev-list", "--left-right", "--count", f"{base}...{candidate}").split()
    if behind != "0":
        raise ValueError(f"candidate is behind recorded base by {behind} commit(s)")
    print(f"base_sha={base}")
    print(f"candidate_sha={candidate}")
    print(f"candidate_tree={tree(candidate)}")
    print(f"candidate_commits_ahead={ahead}")


def verify_integration(integration: str) -> None:
    require_commit(integration, "integration")
    parents = git("show", "-s", "--format=%P", integration).split()
    if len(parents) != 2:
        raise ValueError(
            "governed main integration must be a two-parent merge commit; "
            f"found {len(parents)} parent(s)"
        )
    base, candidate = parents
    if subprocess.run(
        ("git", "merge-base", "--is-ancestor", base, candidate), check=False
    ).returncode:
        raise ValueError("merge candidate parent does not contain the base parent")
    integration_tree = tree(integration)
    candidate_tree = tree(candidate)
    if integration_tree != candidate_tree:
        raise ValueError(
            "integration tree differs from verified candidate parent tree: "
            f"{integration_tree} != {candidate_tree}"
        )
    print(f"base_sha={base}")
    print(f"candidate_sha={candidate}")
    print(f"candidate_tree={candidate_tree}")
    print(f"integration_sha={integration}")
    print(f"integration_tree={integration_tree}")
    print("tree_identity=verified")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    candidate = subparsers.add_parser("candidate")
    candidate.add_argument("--base", required=True)
    candidate.add_argument("--candidate", required=True)
    integration = subparsers.add_parser("integration")
    integration.add_argument("--integration", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "candidate":
            verify_candidate(args.base, args.candidate)
        else:
            verify_integration(args.integration)
    except ValueError as error:
        print(f"Integration identity validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
