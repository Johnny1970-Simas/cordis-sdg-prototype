# CORDIS → SDGs Prototype

Evidence-based mapping of CORDIS research projects to the United Nations Sustainable Development Goals (SDGs), using local language-model inference, deterministic validation and human review.

**Live prototype:** https://cordis-sdg-prototype.streamlit.app/

## Overview

This repository contains a research prototype for exploring whether evidence contained in CORDIS project objectives can support proposed mappings to specific Sustainable Development Goal targets.

The system is designed around a deliberately conservative principle:

> Model-generated mappings are proposals for human review, not confirmed statements that a project contributes to an SDG.

The prototype preserves the source evidence used by the model, validates the technical structure of each proposal, and separates machine-generated results from subsequent human assessment.

## Current deployed snapshot

The public Streamlit application currently exposes a fixed pilot snapshot containing:

- **20 CORDIS projects**
- **20 projects processed successfully**
- **0 model abstentions**
- **14 projects with technically valid proposals**
- **6 projects with rejected proposals pending review**

A technically valid proposal means that its SDG URI, output schema and quoted source span passed automated checks.

It **does not** mean that the proposed SDG contribution has been confirmed.

The deployed results are static. No live model inference is performed by the Streamlit application.

A separate **60-project holdout evaluation** is being processed independently and is not included in the deployed pilot snapshot. Holdout results will not be incorporated into the public dataset merely because model inference has completed; they remain subject to validation and review.

## Public application

The interactive prototype is available at:

**https://cordis-sdg-prototype.streamlit.app/**

The application allows users to:

- inspect the overall run status;
- explore the distribution of proposed SDGs;
- filter projects by technical state, confidence and proposed SDG;
- inspect individual CORDIS projects;
- view the proposed SDG target and its ancestor goal;
- examine the model rationale and stated uncertainty;
- inspect the exact CORDIS source text used as evidence.

## Method

The prototype follows an evidence-first workflow:

1. **CORDIS source snapshot**  
   Project objectives are extracted unchanged from a pinned CORDIS data snapshot.

2. **Local model inference**  
   A locally hosted language model proposes SDG mappings from the project evidence.

3. **Structured output**  
   Proposals must conform to a defined schema.

4. **Deterministic validation**  
   The pipeline checks, among other things:
   - SDG URI validity;
   - schema compliance;
   - presence and correspondence of quoted source evidence.

5. **Technical state assignment**  
   Proposals are separated into states such as:
   - `validated_proposals_pending_review`
   - `rejected_proposals_pending_review`

6. **Human review**  
   Technical validation is not treated as substantive confirmation. Final interpretation requires human assessment.

## Evidence and provenance

The application is designed so that a proposed SDG mapping can be traced back to the project text from which it was inferred.

For each proposal, the interface can expose:

- CORDIS project identifier and title;
- programme information;
- proposed SDG target URI;
- ancestor SDG goal;
- qualitative model confidence;
- proposed contribution;
- model rationale;
- uncertainty statement;
- original project objective text.

This provenance is intended to make the mapping inspectable rather than presenting an opaque classification result.

## Data integrity

The hosted project objectives are unchanged extracts from the pinned CORDIS snapshot used during preparation of the deployment dataset.

The deployment verifies the checksum of the exported project subset. The checksum of the complete source ZIP was verified during the export process.

The public application uses a static database snapshot rather than querying or modifying the source CORDIS dataset at runtime.

## Repository contents

The deployment package contains the application and the data required to reproduce the public pilot interface, including:

- `app.py` — Streamlit application;
- `requirements.txt` — Python dependencies;
- `cordis_sdg_pilot.db` — static pilot database;
- `project_subset.json` — exported CORDIS project subset;
- `sdg_full.rdf` — SDG vocabulary used by the prototype;
- `review_sample.csv` — review-oriented export;
- validation and analytical support modules;
- deployment metadata and manifest files.

## Important limitations

This is a **prototype**, not an authoritative SDG classification system.

In particular:

- model proposals may be incorrect, overly broad or based on insufficient evidence;
- technical validation only establishes structural and provenance-related validity;
- a technically valid proposal is not equivalent to a verified SDG contribution;
- the current public dataset is a small pilot sample and should not be interpreted as representative of all CORDIS projects;
- model confidence labels are not calibrated probabilities;
- substantive conclusions require human review.

## Current development stage

The project currently has two distinct evaluation stages:

**Pilot deployment**

A fixed 20-project snapshot is publicly available through Streamlit and serves as the inspectable prototype.

**Holdout evaluation**

A separate 60-project cohort is being evaluated locally. It is kept outside the deployed pilot dataset during inference and validation in order to preserve the distinction between the initial pilot and subsequent evaluation.

## Purpose

The prototype explores a reproducible and auditable approach to mapping research-project evidence to the SDGs while retaining:

- source provenance;
- explicit uncertainty;
- deterministic technical validation;
- separation between model proposals and human judgement;
- reproducible deployment artifacts.

## Status

**Public prototype:** operational  
**Pilot snapshot:** 20 projects  
**Holdout evaluation:** in progress  
**Human review:** required for all model proposals

---

CORDIS project data remain subject to the terms and conditions applicable to the original European Commission data sources. SDG terminology and identifiers refer to the United Nations Sustainable Development Goals framework.
