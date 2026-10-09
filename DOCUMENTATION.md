# Technical Documentation — Hoax Checker

Full reference of every file and function in the project. The complete source is in each file (`chat.py`, `app.py`, `core/*.py`).

---

## `chat.py` — Terminal entry point

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `check_and_report(message, source_input, use_cache)` | message, input type ("text"/"image"/"batch"), whether to use the cache | `str` (verdict) | Checks the cache via `find_cached()`, otherwise calls `check_message()` and saves the result to the DB |
| `mode_text_check()` | - | - | Reads a message via `input()` and calls `check_and_report()` |
| `mode_image_check()` | - | - | Asks for an image path, OCRs it via `extract_text_from_image()`, then checks the text |
| `mode_batch_check()` | - | - | Reads a `.txt`/`.csv` file, loops over each message, writes a summary to `<name>_results.csv` |
| `mode_history()` | - | - | Fetches history via `get_history()` and prints it |
| `main()` | - | - | Main menu loop, dispatches to the mode functions above |

---

## `app.py` — GUI entry point (Streamlit)

Same functionality as `chat.py`, but I/O uses Streamlit widgets (`st.text_area`, `st.file_uploader`, `st.button`, ...) instead of `input()`/`print()`. Four tabs: Text Check, Image Check, Batch Check, History. The core logic (`check_message`, `save_check`, etc.) is called from `core/` exactly as in the terminal version.

`run_check(message, source_input)` — the Streamlit version of `check_and_report()`, using `st.spinner()` as a loading indicator and `st.markdown()` to display the result.

---

## `core/ollama_client.py` — LLM orchestration

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `_call_ollama(messages, use_tools)` | message list, whether to send tools | `dict` (Ollama JSON response) | Raw POST request to `/api/chat` |
| `_build_kb_context(user_message)` | user message | `str` | Calls `knowledge_base.search()` and formats the matches as extra context. Returns an empty string if the KB fails or has no match |
| `check_message(user_message, max_tool_rounds)` | user message, max tool-call iterations | `(str, list)` — (final answer, list of search queries used) | Main function: builds messages (system + KB context + user), loops over Ollama calls, runs `run_tool()` when there are `tool_calls`, returns the final answer when there are none |

Constant: `MODEL = "qwen3:4b"` (chat model). Imports from `core.tools` and `core.knowledge_base`.

---

## `core/tools.py` — Web search & cross-check

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `_search_raw(query, max_results)` | keywords, number of results | `list[dict]` | Wrapper around `duckduckgo_search.DDGS().text()`, returns an empty list on error |
| `cross_check_search(claim)` | claim to verify | `str` | Searches the claim directly + searches "fact check OR hoax OR debunked {claim}", merges and dedupes by URL, tags each result using `score_source()` |
| `run_tool(name, arguments)` | tool name, arguments from the LLM | `str` | Dispatcher — currently only handles `"web_search"` |

`TOOLS_SCHEMA` — the JSON schema sent to Ollama so the LLM knows which tools are available and their format (OpenAI-style function calling).

---

## `core/credibility.py` — Source credibility scoring

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `score_source(url)` | source URL | `dict` `{domain, score, tier}` | Extracts the domain from the URL, matches it against `CREDIBILITY_TIERS`, falls back to `DEFAULT_SCORE` |
| `_label(score)` | numeric score | `str` | Converts a score to a label ("Highly credible" / "Fairly credible" / "Unknown / use caution") |

`CREDIBILITY_TIERS` — a dictionary of domain → score (0.0–1.0), maintained manually and easy to extend.

---

## `core/knowledge_base.py` — Past-hoax RAG

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `_get_embedding(text)` | text | `list[float]` | Calls Ollama's `/api/embeddings` (model `nomic-embed-text`) and returns a vector |
| `_cosine_similarity(a, b)` | two vectors | `float` | Measures how similar two vectors' directions are (dot product / product of norms) |
| `build_index(force)` | force a rebuild or not | - | Embeds every entry in `known_hoaxes.json` and saves it to the cache `known_hoaxes_embeddings.json`. Skipped if the cache already exists (unless `force=True`) |
| `search(query, top_k, min_similarity)` | new claim, max results, similarity threshold | `list[dict]` | Embeds the query, compares it to all cached entries, filters and sorts by similarity |

---

## `core/database.py` — History & cache (SQLite)

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `init_db()` | - | - | Creates the `data/history.db` file + `checks` table if they don't exist |
| `save_check(message, verdict, sources, source_input)` | message, result, list of search queries, input type | - | Inserts a new row into `checks` |
| `get_history(limit)` | max entries | `list[dict]` | Fetches the latest N entries, newest first |
| `find_cached(message)` | message | `dict` or `None` | Looks for an exact match of the same message, for caching |

`checks` table schema: `id, timestamp, message, verdict, sources (JSON string), source_input`.

`core/database_mysql.py` is an optional MySQL drop-in with the same four functions.

---

## `core/ocr.py` — Extract text from images

| Function | Parameters | Returns | Purpose |
|---|---|---|---|
| `extract_text_from_image(image_path, lang)` | image path, Tesseract language code | `str` | Opens the image with PIL and runs `pytesseract.image_to_string()`. Raises a clear error if Tesseract is not installed |

---

## `core/prompts.py`

A single constant: `SYSTEM_PROMPT` — full instructions for the LLM on how to analyze a message (extract claims, check the KB, search if needed, prioritize credible sources, answer format).

---

## Full data flow (one check)

```
User input (text/image)
    │
    ▼
[OCR if image] → text
    │
    ▼
find_cached() ── found? ──▶ show the old result, DONE
    │ (not found)
    ▼
_build_kb_context() ── embed the message, find similar entries in known_hoaxes.json
    │
    ▼
check_message()
    │
    ▼
messages = [system_prompt, kb_context?, user_message]
    │
    ▼
┌─────────────── loop (max 3x) ───────────────┐
│ _call_ollama(messages)                       │
│    │                                         │
│    ├─ tool_calls? ──▶ run_tool()             │
│    │                   └─ cross_check_search()
│    │                        └─ score_source() per result
│    │                   └─ result appended to messages
│    │                   └─ LOOP AGAIN         │
│    │                                         │
│    └─ no tool_calls ──▶ final answer         │
└───────────────────────────────────────────────┘
    │
    ▼
save_check() → store in SQLite
    │
    ▼
Display to the user (terminal/GUI)
```
