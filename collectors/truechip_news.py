import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


TRUECHIP_ALLOWED_PATH_HINTS = (
    "news",
    "press",
    "blog",
    "article",
)


TRUECHIP_RELEVANT_TERMS = (
    "verification",
    "verification ip",
    "vip",
    "pcie",
    "cxl",
    "ucie",
    "usb",
    "ethernet",
    "ddr",
    "lpddr",
    "mipi",
    "noc",
    "risc-v",
    "riscv",
    "tilelink",
    "jesd",
    "silicon ip",
    "chiplet",
)


def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def _looks_relevant(title, url):
    text = f"{title} {url}".lower()
    return any(term in text for term in TRUECHIP_RELEVANT_TERMS)


def fetch_truechip(source):
    html = fetch_page(source["url"])
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        title = anchor.get_text(" ", strip=True)
        href = anchor.get("href", "").strip()

        if not title or not href:
            continue

        if len(title) < 20:
            continue

        url = urljoin(source["url"], href)
        lower_url = url.lower()

        if url in seen:
            continue

        path_hint = any(hint in lower_url for hint in TRUECHIP_ALLOWED_PATH_HINTS)
        relevant = _looks_relevant(title, url)

        if not (path_hint or relevant):
            continue

        if not relevant:
            continue

        seen.add(url)

        articles.append({
            "source": source["name"],
            "company": source["company"],
            "category": source["category"],
            "title": title,
            "link": url,
            "published": "",
            "summary": "",
        })

    return articles


def fetch_truechip_news(source):
    try:
        articles = fetch_truechip(source)
        print(
            f"[COMPANY RESULT] {source['name']} | "
            f"{len(articles)} candidates"
        )
        return articles

    except requests.RequestException as error:
        print(
            f"[COMPANY ERROR] {source['name']} | {error}"
        )
        return []
