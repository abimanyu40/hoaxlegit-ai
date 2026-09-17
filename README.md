# Cek Hoax v2 — LLM Hoax Checker (Full Feature Version)

A terminal/GUI program that helps identify hoax/misinformation patterns in viral messages, using a local LLM (Ollama).

## Features

- Text message check (internet search + claim vs. rebuttal cross-check)
- Image/screenshot OCR (extract text from message screenshots)
- Source credibility scoring (distinguish credible sources from unknown ones)
- Local knowledge base (RAG) — similar claims to past hoaxes are recognized instantly without re-searching
- History/database (SQLite) — every check result is stored, with caching if the same message was checked before
- Batch mode — check many messages at once from a .txt/.csv file, output a summary CSV

## Setup (WSL Ubuntu)

```bash
# 0. If WSL isn't installed yet (run in Windows PowerShell)
wsl --install -d Ubuntu

# 1. Update the system + install Ollama (run inside WSL Ubuntu)
sudo apt update && sudo apt upgrade -y
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the chat model + embedding model
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 3. Install Tesseract OCR + Indonesian language pack
sudo apt install tesseract-ocr tesseract-ocr-ind

# 4. Set up the Python environment
sudo apt install python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Note: make sure your NVIDIA driver on Windows supports WSL (download it from NVIDIA's site), then check that the GPU is detected inside WSL with `nvidia-smi`. Streamlit running in WSL is automatically accessible from your Windows browser at `localhost:8501` with no extra config.

## Running it

Terminal version:
```bash
python chat.py
```
A menu will appear: text check, image check, batch check, or view history.

GUI version (Streamlit):
```bash
streamlit run app.py
```
Opens automatically in your browser (`localhost:8501`). Has 4 tabs: Text Check, Image Check, Batch Check, History.

## Structure

```
hoax-checker/
├── chat.py                    # terminal entry point
├── app.py                     # GUI entry point (Streamlit)
├── core/
│   ├── ollama_client.py       # chat + tool-calling + KB context
│   ├── prompts.py             # system prompt
│   ├── tools.py                # web_search + cross-check + credibility tagging
│   ├── credibility.py         # source scoring (domain -> credibility score)
│   ├── knowledge_base.py      # RAG: embedding + similarity search over past hoaxes
│   ├── database.py            # SQLite history + cache
│   └── ocr.py                 # extract text from images
├── data/
│   └── known_hoaxes.json      # database of previously verified hoaxes (fill in manually)
├── requirements.txt
└── .gitignore
```

## Populating the hoax knowledge base (RAG)

`data/known_hoaxes.json` currently only has placeholders. Replace them with real, verified hoax claims — for example from turnbackhoax.id or cekfakta.com's archives, using this format:

```json
[
  {
    "claim": "a commonly viral claim",
    "verdict": "Hoax / Fact / Needs verification",
    "explanation": "brief explanation of why"
  }
]
```

After editing, delete `data/known_hoaxes_embeddings.json` (if it exists) so the embeddings get recomputed automatically on the next run.

## Notes

- The embedding model (`nomic-embed-text`) must be pulled for the RAG feature to work. If it's missing, this feature is skipped automatically (won't crash the program).
- Domain credibility scores live in `core/credibility.py` — add more relevant domains yourself.
- Next step: swap the terminal I/O for a GUI (Streamlit/Gradio) without changing `core/`.
