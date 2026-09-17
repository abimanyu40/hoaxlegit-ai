# Cek Hoax v2 — LLM Hoax Checker (dengan fitur lengkap)

Program terminal yang bantu identifikasi ciri-ciri hoax/misinformasi di pesan viral, pakai LLM lokal (Ollama).

## Fitur

- Cek pesan teks (search internet + cross-check klaim vs bantahan)
- OCR gambar/screenshot (extract teks dari gambar pesan)
- Source credibility scoring (bedain sumber kredibel vs tidak dikenal)
- Local knowledge base (RAG) — klaim yang mirip dengan hoax lama langsung dikenali tanpa search ulang
- Riwayat/database (SQLite) — semua hasil cek tersimpan, ada caching kalau pesan yang sama pernah dicek
- Batch mode — cek banyak pesan sekaligus dari file .txt/.csv, output rekap CSV

## Setup (WSL Ubuntu)

```bash
# 0. Kalau WSL belum ada (dijalankan di PowerShell Windows)
wsl --install -d Ubuntu

# 1. Update sistem + install Ollama (dijalankan di dalam WSL Ubuntu)
sudo apt update && sudo apt upgrade -y
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model chat + model embedding
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 3. Install Tesseract OCR + paket bahasa Indonesia
sudo apt install tesseract-ocr tesseract-ocr-ind

# 4. Setup Python env
sudo apt install python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Catatan: pastikan driver NVIDIA di Windows sudah versi yang support WSL (download dari situs NVIDIA), lalu cek GPU kedetect di dalam WSL dengan `nvidia-smi`. Streamlit yang jalan di WSL otomatis bisa diakses dari browser Windows di `localhost:8501` tanpa config tambahan.

## Jalanin

Versi terminal:
```bash
python chat.py
```
Nanti muncul menu: cek teks, cek gambar, batch check, atau lihat riwayat.

Versi GUI (Streamlit):
```bash
streamlit run app.py
```
Otomatis buka di browser (`localhost:8501`). Ada 4 tab: Cek Teks, Cek Gambar, Batch Check, Riwayat.

## Struktur

```
hoax-checker/
├── chat.py                    # entry point terminal
├── app.py                     # entry point GUI (Streamlit)
├── core/
│   ├── ollama_client.py       # chat + tool-calling + KB context
│   ├── prompts.py             # system prompt
│   ├── tools.py                # web_search + cross-check + credibility tagging
│   ├── credibility.py         # scoring sumber (domain -> skor kredibilitas)
│   ├── knowledge_base.py      # RAG: embedding + similarity search hoax lama
│   ├── database.py            # SQLite riwayat + cache
│   └── ocr.py                 # extract teks dari gambar
├── data/
│   └── known_hoaxes.json      # database hoax yang sudah diverifikasi (isi manual)
├── requirements.txt
└── .gitignore
```

## Isi database hoax lama (RAG)

`data/known_hoaxes.json` masih berisi placeholder. Ganti dengan klaim hoax nyata yang sudah diverifikasi, misalnya dari arsip turnbackhoax.id atau cekfakta.com, formatnya:

```json
[
  {
    "claim": "klaim yang biasa viral",
    "verdict": "Hoax / Fakta / Perlu verifikasi",
    "explanation": "penjelasan singkat kenapa"
  }
]
```

Setelah diedit, hapus `data/known_hoaxes_embeddings.json` (kalau ada) biar embedding dihitung ulang otomatis pas run berikutnya.

## Catatan

- Model embedding (`nomic-embed-text`) wajib di-pull biar fitur RAG jalan. Kalau belum ada, fitur ini otomatis di-skip (gak bikin program crash).
- Skor kredibilitas domain ada di `core/credibility.py` — tambahin sendiri domain lain yang relevan.
- Rencana selanjutnya: ganti terminal I/O ke GUI (Streamlit/Gradio) tanpa ubah `core/`.
