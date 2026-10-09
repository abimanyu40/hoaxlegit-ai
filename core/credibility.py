from urllib.parse import urlparse

# Score 0.0 - 1.0. Feel free to add to or adjust this list.
CREDIBILITY_TIERS = {
    # Official government / fact-checking institutions
    "kominfo.go.id": 1.0,
    "turnbackhoax.id": 1.0,
    "cekfakta.com": 0.95,
    "bpom.go.id": 1.0,
    "kemkes.go.id": 1.0,
    "who.int": 1.0,

    # National mainstream media
    "kompas.com": 0.85,
    "antaranews.com": 0.85,
    "detik.com": 0.8,
    "tempo.co": 0.85,
    "cnnindonesia.com": 0.8,
    "liputan6.com": 0.75,

    # Credible international media
    "reuters.com": 0.9,
    "bbc.com": 0.85,
    "apnews.com": 0.9,
}

DEFAULT_SCORE = 0.3  # unknown source


def score_source(url: str) -> dict:
    domain = urlparse(url).netloc.replace("www.", "")
    for known_domain, score in CREDIBILITY_TIERS.items():
        if known_domain in domain:
            return {"domain": domain, "score": score, "tier": _label(score)}
    return {"domain": domain, "score": DEFAULT_SCORE, "tier": _label(DEFAULT_SCORE)}


def _label(score: float) -> str:
    if score >= 0.8:
        return "Highly credible"
    elif score >= 0.5:
        return "Fairly credible"
    else:
        return "Unknown / use caution"
