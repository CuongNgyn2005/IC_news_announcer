import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def fetch_html_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    return response.text


def extract_links(source):
    """
    Generic HTML collector.

    It discovers candidate article links. More precise
    source-specific collectors can replace this later.
    """

    html = fetch_html_page(source["url"])

    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen_urls = set()

    for anchor in soup.find_all("a", href=True):
        title = anchor.get_text(
            " ",
            strip=True,
        )

        href = anchor.get("href")

        if not title or not href:
            continue

        # Ignore tiny navigation labels.
        if len(title) < 20:
            continue

        url = urljoin(
            source["url"],
            href,
        )

        if url in seen_urls:
            continue

        seen_urls.add(url)

        articles.append({
            "source": source["name"],
            "title": title,
            "link": url,
            "published": "",
            "summary": "",
        })

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
            f"[HTML ERROR] {source['name']} | "
            f"{error}"
        )

        return []