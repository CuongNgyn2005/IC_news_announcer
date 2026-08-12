import feedparser

from config.sources import NEWS_SOURCES
from collectors.html_news import fetch_html_news
from collectors.company_news import fetch_company_news
from collectors.truechip_news import fetch_truechip_news


FPT_STATIC_PAGE_TITLES = {
    "power management multi-channel (pmic)",
    "fas06.8",
    "osat factory",
    "load switch",
    "automotive",
    "hps",
    "our applications",
    "fas eid",
    "on-job training",
    "accelerate your ic development with custom ip & solutions",
    "fas06",
    "reset your password",
    "boost converter",
    "engineering services",
    "personal electronic devices",
    "fas02",
    "our services",
    "technical resources",
    "buck converter",
}


def _rss_content(entry):
    values = []
    for item in entry.get("content", []) or []:
        if isinstance(item, dict):
            value = item.get("value", "")
            if value:
                values.append(value)
    return " ".join(values)


def _normalized_feed_title(title):
    value = (title or "").strip().lower()
    for suffix in (" - fpt semiconductor", " - marvell technology"):
        if value.endswith(suffix):
            value = value[: -len(suffix)].strip()
    return value


def _allow_rss_entry(source, entry):
    if source.get("name") != "FPT Semiconductor News":
        return True

    title = _normalized_feed_title(entry.get("title", ""))
    return title not in FPT_STATIC_PAGE_TITLES


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
        if not _allow_rss_entry(source, entry):
            print(
                f"[RSS STATIC REJECT] {source['name']} | "
                f"{entry.get('title', '').strip()}"
            )
            continue

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
            "content": _rss_content(entry),
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
        elif source["type"] == "truechip":
            source_articles = fetch_truechip_news(source)
        elif source["type"] == "html":
            source_articles = fetch_html_news(source)
        else:
            print(f"[UNKNOWN SOURCE TYPE] {source['type']}")
            continue

        articles.extend(source_articles)

    return articles
