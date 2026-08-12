import feedparser
import requests

from config.sources import NEWS_SOURCES


def check_rss(source):
    try:
        response = requests.get(
            source["url"],
            timeout=15,
            headers={
                "User-Agent": "IC-Watch-Bot/1.0"
            },
        )

        status = response.status_code

        feed = feedparser.parse(response.content)

        entries = len(feed.entries)

        if status == 200 and entries > 0:
            result = "OK"
        elif status == 200:
            result = "EMPTY"
        else:
            result = "ERROR"

        return result, status, entries

    except requests.RequestException as error:
        return f"ERROR: {error}", None, 0


def check_html(source):
    try:
        response = requests.get(
            source["url"],
            timeout=15,
            headers={
                "User-Agent": "IC-Watch-Bot/1.0"
            },
        )

        if response.status_code == 200:
            return "REACHABLE", response.status_code

        return "ERROR", response.status_code

    except requests.RequestException as error:
        return f"ERROR: {error}", None


def main():

    print("\nIC WATCH SOURCE HEALTH CHECK")
    print("=" * 70)

    for source in NEWS_SOURCES:

        print(f"\nSource: {source['name']}")
        print(f"Type:   {source['type']}")
        print(f"URL:    {source['url']}")
        print(f"Active: {source['enabled']}")

        if source["type"] == "rss":

            result, status, entries = check_rss(source)

            print(f"Health: {result}")
            print(f"HTTP:   {status}")
            print(f"Entries:{entries}")

        elif source["type"] == "html":

            result, status = check_html(source)

            print(f"Health: {result}")
            print(f"HTTP:   {status}")


if __name__ == "__main__":
    main()