# CORDIS → SDGs: Evidence-Based Mapping with Human Review

## Submission

**Competition:** Mapping CORDIS projects to SDGs  
**Platform:** data.europa.eu  
**Notebook:** *CORDIS - SDGs: Evidence-Based Mapping with Human Review*  
**Status:** Successfully submitted on 30 September 2026  
**Public prototype:** https://cordis-sdg-prototype.streamlit.app/  
**Repository:** https://github.com/Johnny1970-Simas/cordis-sdg-prototype

## Objective

The project develops a transparent and auditable method for proposing links between CORDIS research projects and the United Nations Sustainable Development Goals (SDGs).

The core principle is that model-generated mappings are treated as **proposals for human review**, not as confirmed classifications.

The workflow preserves the original project evidence, applies deterministic technical validation and maintains a clear distinction between machine output and human assessment.

## Data and evaluation design

The source corpus is a pinned Horizon Europe CORDIS snapshot containing **23,613 project records**.

A deterministic stratified sample of **80 projects** was created:

- **20 pilot projects**
- **60 disjoint holdout projects**

The public Streamlit prototype exposes the fixed 20-project pilot snapshot. The 60-project holdout was evaluated separately.

The SDG taxonomy is based on the official EU Vocabularies SDG scheme and contains:

- **812 concepts**
- **17 top-level SDG goals**
- **816 parent relationships**
- **18 multi-parent concepts**

## Method

Inference is performed locally using **qwen2.5:3b-instruct-q4_K_M** through Ollama with deterministic generation settings.

The process uses two stages:

1. **Goal pass** — comparison with the 17 top-level SDGs.
2. **Target pass** — expansion of technically valid goal proposals to more specific SDG concepts.

Each proposal includes:

- SDG concept URI
- verbatim source evidence
- contribution mechanism
- rationale
- qualitative confidence
- uncertainty statement

Deterministic validation checks schema compliance, URI validity, candidate-set membership, proposal structure and correspondence between quoted evidence and the original CORDIS objective.

## Results

### Pilot

- **20/20 projects processed**
- **14 technically validated proposals**
- **6 technically rejected proposals**
- **0 abstentions**

### Holdout

- **60/60 expected projects processed**
- **50 technically validated proposals**
- **10 technically rejected proposals**
- **0 retryable model errors**
- no pilot overlap
- no missing or unexpected projects
- no orphan records

Across all 80 projects, the final model mapping table contains:

- **64 technically validated proposals**
- **16 technically rejected proposals**

Technical validation does not establish substantive SDG correctness.

## Human-reference comparison

The 60-project holdout was compared with a **single-human-reviewer, AI-assisted reference**.

Observed agreement:

- **4/60 (6.7%)** exact concept matches
- **8/60 (13.3%)** same top-level SDG, different concept
- **12/60 (20.0%)** agreement at least at SDG level
- **43/60 (71.7%)** different goal or concept
- **5/60 (8.3%)** model mapping where the reference indicated no justified mapping

Among technically validated projects, same-SDG-or-exact agreement was **9/50 (18.0%)**. Among technically rejected projects it was **3/10 (30.0%)**.

These figures are treated as **agreement measures, not accuracy estimates**.

## Diagnostic findings

The analysis identified possible **concept-attractor behaviour**, with repeated model selection of concepts such as SDG 13.3, 16.7, 8.7, 17.16 and 17.13.

The model was not globally more concentrated than the human reference, but the shape of the distributions differed. The five most frequent model concepts represented **58.3%** of assignments, compared with **51.5%** for the human reference.

This is interpreted as diagnostic evidence of possible selection imbalance, not proof of model bias.

## Main limitations

- small pilot and holdout samples
- stratified sampling designed for error discovery rather than population prevalence estimation
- qualitative confidence scores are not calibrated probabilities
- technical validity does not imply semantic correctness
- the human reference is based on a single reviewer with AI assistance
- the local model adapter was introduced after the AI-assisted human holdout review, so the holdout is not a fully independent untouched benchmark
- all model-generated mappings still require human review

## Published artefacts

The final submission includes:

- `review_sample.csv`
- `SAMPLE_MANIFEST.json`
- `SOURCE_MANIFEST.json`
- `DEPLOYMENT_MANIFEST.json`
- `mapping_table.csv`
- `model_mapping_table.csv`
- `holdout_evaluation_metrics.csv`
- public Streamlit prototype
- GitHub repository and README
- competition Abstract and Solution documentation

## Design principle

The project does not aim to maximise the number of SDG assignments.

Its objective is to provide a **reproducible, inspectable and reviewable mapping process** in which every proposed link remains traceable to source evidence, technical failures remain visible, uncertainty is preserved and human judgement remains the final authority.
