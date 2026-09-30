"""Project-level aggregation of technical proposals, never final SDG outcomes."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from itertools import combinations


def run_records(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    projects = {
        pid: {
            "project_id": pid, "state": state, "abstention_reason": reason,
            "error": error, "proposals": [],
        }
        for pid, state, reason, error in conn.execute(
            "SELECT project_id,state,abstention_reason,error FROM projects WHERE run_id=?",
            (run_id,),
        )
    }
    for pid, index, raw, validation, technical_state in conn.execute(
        "SELECT project_id,ordinal,raw_json,validation_json,technical_state "
        "FROM proposals WHERE run_id=? ORDER BY project_id,ordinal", (run_id,)
    ):
        projects[pid]["proposals"].append({
            "ordinal": index, "raw": json.loads(raw), "validation": json.loads(validation),
            "technical_state": technical_state,
        })
    return list(projects.values())


def summary(records: list[dict], expected_project_ids: set[str] | None = None) -> dict:
    ids = [r["project_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate project records")
    if expected_project_ids is not None and not set(ids) <= expected_project_ids:
        raise ValueError("Run contains IDs outside the declared cohort")
    states = Counter(r["state"] for r in records)
    successful = sum(n for state, n in states.items() if state != "model_error_retryable")
    model_abstained = states["model_abstained_pending_review"]
    technically_valid = states["validated_proposals_pending_review"]
    project_goals = {}
    for record in records:
        goals = set()
        for proposal in record["proposals"]:
            if proposal["technical_state"] == "validated_candidate":
                goals.update(proposal["validation"].get("goal_uris", []))
        project_goals[record["project_id"]] = goals
    goal_counts = Counter(goal for goals in project_goals.values() for goal in goals)
    pair_counts = Counter(pair for goals in project_goals.values()
                          for pair in combinations(sorted(goals), 2))
    denominator = len(expected_project_ids) if expected_project_ids is not None else None
    return {
        "cohort_n": denominator, "recorded_n": len(records),
        "processed_successfully_n": successful, "state_counts": dict(states),
        "model_abstained_n": model_abstained,
        "technically_valid_project_n": technically_valid,
        "goal_project_counts": dict(sorted(goal_counts.items())),
        "goal_pair_project_counts": {"|".join(pair): n for pair, n in sorted(pair_counts.items())},
        "complete": denominator is not None and successful == denominator,
        "note": "All concept assignments counted here are technical proposals pending human review.",
    }
