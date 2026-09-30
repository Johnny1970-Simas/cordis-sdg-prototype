# CORDIS → SDGs Prototype

Evidence-based mapping of CORDIS research projects to the United Nations Sustainable Development Goals (SDGs), using local language-model inference, deterministic technical validation and human review.

**Live prototype:** https://cordis-sdg-prototype.streamlit.app/

## Overview

This repository contains a research prototype for exploring whether evidence contained in CORDIS project objectives can support proposed mappings to specific Sustainable Development Goal concepts.

The system follows a deliberately conservative principle:

> Model-generated mappings are proposals for human review, not confirmed statements that a project contributes to an SDG.

The prototype preserves the source evidence used by the model, validates the technical structure of each proposal, and separates machine-generated results from subsequent human assessment.

## Evaluation design

The evaluation uses a deterministic stratified sample of **80 CORDIS projects** drawn from a pinned Horizon Europe corpus containing **23,613 project records**.

The sample is divided into two disjoint cohorts:

- **20 pilot projects**
- **60 holdout projects**

The pilot and holdout contain no overlapping project IDs.

The public Streamlit application currently exposes the fixed **20-project pilot snapshot**. The holdout was evaluated separately and is not automatically incorporated into the deployed application.

## Pilot results

The deployed pilot contains:

- **20 / 20 projects processed successfully**
- **14 projects with technically valid proposals pending review**
- **6 projects with rejected proposals pending review**
- **0 model abstentions**
- **20 unique project IDs**
- **20 proposal records**

A technically valid proposal means that its SDG URI, schema and quoted evidence passed automated checks.

It does **not** mean that the proposed SDG contribution has been confirmed.

## Holdout results

The separate 60-project holdout evaluation has been completed.

Final technical states:

- **50 projects** — `validated_proposals_pending_review`
- **10 projects** — `rejected_proposals_pending_review`
- **0 projects** — `model_error_retryable`
- **0 unexpected states**

Final integrity checks confirmed:

- all **60 expected holdout projects** are present;
- all **60 project IDs are unique**;
- no expected projects are missing;
- no unexpected projects are present;
- there is **no overlap with the pilot cohort**;
- there are no orphan project records;
- there are no orphan proposal records.

These results describe technical validation status only. They are not human-confirmed SDG mappings or ground truth.

## Public application

The interactive prototype is available at:

**https://cordis-sdg-prototype.streamlit.app/**

The application allows users to:

- inspect run status;
- explore proposed SDGs;
- filter projects by technical state, confidence and proposed SDG;
- inspect individual CORDIS projects;
- view proposed SDG concepts and ancestor goals;
- examine model rationale and uncertainty;
- inspect the exact CORDIS source text used as evidence.

The public application uses a static snapshot and performs no live model inference.

## Method

The prototype follows an evidence-first workflow.

### 1. CORDIS source snapshot

Project objectives are extracted unchanged from a pinned CORDIS Horizon projects snapshot.

### 2. SDG taxonomy

The system uses the official SDG vocabulary exposed through EU Vocabularies.

A complete local taxonomy snapshot was materialised by dereferencing the official SDG concept URIs and merging the resulting RDF data.

The taxonomy contains:

- **812 concepts**
- **17 top-level SDG goals**
- **816 parent relationships**
- **18 multi-parent concepts**

### 3. Local model inference

Inference is performed locally using:

`qwen2.5:3b-instruct-q4_K_M`

through Ollama with deterministic generation settings.

The workflow uses two passes:

- **Goal pass** — evaluates the project objective against the 17 top-level SDG goals.
- **Target pass** — expands technically valid goal proposals to more specific SDG concepts.

If goal evidence fails technical validation, the raw proposal is preserved for review and no target expansion is performed.

### 4. Structured output

Each proposal must contain:

- an allowed SDG concept URI;
- a verbatim evidence excerpt;
- a contribution mechanism;
- a rationale;
- qualitative confidence;
- an uncertainty statement.

### 5. Deterministic technical validation

The pipeline checks:

- schema compliance;
- SDG URI validity;
- candidate-set membership;
- verbatim correspondence between the evidence excerpt and the original CORDIS objective;
- technical proposal structure.

### 6. Human review

Technical validation is not substantive confirmation.

All model outputs remain pending human review.

## Technical states

The main project states are:

- `validated_proposals_pending_review` — at least one proposal passed technical validation and awaits human review;
- `rejected_proposals_pending_review` — generated proposals failed technical validation but are preserved for audit and review;
- `model_abstained_pending_review` — the model explicitly returned no justified proposal;
- `model_error_retryable` — inference failed because of a recoverable technical error such as a timeout.

## Mapping outputs

The repository distinguishes two different resources:

### Model mapping table

`model_mapping_table.csv
`holdout_evaluation_metrics.csv`

Contains the final model output for all **80 projects**:

- 20 pilot;
- 60 holdout;
- 64 technically validated proposals;
- 16 technically rejected proposals.

Each row preserves the proposed SDG concept, confidence, contribution mechanism, rationale, uncertainty and verbatim source evidence.

All mappings remain pending human review.

### Human validation reference

`mapping_table.csv`

Contains single-human-reviewer, AI-assisted reference annotations for the 60-project holdout.

These annotations are used for validation and error analysis and must not be interpreted as model predictions.

## Evidence and provenance

The application is designed so that every proposed mapping can be traced back to the project text from which it was inferred.

The workflow records hashes for the principal artefacts used by each run, including:

- source CORDIS corpus;
- SDG taxonomy;
- system prompt;
- retrieval/method fingerprint;
- exported project subset;
- deployed SQLite database.

The deployed taxonomy and pilot database have been independently recomputed and confirmed to match the hashes recorded in their manifests.

## Repository resources

Key evaluation and provenance resources include:

- `review_sample.csv` — pilot/holdout sample definition;
- `SAMPLE_MANIFEST.json` — sampling method, seed, strata and limitations;
- `SOURCE_MANIFEST.json` — pinned CORDIS source corpus and SDG taxonomy provenance;
- `DEPLOYMENT_MANIFEST.json` — deployment provenance and artefact hashes;
- `model_mapping_table.csv` — final 80-project model mapping output;
- `mapping_table.csv` — human validation reference;
- `cordis_sdg_pilot.db` — static pilot database used by the public application;
- `project_subset.json` — exported 80-project subset;
- `sdg_full.rdf` — pinned SDG taxonomy snapshot.

## Data integrity

The pilot database has been checked for internal consistency:

- no project records without proposals;
- no orphan proposal records;
- all pilot projects and proposals belong to the same recorded run;
- the deployed database matches its recorded SHA-256 hash.

The holdout database has also passed final cohort and relational-integrity checks.

## Limitations

This is a **prototype**, not an authoritative SDG classification system.

In particular:

- model proposals may be incorrect, overly broad or based on insufficient evidence;
- technical validation establishes structural and provenance-related validity, not substantive correctness;
- pilot and holdout samples are small and must not be interpreted as representative estimates for the complete CORDIS population;
- the stratified sampling design supports error discovery and programme-part coverage rather than unbiased corpus-wide prevalence estimates;
- qualitative confidence labels are not calibrated probabilities;
- human review remains necessary for substantive interpretation.

The local model adapter was introduced after AI-assisted human holdout review. Consequently, the holdout must not be described as a fully independent untouched benchmark. This chronology is explicitly recorded in the run metadata.

## Design objective

The objective is not to maximise the number of SDG assignments.

The system is designed to provide a reproducible and reviewable mapping process in which proposed links remain traceable to the original evidence, technical failures remain visible, uncertainty is preserved and human judgement remains the final authority.

## Status

**Public prototype:** operational  
**Pilot:** completed — 20/20 projects  
**Holdout:** completed — 60/60 projects  
**Model mapping table:** 80 projects  
**Human review:** required for all model proposals
