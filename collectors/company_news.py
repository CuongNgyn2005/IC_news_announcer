import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


DATE_PATTERN = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def _title_from_anchor(anchor):
    heading = anchor.find(["h1", "h2", "h3", "h4", "h5", "h6"])

    if heading:
        value = _clean(heading.get_text(" ", strip=True))
        if value:
            return value

    return _clean(anchor.get_text(" ", strip=True))


def _article_from_anchor(source, anchor, url):
    title = _title_from_anchor(anchor)
    parent = anchor.find_parent(
        ["article", "li", "section", "div"]
    )
    context = _clean(
        parent.get_text(" ", strip=True)
        if parent
        else title
    )

    summary = context
    if summary.startswith(title):
        summary = _clean(summary[len(title):])
    summary = summary[:700]

    date_match = DATE_PATTERN.search(context)

    return {
        "source": source["name"],
        "company": source["company"],
        "category": source["category"],
        "title": title,
        "link": url,
        "published": date_match.group(0) if date_match else "",
        "summary": summary,
    }


def fetch_marvell(source):
    html = fetch_page(source["url"])
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        title = _title_from_anchor(anchor)
        url = urljoin(source["url"], href)

        if not title or len(title) < 20:
            continue
        if "/company/newsroom/" not in url:
            continue
        if url.endswith("newsroom.html") or url in seen:
            continue

        seen.add(url)
        articles.append(_article_from_anchor(source, anchor, url))

    return articles


def fetch_ampere(source):
    html = fetch_page(source["url"])
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = _clean(anchor.get("href", ""))
        title = _title_from_anchor(anchor)

        if not title or not href or len(title) < 20:
            continue

        url = urljoin(source["url"], href)
        lower_url = url.lower()

        allowed = (
            "/press/" in lower_url
            or "/blog/" in lower_url
            or "/blogs/" in lower_url
            or "/news/" in lower_url
        )

        if not allowed or url in seen:
            continue

        seen.add(url)
        articles.append(_article_from_anchor(source, anchor, url))

    return articles


def fetch_company_news(source):
    company = source.get("company", "").lower()

    try:
        if company == "marvell":
            articles = fetch_marvell(source)
        elif company == "ampere computing":
            articles = fetch_ampere(source)
        else:
            print(
                f"[NO COMPANY COLLECTOR] {source['name']}"
            )
            return []

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
