# MediSure AI

The interface starts with Upload, then Verify, then Understand. API keys and model selection are configured by the team outside the interface. Connection testing controls and sample-download controls have been removed. The working Gemini REST processing flow is unchanged.

## Before replacing your working app

Copy the EXACT model ID that passed the connection test in the previous version. Keep that same API key. Do not guess a different model or change to an alias.

## Configure once

Create `.env` beside `app.py` (not `.env.example`) and save:

```dotenv
GEMINI_API_KEY=your_actual_working_key
GEMINI_MODEL=the_exact_model_id_that_worked
```

These are placeholders: replace both values. Never commit `.env`. The included `.gitignore` excludes it. Existing environment variables take priority over `.env`; keep their values consistent if you previously configured them.

Stop the old app using Ctrl+C, then run from the folder containing app.py:

```bash
python -m pip install -r requirement.txt
python -m streamlit run app.py
```

For the existing Codespace folder:

```bash
cd /workspaces/GT_MEDISURE-AI/MediSure-AI-Fresh
```

The key is used only by the Python backend when a report is processed. Visitors upload, acknowledge Gemini processing, verify and confirm results, then view explanations and download PDF/CSV. No connection check is shown or required per visit.

For Streamlit Cloud, set GEMINI_API_KEY and GEMINI_MODEL in app secrets using quoted TOML strings. Do not upload `.env` to GitHub.

Five modules remain: app.py, extractor.py, document_classifier.py, comparison.py, explainer.py; styling is in styles.css. Samples remain in the samples folder for team testing, but are not displayed in the user interface.

The existing numerical verification and comparison limits still apply: numeric results only, no guessed ranges or unit conversion, missing/incompatible ranges marked Unavailable. No database; report content is sent to Google for processing. Educational only.

Automated checks cover the mocked upload/verify/results flow, absence of connection controls, diagnostic redaction and PDF generation. Live account access was not independently verified here; use the exact key/model combination you already tested successfully.

## Professional interface update

The design update uses `styles.css` and a small amount of presentation markup in `app.py` (intro, progress indicator, and section labeling). `app.py` retains the original upload/verification/results actions, Gemini integration, and session-state transitions. `explainer.py` retains its Gemini and CSV logic, with only the `pdf_report()` presentation implementation updated for a polished, multipage PDF with a summary, range comparisons, color-coded result headings, doctor questions, and page numbers. The output PDF is still educational only.

The project deliberately does not include a `.env` file. Preserve your existing working API key and model settings; do not commit them. To launch, install `requirements.txt` and run `python -m streamlit run app.py`. Streamlit layout/CSS can vary slightly across Streamlit versions.
