import json
import requests

from core.tools import TOOLS_SCHEMA, run_tool
from core import knowledge_base

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"  # ganti ke qwen2.5:3b kalau berat di RTX 2050


def _call_ollama(messages, use_tools=True):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    if use_tools:
        payload["tools"] = TOOLS_SCHEMA

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()


def _build_kb_context(user_message: str) -> str:
    """Cari klaim mirip di database hoax lama, format jadi konteks tambahan."""
    try:
        matches = knowledge_base.search(user_message)
    except Exception:
        return ""  # KB gagal (misal model embedding belum di-pull), skip aja

    if not matches:
        return ""

    lines = ["Database hoax yang sudah pernah diverifikasi (kemiripan tinggi):"]
    for m in matches:
        lines.append(
            f"- Klaim serupa: \"{m['claim']}\" -> Verdict: {m['verdict']} "
            f"(kemiripan {m['similarity']})\n  Penjelasan: {m['explanation']}"
        )
    return "\n".join(lines)


def check_message(user_message: str, max_tool_rounds: int = 3) -> tuple[str, list]:
    """
    Cek satu pesan. Return (jawaban_final, daftar_sumber_yang_dipakai).
    """
    from core.prompts import SYSTEM_PROMPT

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    kb_context = _build_kb_context(user_message)
    if kb_context:
        messages.append({"role": "system", "content": kb_context})

    messages.append({"role": "user", "content": user_message})

    sources_used = []

    for _ in range(max_tool_rounds):
        data = _call_ollama(messages)
        message = data["message"]

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            messages.append(message)
            return message.get("content", ""), sources_used

        messages.append(message)
        for call in tool_calls:
            fn_name = call["function"]["name"]
            fn_args = call["function"]["arguments"]
            if isinstance(fn_args, str):
                fn_args = json.loads(fn_args)

            query = fn_args.get("query", "")
            print(f"[mencari: {query}]")
            result = run_tool(fn_name, fn_args)
            sources_used.append(query)

            messages.append({"role": "tool", "content": result})

    data = _call_ollama(messages, use_tools=False)
    final_message = data["message"]
    return final_message.get("content", ""), sources_used
