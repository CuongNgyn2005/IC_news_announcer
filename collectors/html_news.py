import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


DATE_PATTERN = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}",
    flags=re.IGNORECASE,
)

SKYE_DATED_POST_PATH = re.compile(r"^/20\d{2}/\d{1,2}/\d{1,2}/[^/]+/?$")


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_html_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def _candidate_title(anchor):
    heading = anchor.find(["h1", "h2", "h3", "h4", "h5", "h6"])

    if heading:
        title = _clean(heading.get_text(" ", strip=True))
        if title:
            return title

    return _clean(anchor.get_text(" ", strip=True))


def _allowed_article_url(source, url):
    """Prevent broad corporate pages from turning navigation links into news."""
    name = source.get("name", "").lower()
    parsed = urlparse(url)
    path = parsed.path.lower()

    if name == "infineon technology news":
        # Infineon's index lives under /about/press/technology-news, while the
        # actual article URLs live at /technology-news/YYYY/<article-id>.
        return path.startswith("/technology-news/") and path.count("/") >= 3

    if name == "skyechip media releases":
        # SkyeChip's category page does not preserve /media-release/ in the
        # article permalink; WordPress uses /YYYY/MM/DD/<slug>/ instead.
        return bool(SKYE_DATED_POST_PATH.match(path))

    return True


def extract_links(source):
    """Collect candidate links from a targeted company/news page."""
    html = fetch_html_page(source["url"])
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen_urls = set()

    for anchor in soup.find_all("a", href=True):
        title = _candidate_title(anchor)
        href = _clean(anchor.get("href", ""))

        if not title or not href or len(title) < 20:
            continue

        url = urljoin(source["url"], href)

        if not _allowed_article_url(source, url):
            continue
        if url.rstrip("/") == source["url"].rstrip("/"):
            continue
        if url in seen_urls:
            continue

        parent = anchor.find_parent(
            ["article", "li", "section", "div"]
        )
        context = _clean(
            parent.get_text(" ", strip=True)
            if parent
            else title
        )

        # Prevent a huge site/navigation container from making an unrelated
        # link look semiconductor-related. Keep only a small card-sized window.
        if len(context) > 1400:
            context = title

        summary = context
        if summary.startswith(title):
            summary = _clean(summary[len(title):])
        summary = summary[:700]

        date_match = DATE_PATTERN.search(context)
        published = date_match.group(0) if date_match else ""

        seen_urls.add(url)
        articles.append({
            "source": source["name"],
            "company": source.get("company"),
            "category": source.get("category"),
            "title": title,
            "link": url,
            "published": published,
            "summary": summary,
        })

        if source.get("name") == "Infineon Technology News" and len(articles) >= 40:
            break

    return articles


def fetch_html_news(source):
    try:
        articles = extract_links(source)

        print(
            f"[HTML RESULT] {source['name']} | "
            f"{len(articles)} candidates"
        )
        return articles

    except requests.RequestException as error:
        print(
            f"[HTML ERROR] {source['name']} | {error}"
        )
        return []
