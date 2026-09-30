"""Read-only Streamlit audit interface for CORDIS → SDG technical proposals.

Run with: streamlit run app.py
Optional server-side CORDIS_SDG_DB=/absolute/path/to/run.db
No user-controlled database path, writes, or final-mapping claims.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path

from analytics import run_records, summary
from validation import load_taxonomy, sha256

BASE = Path(__file__).resolve().parent


def original_excerpt_html(source: str, start: int, end: int) -> str:
    """Highlight only a verified original span; escape every source character."""
    if not (isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(source)):
        raise ValueError("Evidence offsets outside the original source field")
    return (
        '<div class="source-text">' + html.escape(source[:start])
        + "<mark>" + html.escape(source[start:end]) + "</mark>"
        + html.escape(source[end:]) + "</div>"
    )


def open_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def source_data():
    manifest = json.loads((BASE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    subset_manifest = json.loads((BASE / "DEPLOYMENT_MANIFEST.json").read_text(encoding="utf-8"))
    if subset_manifest["source_corpus_sha256"] != manifest["cordis"]["sha256"]:
        raise ValueError("Extracted subset source provenance mismatch")
    if sha256(BASE / "project_subset.json") != subset_manifest["subset_sha256"]:
        raise ValueError("Extracted project subset checksum mismatch")
    taxonomy = load_taxonomy(BASE / "sdg_full.rdf", manifest["taxonomy_snapshot"]["sha256"])
    with (BASE / "review_sample.csv").open(encoding="utf-8") as stream:
        sample = list(csv.DictReader(stream))
    sample_manifest = json.loads((BASE / "SAMPLE_MANIFEST.json").read_text(encoding="utf-8"))
    if sha256(BASE / "review_sample.csv") != sample_manifest["sample_sha256"]:
        raise ValueError("Review sample checksum mismatch")
    return manifest, taxonomy, sample


def project_fields(corpus_file: Path, ids: set[str]) -> dict[str, dict]:
    # corpus_file is retained for interface compatibility; no live ZIP download.
    subset = json.loads((BASE / "project_subset.json").read_text(encoding="utf-8"))
    return {pid: fields for pid, fields in subset.items() if pid in ids}


def main():
    import streamlit as st

    st.set_page_config(page_title="CORDIS → SDGs | Evidence explorer", layout="wide")
    st.markdown("""<style>
    .block-container{max-width:1200px;padding-top:1.7rem}
    .source-text{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.7;
      background:#f4f7fb;border:1px solid #d6e0ed;border-radius:9px;padding:1rem;color:#12243a}
    mark{background:#ffe28a;color:#12243a;padding:0 .08rem}
    </style>""", unsafe_allow_html=True)
    st.title("CORDIS → SDGs")
    st.caption("Explore project evidence and technical SDG proposals. All model proposals require human review.")
    st.caption("Hosted data: unchanged objectives extracted from the pinned CORDIS snapshot. The subset checksum is verified here; the full ZIP checksum was verified during export. Model results are a static snapshot, not live inference.")
    try:
        manifest, taxonomy, sample = source_data()
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        st.error(f"Source integrity check failed: {exc}")
        st.stop()
    goal_labels = {
        uri: f"SDG {uri.rsplit('/', 1)[1]} · {taxonomy['concepts'][uri]['labels']['en']}"
        for uri in taxonomy["top"]
    }
    sample_cohorts = {
        cohort: {r["project_id"] for r in sample if r["cohort"] == cohort}
        for cohort in ("pilot", "holdout")
    }
    db_path = Path(os.environ.get("CORDIS_SDG_DB", str(BASE / "cordis_sdg_pilot.db")))
    records = []
    run_id = None
    if db_path.is_file():
        try:
            with closing(open_read_only(db_path)) as conn:
                runs = [row[0] for row in conn.execute("SELECT run_id FROM runs ORDER BY run_id")]
                if runs:
                    run_id = st.sidebar.selectbox("Processing run", runs)
                    records = run_records(conn, run_id)
        except sqlite3.DatabaseError as exc:
            st.error(f"Could not read the run database: {exc}")
            st.stop()
    if run_id:
        ids = {r["project_id"] for r in records}
        cohort = next((name for name, members in sample_cohorts.items() if ids <= members), None)
        expected = sample_cohorts[cohort] if cohort else None
        metrics = summary(records, expected)
        st.subheader("Run status")
        a, b, c, d = st.columns(4)
        a.metric("Recorded projects", f"{metrics['recorded_n']}" +
                 (f" / {metrics['cohort_n']}" if metrics["cohort_n"] else ""))
        b.metric("Processed successfully", metrics["processed_successfully_n"])
        c.metric("Model abstentions", metrics["model_abstained_n"])
        d.metric("Projects with technically valid proposals", metrics["technically_valid_project_n"])
        if not metrics["complete"]:
            st.info("This run is incomplete or has no declared cohort denominator. Counts are descriptive, not coverage rates.")
        st.caption("Technically valid means that the URI, schema and quoted source span passed checks. It does not confirm an SDG contribution.")
        if metrics["goal_project_counts"]:
            st.subheader("Projects per proposed SDG")
            st.caption("Each project is counted at most once per SDG. One project can appear under several SDGs.")
            import pandas as pd
            chart = pd.DataFrame([
                {"SDG": f"SDG {uri.rsplit('/', 1)[1]}", "Projects": count}
                for uri, count in metrics["goal_project_counts"].items()
            ]).set_index("SDG")
            st.bar_chart(chart)
    else:
        st.info("No model run is available yet. Browse the real CORDIS pilot projects below; no SDG mappings are claimed.")
        records = [{"project_id": r["project_id"], "state": "not_processed", "proposals": []}
                   for r in sample if r["cohort"] == "pilot"]
        ids = {r["project_id"] for r in records}
    corpus_file = BASE / manifest["cordis"]["file"]
    fields = project_fields(corpus_file, ids)
    st.subheader("Project explorer")
    query = st.text_input("Search project ID or title").strip().lower()
    states = sorted({r["state"] for r in records})
    state_filter = st.multiselect("Technical state", states, default=states)
    confidence = st.selectbox("Proposal confidence", ["Any", "strong", "weak", "uncertain"])
    goal_options = sorted(taxonomy["top"], key=lambda u: int(u.rsplit("/", 1)[1]))
    selected_goal = st.selectbox("Proposed SDG", ["Any"] + goal_options,
                                 format_func=lambda u: u if u == "Any" else goal_labels[u])
    filtered = []
    for record in records:
        pid = record["project_id"]
        if record["state"] not in state_filter or pid not in fields:
            continue
        if query and query not in pid.lower() and query not in fields[pid]["title"].lower():
            continue
        valid = [p["validation"] for p in record["proposals"]
                 if p["technical_state"] == "validated_candidate"]
        if confidence != "Any" and not any(p.get("confidence_level") == confidence for p in valid):
            continue
        if selected_goal != "Any" and not any(selected_goal in p.get("goal_uris", []) for p in valid):
            continue
        filtered.append(record)
    st.caption(f"{len(filtered)} projects match the filters")
    if not filtered:
        st.stop()
    st.dataframe(
        [{"Project ID": r["project_id"], "Title": fields[r["project_id"]]["title"],
          "Technical state": r["state"]} for r in filtered[:250]],
        hide_index=True, width="stretch",
    )
    if len(filtered) > 250:
        st.caption("Showing the first 250 rows. Narrow the search to inspect another project.")
    chosen = st.selectbox("Inspect project", filtered,
                          format_func=lambda r: f"{r['project_id']} · {fields[r['project_id']]['title']}")
    project = fields[chosen["project_id"]]
    st.markdown(f"### {project['title']}")
    st.caption(f"CORDIS project {chosen['project_id']} · {project['topic']}")
    st.write(f"Technical state: **{chosen['state']}**")
    if chosen.get("abstention_reason"):
        st.write("Model abstention reason:", chosen["abstention_reason"])
    if chosen.get("error"):
        st.warning("Processing error: " + chosen["error"])
    with st.expander("Method and provenance"):
        st.write("CORDIS ZIP SHA-256:", manifest["cordis"]["sha256"])
        st.write("SDG RDF SHA-256:", manifest["taxonomy_snapshot"]["sha256"])
        st.write("Selection: 20 pilot projects and 60 human-reviewed holdout projects across 15 programme parts.")
        st.write("All assignments in this interface are model proposals pending human review.")
    if not chosen["proposals"]:
        st.markdown("#### Original objective")
        st.text(project["objective"])
        return
    for proposal in chosen["proposals"]:
        result = proposal["validation"]
        raw = proposal["raw"]
        uri = result.get("concept_uri", raw.get("concept_uri", "Unrecognised URI"))
        label = taxonomy["concepts"].get(uri, {}).get("labels", {}).get("en", "")
        st.markdown(f"#### Proposal {proposal['ordinal'] + 1}: {label or uri}")
        st.caption(uri)
        if proposal["technical_state"] != "validated_candidate":
            st.warning("Rejected technical proposal: " + result.get("reason", "unspecified"))
            continue
        goals = result.get("goal_uris", [])
        st.write("Ancestor goals:", ", ".join(goal_labels.get(g, g) for g in goals))
        st.write("Qualitative confidence:", result["confidence_level"])
        st.write("Proposed contribution:", raw.get("contribution_mechanism", ""))
        st.write("Model rationale:", result["rationale"])
        st.write("Uncertainty:", raw.get("uncertainty") or "None stated")
        if result["evidence_field"] == "objective":
            start, end = result["evidence_start"], result["evidence_end"]
            source = project["objective"]
            if source[start:end] != result["evidence_excerpt"]:
                st.error("Evidence offsets fail verification against the pinned original objective.")
            else:
                st.markdown(original_excerpt_html(source, start, end), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
