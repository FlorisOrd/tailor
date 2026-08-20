"""Validate candidate-bound Gate Records exported from agent-published GitHub comments."""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
GATES = {"Independent Code Review", "QA", "Security Review", "Release"}
SEVERITIES = {"BLOCKING", "MAJOR", "MINOR", "SUGGESTION"}

def validate_record(record: object) -> list[str]:
    if not isinstance(record, dict): return ["record must be an object"]
    required = {"schema_version", "gate_record_id", "gate_type", "agent_role", "agent_id", "pr_number", "base_sha", "candidate_sha", "candidate_tree", "timestamp", "scope", "checks", "findings", "disposition", "repository_state_changed", "supersedes", "superseded_by"}
    problems = []
    if set(record) != required: problems.append("record fields do not exactly match the Gate Record schema")
    if record.get("schema_version") != 1: problems.append("schema_version must be 1")
    if record.get("gate_type") not in GATES: problems.append("invalid gate_type")
    if record.get("agent_role") != record.get("gate_type"): problems.append("agent_role must equal gate_type")
    for field in ("gate_record_id", "agent_id", "scope"):
        if not isinstance(record.get(field), str) or not record[field].strip(): problems.append(f"{field} must be non-empty")
    if not isinstance(record.get("pr_number"), int) or record["pr_number"] < 1: problems.append("pr_number must be positive")
    for field in ("base_sha", "candidate_sha", "candidate_tree"):
        if not isinstance(record.get(field), str) or not SHA.fullmatch(record[field]): problems.append(f"{field} must be a lowercase full SHA")
    try: datetime.fromisoformat(str(record.get("timestamp")).replace("Z", "+00:00"))
    except ValueError: problems.append("timestamp must be ISO-8601")
    if not isinstance(record.get("checks"), list) or not record["checks"] or not all(isinstance(x, str) and x for x in record["checks"]): problems.append("checks must be a non-empty string array")
    if record.get("disposition") not in {"PASS", "FAIL", "PENDING", "N/A"}: problems.append("invalid disposition")
    if not isinstance(record.get("repository_state_changed"), bool): problems.append("repository_state_changed must be boolean")
    if not isinstance(record.get("findings"), list): problems.append("findings must be an array")
    else:
        for finding in record["findings"]:
            if not isinstance(finding, dict) or finding.get("severity") not in SEVERITIES or finding.get("status") not in {"OPEN", "CLOSED"}: problems.append("invalid finding")
    return problems

def validate_set(records: list[dict[str, object]], base: str, candidate: str, candidate_tree: str, pr: int, required: set[str]) -> list[str]:
    problems, selected, gate_counts = [], {}, {}
    current = [r for r in records if r.get("superseded_by") is None]
    ids = [r.get("gate_record_id") for r in current]
    if len(ids) != len(set(ids)): problems.append("active gate_record_id values must be unique")
    for record in current:
        record_problems = validate_record(record)
        problems.extend(f"{record.get('gate_record_id')}: {p}" for p in record_problems)
        if record_problems: continue
        gate_counts[record["gate_type"]] = gate_counts.get(record["gate_type"], 0) + 1
        if record.get("gate_type") in required and record.get("disposition") == "PASS": selected[record["gate_type"]] = record
    for gate in required:
        if gate not in selected: problems.append(f"missing current PASS Gate Record: {gate}")
        if gate_counts.get(gate, 0) != 1: problems.append(f"gate must have exactly one active Gate Record: {gate}")
    for gate, record in selected.items():
        if (record["base_sha"], record["candidate_sha"], record["candidate_tree"], record["pr_number"]) != (base, candidate, candidate_tree, pr): problems.append(f"stale or mismatched Gate Record: {gate}")
    current_ids = {r.get("gate_record_id") for r in current}
    for record in current:
        if validate_record(record): continue
        for finding in record["findings"]:
            if finding["severity"] in {"BLOCKING", "MAJOR"}:
                if finding["status"] != "CLOSED": problems.append(f"open blocking finding in {record['gate_type']}")
                elif not finding.get("rechecked_by_gate_record_id") or finding["rechecked_by_gate_record_id"] not in current_ids: problems.append(f"closed blocking finding lacks a current independent recheck record in {record['gate_type']}")
    agent_ids = [r["agent_id"] for r in selected.values()]
    if len(agent_ids) != len(set(agent_ids)): problems.append("required gates must use distinct agent identities")
    return problems

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("record_files", nargs="+")
    parser.add_argument("--base", required=True); parser.add_argument("--candidate", required=True); parser.add_argument("--tree", required=True); parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--require", nargs="+", choices=sorted(GATES), required=True); args = parser.parse_args()
    records = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.record_files]
    problems = validate_set(records, args.base, args.candidate, args.tree, args.pr, set(args.require))
    if problems: print("Gate Record validation failed:"); [print(f"- {p}") for p in problems]; return 1
    print("Gate Record validation passed."); return 0

if __name__ == "__main__": sys.exit(main())
