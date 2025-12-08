# AI Usage Insights – BankWide AI Project Tracker Demo

A Streamlit app for importing AI use-cases from Excel, browsing the catalogue, and getting platform recommendations for leaders.

## Setup
- Python 3.11+ recommended. Create/activate a virtualenv (or conda env) and be sure to run Streamlit with the SAME interpreter you install deps with.
- Install dependencies: `python -m pip install -r requirements.txt` (or `python3`/`pip3` depending on your setup). This installs `chromadb`, `streamlit`, and other required libs.
- Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`. Adjust `CHROMA_PATH` if you want to store embeddings elsewhere.
- FinOps decision weights/heuristics live in `finops_config.json`; edit this file to tune how answers/recommendations prioritise financial benefit, cost efficiency, production readiness, governance/risk, and user adoption.

## Code layout
- `admin/` – shared admin helpers (vector DB access, ingest counters).
- `admin_components/` – Streamlit tabs for dashboard, manual add, and bulk import.
- `finops/` – config, deterministic metrics, and reusable FinOps query helpers.
- `ingestion/` – Excel ingest pipeline.
- `llm/` – LLM client wrapper and prompts.
- `platform_logic/` – platform recommendation logic (renamed to avoid stdlib `platform` clash).
- `storage/` – Chroma vector DB wrapper.
- `config/` – central LLM/storage settings (OpenAI/Ollama + Chroma paths).
- `app_ui.py` – Streamlit UI wiring and page orchestration.
- `data/` – Excel source file for catalogue ingest.

## Run
- `streamlit run app.py`
- Use the sidebar to refresh data via **Bulk Import** before exploring the dashboard or **Leader Insights**.
- To purge/reset the vector DB before a fresh ingest: `python purge_vector_db.py`.

## Troubleshooting
- `ModuleNotFoundError: No module named 'pydantic'`: ensure the virtualenv is active and rerun `pip install -r requirements.txt`.
- Vector DB errors: check `OPENAI_API_KEY` is set and that you have write access to `CHROMA_PATH`.
