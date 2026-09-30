# CORDIS → SDGs evidence explorer

Read-only prototype for inspecting model proposals and verbatim project evidence.

## Run

`python -m pip install -r requirements.txt`

`python -m streamlit run app.py`

Deploy on Streamlit Community Cloud with `app.py` as the entry point and Python 3.12.
No API key or local Ollama server is required to browse the recorded results.

## Interpretation and provenance

Technical validation does not certify semantic correctness. Confidence labels
are model declarations. Model abstentions and rejected evidence are distinct.
The database is a static snapshot and may contain an incomplete pilot or holdout.
The interface explicitly reports the denominator and incomplete execution.

The 80 project records were extracted unchanged from the pinned CORDIS ZIP,
whose checksum was verified at export. This deployment verifies the extracted
JSON checksum and the pinned taxonomy checksum, not the complete ZIP at runtime.
Source hashes and extraction information are in the manifests.

The local model adapter was introduced after AI-assisted human holdout review;
results must not be described as a fully independent untouched benchmark.
Human reference annotations are not included in this deployment package.

Code and documentation authorship: João Carlos Monteiro Simas, with AI assistance.
Third-party source data and libraries retain their applicable terms. No licence
for this project code has been selected yet.
