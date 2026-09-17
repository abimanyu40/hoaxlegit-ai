from urllib.parse import urlparse

# Skor 0.0 - 1.0. Silakan tambah/sesuaikan daftar ini.
CREDIBILITY_TIERS = {
    # Resmi pemerintah / lembaga fact-check
    "kominfo.go.id": 1.0,
    "turnbackhoax.id": 1.0,
    "cekfakta.com": 0.95,
    "bpom.go.id": 1.0,
    "kemkes.go.id": 1.0,
    "who.int": 1.0,

    # Media arus utama nasional
    "kompas.com": 0.85,
    "antaranews.com": 0.85,
    "detik.com": 0.8,
    "tempo.co": 0.85,
    "cnnindonesia.com": 0.8,
    "liputan6.com": 0.75,

    # Media internasional kredibel
    "reuters.com": 0.9,
    "bbc.com": 0.85,
    "apnews.com": 0.9,
}

DEFAULT_SCORE = 0.3  # sumber tidak dikenal


def score_source(url: str) -> dict:
    domain = urlparse(url).netloc.replace("www.", "")
    for known_domain, score in CREDIBILITY_TIERS.items():
        if known_domain in domain:
            return {"domain": domain, "score": score, "tier": _label(score)}
    return {"domain": domain, "score": DEFAULT_SCORE, "tier": _label(DEFAULT_SCORE)}


def _label(score: float) -> str:
    if score >= 0.8:
        return "Sangat kredibel"
    elif score >= 0.5:
        return "Cukup kredibel"
    else:
        return "Tidak dikenal / perlu hati-hati"
