from duckduckgo_search import DDGS

from core.credibility import score_source

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Cari informasi terbaru di internet untuk memverifikasi sebuah klaim. "
                            "Otomatis melakukan cross-check dari sisi klaim langsung dan sisi bantahan/fakta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Klaim inti yang mau diverifikasi (bukan kata kunci pencarian mentah)."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def _search_raw(query: str, max_results: int = 3):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []


def cross_check_search(claim: str) -> str:
    """
    Multi-source cross-check: search klaim langsung + search sisi bantahan/fakta,
    lalu tag tiap hasil dengan skor kredibilitas sumbernya.
    """
    direct_results = _search_raw(claim, max_results=3)
    fact_check_results = _search_raw(f"fakta OR hoax OR bantahan {claim}", max_results=3)

    all_results = direct_results + fact_check_results
    seen_urls = set()
    formatted = []

    for r in all_results:
        href = r.get("href", "")
        if href in seen_urls:
            continue
        seen_urls.add(href)

        credibility = score_source(href)
        formatted.append(
            f"- {r.get('title', '')}\n"
            f"  {r.get('body', '')}\n"
            f"  Sumber: {href} (Kredibilitas: {credibility['tier']}, skor {credibility['score']})"
        )

    if not formatted:
        return "Tidak ada hasil pencarian yang ditemukan untuk klaim ini."

    return "\n\n".join(formatted)


def run_tool(name: str, arguments: dict) -> str:
    if name == "web_search":
        return cross_check_search(arguments.get("query", ""))
    return f"Tool '{name}' tidak dikenal."
