from duckduckgo_search import DDGS

from core.credibility import score_source

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for current information to verify a claim. "
                            "Automatically cross-checks both the claim itself and fact-check/rebuttal sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The core claim to verify (not a raw keyword search)."
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
    Multi-source cross-check: search the claim directly + search the rebuttal/fact-check side,
    then tag each result with its source credibility score.
    """
    direct_results = _search_raw(claim, max_results=3)
    fact_check_results = _search_raw(f"fact check OR hoax OR debunked {claim}", max_results=3)

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
            f"  Source: {href} (Credibility: {credibility['tier']}, score {credibility['score']})"
        )

    if not formatted:
        return "No search results were found for this claim."

    return "\n\n".join(formatted)


def run_tool(name: str, arguments: dict) -> str:
    if name == "web_search":
        return cross_check_search(arguments.get("query", ""))
    return f"Unknown tool: '{name}'."
