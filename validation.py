"""Strict, offline checks for a pinned RDF/XML taxonomy and model proposals."""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
OWL = "http://www.w3.org/2002/07/owl#"
SDG_PREFIX = "http://data.europa.eu/sdg/"


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_taxonomy(path: str | Path, expected_sha256: str) -> dict:
    """Read a complete pinned graph; reject a thin concept-scheme index."""
    if sha256(path) != expected_sha256:
        raise ValueError("Taxonomy snapshot SHA-256 mismatch")
    root = ET.parse(path).getroot()
    concepts: dict[str, dict] = {}
    top = set()
    for node in root:
        uri = node.get(f"{{{RDF}}}about")
        if not uri:
            continue
        if uri == "http://data.europa.eu/sdg":
            # The current scheme response also uses the non-standard casing
            # skos:hasTopconcept; recognise it explicitly and record the quirk.
            for tag in ("hasTopConcept", "hasTopconcept"):
                top.update(x.get(f"{{{RDF}}}resource") for x in node.findall(f"{{{SKOS}}}{tag}"))
        if not uri.startswith(SDG_PREFIX):
            continue
        labels = {
            x.get("{http://www.w3.org/XML/1998/namespace}lang", ""): (x.text or "").strip()
            for x in node.findall(f"{{{SKOS}}}prefLabel") if (x.text or "").strip()
        }
        parents = {
            x.get(f"{{{RDF}}}resource")
            for x in node.findall(f"{{{SKOS}}}broader")
            if x.get(f"{{{RDF}}}resource")
        }
        deprecated = any(
            (x.text or "").strip().lower() in {"true", "1"}
            for x in node.findall(f"{{{OWL}}}deprecated")
        )
        is_skos_concept = any(
            x.get(f"{{{RDF}}}resource") == SKOS + "Concept"
            for x in node.findall(f"{{{RDF}}}type")
        )
        entry = concepts.setdefault(uri, {"labels": {}, "parents": set(), "deprecated": False, "typed": False})
        entry["labels"].update(labels)
        entry["parents"].update(parents)
        entry["deprecated"] |= deprecated
        entry["typed"] |= is_skos_concept
    if len(top) != 17:
        raise ValueError(f"Expected 17 declared SDG top concepts, found {len(top)}")
    missing_labels = [uri for uri, value in concepts.items() if not value["labels"].get("en")]
    missing_parents = [(u, p) for u, v in concepts.items() for p in v["parents"] if p not in concepts]
    missing_types = [uri for uri, value in concepts.items() if not value["typed"]]
    if missing_labels or missing_parents or missing_types or not top <= concepts.keys():
        raise ValueError(
            f"Incomplete taxonomy: {len(missing_labels)} missing English labels, "
            f"{len(missing_parents)} missing parent nodes, {len(missing_types)} missing SKOS types, "
            f"{len(top - concepts.keys())} missing top nodes"
        )
    if any(concepts[u]["parents"] for u in top):
        raise ValueError("Top concept has a broader concept")
    visited, active = set(), set()

    def visit(uri: str):
        if uri in active:
            raise ValueError(f"Cycle in taxonomy at {uri}")
        if uri in visited:
            return
        active.add(uri)
        for parent in concepts[uri]["parents"]:
            visit(parent)
        active.remove(uri)
        visited.add(uri)

    for uri in concepts:
        visit(uri)
    roots = {uri for uri, value in concepts.items() if not value["parents"]}
    if roots != top:
        raise ValueError(f"Unexpected hierarchy roots: {len(roots - top)}")
    return {"concepts": concepts, "top": top, "sha256": expected_sha256}


def verified_span(original: str, proposed: str) -> tuple[int, int, str] | None:
    """Permit whitespace variation, but return only exact source bytes and offsets."""
    if not proposed or not proposed.strip():
        return None
    start = original.find(proposed)
    if start >= 0:
        return start, start + len(proposed), proposed
    words = re.findall(r"\S+", proposed)
    if not words:
        return None
    pattern = r"\s+".join(re.escape(word) for word in words)
    matches = list(re.finditer(pattern, original))
    if len(matches) != 1:
        return None  # Ambiguous evidence requires review.
    match = matches[0]
    return match.start(), match.end(), original[match.start():match.end()]


def validate_candidate(fields: dict[str, str], proposal: dict, taxonomy: dict) -> dict:
    uri = proposal.get("concept_uri")
    if uri not in taxonomy["concepts"]:
        return {"status": "rejected_candidate", "reason": "unknown_concept_uri"}
    if taxonomy["concepts"][uri]["deprecated"]:
        return {"status": "rejected_candidate", "reason": "deprecated_concept"}
    field = proposal.get("evidence_field")
    if field not in {"objective", "description"} or field not in fields:
        return {"status": "rejected_candidate", "reason": "invalid_evidence_field"}
    excerpt = proposal.get("evidence_excerpt")
    if not isinstance(excerpt, str):
        return {"status": "rejected_candidate", "reason": "missing_evidence"}
    span = verified_span(fields[field], excerpt)
    if span is None:
        return {"status": "rejected_candidate", "reason": "unverified_evidence"}
    if not isinstance(proposal.get("rationale"), str) or not proposal["rationale"].strip():
        return {"status": "rejected_candidate", "reason": "missing_rationale"}
    if proposal.get("confidence_level") not in {"strong", "weak", "uncertain"}:
        return {"status": "rejected_candidate", "reason": "invalid_confidence"}
    start, end, exact_quote = span
    return {
        "status": "validated_candidate",
        "concept_uri": uri,
        "evidence_field": field,
        "evidence_excerpt": exact_quote,
        "evidence_start": start,
        "evidence_end": end,
        "confidence_level": proposal["confidence_level"],
        "rationale": proposal["rationale"],
    }


def ancestor_goals(uri: str, taxonomy: dict) -> set[str]:
    concepts, top = taxonomy["concepts"], taxonomy["top"]
    if uri not in concepts:
        raise KeyError(uri)
    found, seen, queue = set(), set(), [uri]
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in top:
            found.add(current)
        queue.extend(concepts[current]["parents"])
    return found
