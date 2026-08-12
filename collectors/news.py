import feedparser

from config.sources import NEWS_SOURCES
from collectors.html_news import fetch_html_news
from collectors.company_news import fetch_company_news


def fetch_rss_news(source):
    print(f"[RSS FETCH] {source['name']}")

    feed = feedparser.parse(source["url"])

    if feed.bozo:
        print(
            f"[RSS WARNING] {source['name']} | "
            f"{feed.bozo_exception}"
        )

    print(
        f"[RSS RESULT] {source['name']} | "
        f"{len(feed.entries)} entries"
    )

    articles = []

    for entry in feed.entries[:20]:
        articles.append({
            "source": source["name"],
            "company": source.get("company"),
            "category": source.get("category"),
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "published": entry.get(
                "published",
                entry.get("updated", ""),
            ),
            "summary": entry.get(
                "summary",
                entry.get("description", ""),
            ),
        })

    return articles


def fetch_news():
    articles = []

    for source in NEWS_SOURCES:

        if not source["enabled"]:
            continue

        print(
            f"\n[FETCH] {source['name']} "
            f"({source['type']})"
        )

        if source["type"] == "rss":
            source_articles = fetch_rss_news(source)

        elif source["type"] == "company":
            source_articles = fetch_company_news(source)

        elif source["type"] == "html":
            source_articles = fetch_html_news(source)

        else:
            print(
                f"[UNKNOWN SOURCE TYPE] "
                f"{source['type']}"
            )
            continue

        articles.extend(source_articles)

    return articles