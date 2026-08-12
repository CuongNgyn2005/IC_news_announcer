import html
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


NOT_STATED = "Not stated in the source text available to the bot."


COMPANY_DOMAINS = {
    "marvell": "marvell.com",
    "hcltech": "hcltech.com",
    "ideas2silicon": "ideas2silicon.com",
}


FIELD_RULES = {
    "engineering_breakthrough": (
        "transistor",
        "nanosheet",
        "gate-all-around",
        "gaa",
        "finfet",
        "architecture",
        "microarchitecture",
        "chiplet",
        "optical",
        "interconnect",
        "processor",
        "accelerator",
        "switch",
        "memory",
        "hbm",
        "serdes",
        "cxl",
        "ucie",
        "lithography",
        "material",
    ),
    "process_node": (
        "process node",
        "nanosheet",
        "gate-all-around",
        "finfet",
        "euv",
        "high-na",
        "high na",
        "lithography",
        "foundry",
        "fab",
        "fabrication",
        "tsmc",
        "samsung foundry",
        "intel foundry",
    ),
    "packaging": (
        "cowos",
        "packaging",
        "chiplet",
        "hybrid bonding",
        "3d integration",
        "2.5d",
        "3d packaging",
        "optical i/o",
        "optical io",
        "ucie",
        "interposer",
        "interconnect",
    ),
    "power": (
        "power",
        "energy",
        "efficiency",
        "watt",
        "watts",
        "tops/w",
        "tops per watt",
        "performance per watt",
    ),
    "performance": (
        "performance",
        "throughput",
        "tops",
        "tflops",
        "ghz",
        "tbps",
        "gbps",
        "bandwidth",
        "latency",
        "clock speed",
        "faster",
        "uplift",
    ),
    "area_density": (
        "area",
        "density",
        "mtr/mm",
        "transistor density",
        "die size",
        "mm²",
        "mm2",
    ),
    "financial": (
        "funding",
        "investment",
        "invested",
        "capex",
        "capital expenditure",
        "deal",
        "valuation",
        "billion",
        "million",
    ),
    "production": (
        "tape-out",
        "tape out",
        "risk production",
        "volume production",
        "mass production",
        "manufacturing",
        "sampling",
        "sampled",
        "shipping",
        "availability",
        "available",
        "production",
    ),
    "use_case": (
        "data center",
        "datacenter",
        "ai infrastructure",
        "artificial intelligence",
        "automotive",
        "mobile",
        "smartphone",
        "edge computing",
        "edge ai",
        "cloud",
        "hpc",
        "high-performance computing",
        "networking",
    ),
}


TECH_METRIC_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*(?:nm|ghz|tbps|gbps|tops|tflops|watts?|w)\b|"
    r"\b\d+(?:\.\d+)?\s*%|"
    r"\$\s*\d+(?:\.\d+)?\s*(?:billion|million|bn|m)?|"
    r"\b\d+(?:\.\d+)?\s*(?:x|times)\b)",
    flags=re.IGNORECASE,
)


NODE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*nm\b", re.IGNORECASE)
FINANCIAL_PATTERN = re.compile(
    r"(?:\$|usd\s*)\d+(?:\.\d+)?\s*(?:billion|million|bn|m)?",
    re.IGNORECASE,
)


def _clean(text):
    text = html.unescape(str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _html_to_text(value):
    if not isinstance(value, str):
        value = str(value or "")
    soup = BeautifulSoup(value, "html.parser")
    return _clean(soup.get_text(" ", strip=True))


def _browser_get(url):
    headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml",
        "Referer": url,
    }

    if curl_requests is not None:
        response = curl_requests.get(
            url,
            headers=headers,
            timeout=20,
            impersonate="chrome",
        )
        response.raise_for_status()
        return response

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response


def _page_text(response):
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(
        ["script", "style", "noscript", "svg", "nav", "footer", "aside"]
    ):
        tag.decompose()

    root = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [
        _clean(node.get_text(" ", strip=True))
        for node in root.find_all(["p", "li"])
    ]
    paragraphs = [text for text in paragraphs if len(text) >= 35]
    return _clean(" ".join(paragraphs))[:40000]


def _google_source_link(response, article):
    soup = BeautifulSoup(response.text, "html.parser")
    company = _clean(article.get("company", "")).lower()
    preferred_domain = COMPANY_DOMAINS.get(company, "")
    external = []

    for anchor in soup.find_all("a", href=True):
        href = urljoin(response.url, anchor.get("href", ""))
        host = urlparse(href).netloc.lower()
        if not href.startswith("http"):
            continue
        if any(
            blocked in host
            for blocked in (
                "google.com",
                "googleusercontent.com",
                "gstatic.com",
                "youtube.com",
            )
        ):
            continue
        external.append(href)

    if preferred_domain:
        for href in external:
            if preferred_domain in urlparse(href).netloc.lower():
                return href

    return external[0] if external else ""


def _fetch_article_text(article):
    link = _clean(article.get("link", ""))
    if not link.startswith("http"):
        return ""

    try:
        response = _browser_get(link)
        host = urlparse(response.url).netloc.lower()

        if "news.google.com" in host:
            source_link = _google_source_link(response, article)
            if source_link:
                try:
                    source_response = _browser_get(source_link)
                    source_text = _page_text(source_response)
                    if source_text:
                        return source_text
                except Exception:
                    pass

        return _page_text(response)
    except Exception:
        return ""


def _sentences(text):
    cleaned = _clean(text)
    if not cleaned:
        return []

    chunks = re.split(r"(?<=[.!?])\s+|\s*[•▪●]\s*", cleaned)
    return [chunk.strip() for chunk in chunks if 20 <= len(chunk.strip()) <= 700]


def _score_sentence(sentence, terms):
    lower = sentence.lower()
    score = sum(2 for term in terms if term in lower)

    if TECH_METRIC_PATTERN.search(sentence):
        score += 3
    if any(
        cue in lower
        for cue in (
            "first",
            "new",
            "introduc",
            "launch",
            "enable",
            "deliver",
            "improv",
            "reduce",
            "increase",
            "production",
            "available",
        )
    ):
        score += 1

    return score


def _best_sentence(sentences, terms, require_metric=False, extra_check=None):
    candidates = []

    for sentence in sentences:
        lower = sentence.lower()
        if not any(term in lower for term in terms):
            continue
        if require_metric and not TECH_METRIC_PATTERN.search(sentence):
            continue
        if extra_check and not extra_check(sentence):
            continue

        candidates.append((_score_sentence(sentence, terms), sentence))

    if not candidates:
        return NOT_STATED

    candidates.sort(key=lambda item: (-item[0], len(item[1])))
    return candidates[0][1][:220]


def summarize_text(text):
    sentences = _sentences(text)

    process_terms = FIELD_RULES["process_node"]
    process = _best_sentence(
        sentences,
        process_terms,
        extra_check=lambda sentence: (
            NODE_PATTERN.search(sentence) is not None
            or any(term in sentence.lower() for term in process_terms)
        ),
    )

    financial = _best_sentence(
        sentences,
        FIELD_RULES["financial"],
        extra_check=lambda sentence: (
            FINANCIAL_PATTERN.search(sentence) is not None
            or "capex" in sentence.lower()
            or "investment" in sentence.lower()
            or "funding" in sentence.lower()
        ),
    )

    return {
        "engineering_breakthrough": _best_sentence(
            sentences,
            FIELD_RULES["engineering_breakthrough"],
        ),
        "process_node": process,
        "packaging": _best_sentence(sentences, FIELD_RULES["packaging"]),
        "power": _best_sentence(
            sentences,
            FIELD_RULES["power"],
            require_metric=True,
        ),
        "performance": _best_sentence(
            sentences,
            FIELD_RULES["performance"],
            require_metric=True,
        ),
        "area_density": _best_sentence(
            sentences,
            FIELD_RULES["area_density"],
            require_metric=True,
        ),
        "financial": financial,
        "production": _best_sentence(sentences, FIELD_RULES["production"]),
        "use_case": _best_sentence(sentences, FIELD_RULES["use_case"]),
    }


def summarize_article(article):
    rss_or_listing_text = _clean(
        " ".join(
            [
                article.get("title", ""),
                _html_to_text(article.get("summary", "")),
                _html_to_text(article.get("content", "")),
            ]
        )
    )
    fetched_text = _fetch_article_text(article)
    combined = _clean(f"{rss_or_listing_text} {fetched_text}")
    return summarize_text(combined)


def format_technical_summary(summary):
    return (
        "### 1. Core Technical Innovation\n\n"
        f"- Engineering Breakthrough: {summary['engineering_breakthrough']}\n"
        f"- Process Node & Fabrication: {summary['process_node']}\n"
        f"- Key Interconnect/Packaging: {summary['packaging']}\n\n"
        "### 2. Hard Performance Metrics (PPA)\n\n"
        f"- Power Efficiency: {summary['power']}\n"
        f"- Performance Uplift: {summary['performance']}\n"
        f"- Area / Density: {summary['area_density']}\n\n"
        "### 3. Commercial & Scale Highlights\n\n"
        f"- Financial/CapEx Footprint: {summary['financial']}\n"
        f"- Production Status & Timeline: {summary['production']}\n"
        f"- Primary Use Case: {summary['use_case']}"
    )
