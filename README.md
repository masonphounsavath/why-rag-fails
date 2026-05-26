# Why RAG Fails

A RAG (Retrieval-Augmented Generation) system built from primitives over SEC 10-K filings — with rigorous, reproducible analysis of where and why it breaks.

## The Point

Most RAG tutorials show you how to build one. This project shows you how to break one — systematically.

The pipeline is built without frameworks (no LangChain, no LlamaIndex) so every component is legible and measurable. The core work is a documented failure analysis across five failure modes: chunking boundaries, retrieval precision/recall, hallucination on missing context, multi-document reasoning, and numerical reasoning.

**Key findings:** _(populated as experiments run)_

## Project Structure

```
src/
  ingestion/    # SEC EDGAR downloader, PDF parser
  chunking/     # Three chunking strategies: fixed, sentence-aware, section-aware
  embedding/    # sentence-transformers, embedding cache
  retrieval/    # FAISS index, top-k search
  generation/   # Claude API, prompt construction
  eval/         # Eval harness, metrics (precision@k, recall@k, faithfulness)

evals/
  qa_dataset.json   # 100 hand-labeled QA pairs (answerable + unanswerable)
  results/          # JSON output from each eval run

notebooks/
  01_corpus_eda.ipynb
  02_chunking_comparison.ipynb
  03_retrieval_eval.ipynb
  04_failure_modes.ipynb

docs/
  findings.md   # Written analysis of failure modes and improvements
```

## Corpus

SEC 10-K annual filings (2021-2023) for 8 companies: Apple, Microsoft, Nvidia, Google, JPMorgan, Goldman Sachs, Meta, Amazon. Downloaded from the public SEC EDGAR API — no scraping, no paywalls.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# add your ANTHROPIC_API_KEY to .env

python scripts/download_corpus.py
python scripts/build_index.py
python scripts/run_evals.py
```

## Failure Modes Studied

| Failure Mode | Description | Metric |
|---|---|---|
| Chunking boundaries | Meaning lost at chunk splits, tables broken | Manual coherence scoring |
| Retrieval precision/recall | Wrong or missing chunks | Precision@k, Recall@k |
| Missing context hallucination | Model answers unanswerable questions | Hallucination rate |
| Multi-document reasoning | Synthesis across companies/years | Answer accuracy |
| Numerical reasoning | Arithmetic over retrieved numbers | Exact match accuracy |

Full analysis in [docs/findings.md](docs/findings.md).
