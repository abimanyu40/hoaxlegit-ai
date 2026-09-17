# Dokumentasi Teknis — Cek Hoax

Referensi lengkap semua file dan fungsi di project. Kode sumber lengkap ada di file masing-masing (`chat.py`, `app.py`, `core/*.py`).

---

## `chat.py` — Entry point terminal

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `check_and_report(message, source_input, use_cache)` | pesan, tipe sumber ("text"/"image"/"batch"), pakai cache atau tidak | `str` (verdict) | Cek cache dulu via `find_cached()`, kalau kosong panggil `check_message()`, simpan hasil ke DB |
| `mode_text_check()` | - | - | Input pesan dari `input()`, panggil `check_and_report()` |
| `mode_image_check()` | - | - | Minta path gambar, OCR via `extract_text_from_image()`, lanjut cek |
| `mode_batch_check()` | - | - | Baca file `.txt`/`.csv`, loop tiap baris, tulis rekap ke `<nama>_hasil.csv` |
| `mode_history()` | - | - | Ambil riwayat dari `get_history()`, print terformat |
| `main()` | - | - | Loop menu utama, dispatch ke fungsi mode di atas |

---

## `app.py` — Entry point GUI (Streamlit)

Sama fungsinya kayak `chat.py`, bedanya I/O pakai widget Streamlit (`st.text_area`, `st.file_uploader`, `st.button`, dst) bukan `input()`/`print()`. 4 tab: Cek Teks, Cek Gambar, Batch Check, Riwayat. Logic inti (`check_message`, `save_check`, dll) dipanggil sama persis dari `core/`.

`run_check(message, source_input)` — versi Streamlit dari `check_and_report()`, pakai `st.spinner()` buat loading indicator dan `st.markdown()` buat nampilin hasil.

---

## `core/ollama_client.py` — Orkestrasi LLM

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `_call_ollama(messages, use_tools)` | list messages, boleh pakai tools atau tidak | `dict` (JSON response Ollama) | POST request mentah ke `/api/chat` |
| `_build_kb_context(user_message)` | pesan user | `str` | Panggil `knowledge_base.search()`, format hasilnya jadi teks konteks tambahan. Return string kosong kalau KB gagal/gak ada match |
| `check_message(user_message, max_tool_rounds)` | pesan user, max iterasi tool call | `(str, list)` — (jawaban final, list query yang di-search) | Fungsi utama: susun messages (system + KB context + user), loop panggil Ollama, kalau ada `tool_calls` jalanin `run_tool()` dan lanjut loop, kalau gak ada return jawaban final |

Konstanta: `MODEL = "qwen2.5:7b"` (model chat), diimport dari `core.tools` dan `core.knowledge_base`.

---

## `core/tools.py` — Web search & cross-check

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `_search_raw(query, max_results)` | keyword, jumlah hasil | `list[dict]` | Wrapper `duckduckgo_search.DDGS().text()`, return list kosong kalau error |
| `cross_check_search(claim)` | klaim yang mau dicek | `str` | Search klaim langsung + search "fakta/hoax/bantahan {klaim}", gabung & dedupe by URL, tag tiap hasil pakai `score_source()` |
| `run_tool(name, arguments)` | nama tool, argumen dari LLM | `str` | Dispatcher — saat ini cuma handle `"web_search"` |

`TOOLS_SCHEMA` — JSON schema yang dikirim ke Ollama biar LLM tahu tool apa aja yang available dan formatnya gimana (standar OpenAI-style function calling).

---

## `core/credibility.py` — Skor kredibilitas sumber

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `score_source(url)` | URL sumber | `dict` `{domain, score, tier}` | Extract domain dari URL, cocokkan ke `CREDIBILITY_TIERS`, kalau gak ketemu pakai `DEFAULT_SCORE` |
| `_label(score)` | angka skor | `str` | Konversi skor jadi label ("Sangat kredibel" / "Cukup kredibel" / "Tidak dikenal") |

`CREDIBILITY_TIERS` — dictionary domain → skor (0.0–1.0), manual, bisa ditambah sendiri.

---

## `core/knowledge_base.py` — RAG hoax lama

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `_get_embedding(text)` | teks | `list[float]` | Panggil `/api/embeddings` Ollama (model `nomic-embed-text`), dapet vector |
| `_cosine_similarity(a, b)` | dua vector | `float` | Hitung kemiripan arah dua vector (dot product / perkalian norma) |
| `build_index(force)` | paksa rebuild atau tidak | - | Embed semua entri `known_hoaxes.json`, simpan ke cache `known_hoaxes_embeddings.json`. Skip kalau cache udah ada (kecuali `force=True`) |
| `search(query, top_k, min_similarity)` | klaim baru, jumlah hasil maks, ambang kemiripan | `list[dict]` | Embed query, bandingkan ke semua entri cache, filter & sort by similarity |

---

## `core/database.py` — Riwayat & cache (SQLite)

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `init_db()` | - | - | Bikin file `data/history.db` + tabel `checks` kalau belum ada |
| `save_check(message, verdict, sources, source_input)` | pesan, hasil, list query search, tipe sumber | - | Insert row baru ke tabel `checks` |
| `get_history(limit)` | jumlah maks | `list[dict]` | Ambil N entri terakhir, urut terbaru dulu |
| `find_cached(message)` | pesan | `dict` atau `None` | Cari exact match pesan yang sama persis, buat cache |

Skema tabel `checks`: `id, timestamp, message, verdict, sources (JSON string), source_input`.

---

## `core/ocr.py` — Extract teks dari gambar

| Fungsi | Parameter | Return | Fungsinya |
|---|---|---|---|
| `extract_text_from_image(image_path, lang)` | path gambar, kode bahasa Tesseract | `str` | Buka gambar via PIL, jalankan `pytesseract.image_to_string()`. Raise error jelas kalau Tesseract belum terinstall |

---

## `core/prompts.py`

Cuma satu konstanta: `SYSTEM_PROMPT` — instruksi lengkap ke LLM soal cara analisis (ekstrak klaim, cek KB, search kalau perlu, prioritaskan sumber kredibel, format jawaban).

---

## Alur data lengkap (satu kali cek)

```
User input (teks/gambar)
    │
    ▼
[OCR kalau gambar] → teks
    │
    ▼
find_cached() ── ada? ──▶ tampilkan hasil lama, SELESAI
    │ (tidak ada)
    ▼
_build_kb_context() ── embed pesan, cari mirip di known_hoaxes.json
    │
    ▼
check_message()
    │
    ▼
messages = [system_prompt, kb_context?, user_message]
    │
    ▼
┌─────────────── loop (maks 3x) ───────────────┐
│ _call_ollama(messages)                       │
│    │                                         │
│    ├─ ada tool_calls? ──▶ run_tool()         │
│    │                       └─ cross_check_search()
│    │                            └─ score_source() tiap hasil
│    │                       └─ hasil di-append ke messages
│    │                       └─ ULANG LOOP
│    │                                         │
│    └─ tidak ada tool_calls ──▶ jawaban final │
└───────────────────────────────────────────────┘
    │
    ▼
save_check() → simpan ke SQLite
    │
    ▼
Tampilkan ke user (terminal/GUI)
```
