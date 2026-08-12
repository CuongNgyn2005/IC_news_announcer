import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()
    return response.text


def fetch_marvell(source):
    html = fetch_page(source["url"])
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        title = anchor.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(source["url"], href)

        # Keep actual Marvell newsroom articles.
        if "/company/newsroom/" not in url:
            continue

        if url.endswith("newsroom.html"):
            continue

        if len(title) < 20:
            continue

        if url in seen:
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


def fetch_ampere(source):
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

        # Ampere article families
        allowed = (
            "/press/" in lower_url
            or "/blog/" in lower_url
            or "/blogs/" in lower_url
            or "/news/" in lower_url
        )

        if not allowed:
            continue

        if url in seen:
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

def fetch_company_news(source):
    company = source.get("company", "").lower()

    try:
        if company == "marvell":
            articles = fetch_marvell(source)

        elif company == "ampere computing":
            articles = fetch_ampere(source)

        else:
            print(
                f"[NO COMPANY COLLECTOR] "
                f"{source['name']}"
            )
            return []

        print(
            f"[COMPANY RESULT] "
            f"{source['name']} | "
            f"{len(articles)} candidates"
        )

        return articles

    except requests.RequestException as error:
        print(
            f"[COMPANY ERROR] "
            f"{source['name']} | "
            f"{error}"
        )
        return []