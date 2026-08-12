import feedparser
import requests

from config.sources import JOB_SOURCES, NEWS_SOURCES


HEADERS = {
    "User-Agent": "IC-Watch-Bot/1.0",
}


def check_rss(source):
    try:
        response = requests.get(
            source["url"],
            timeout=15,
            headers=HEADERS,
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
            headers=HEADERS,
        )
        if response.status_code == 200:
            return "REACHABLE", response.status_code
        return "ERROR", response.status_code

    except requests.RequestException as error:
        return f"ERROR: {error}", None


def check_workday(source):
    host = source["url"].split("/")[2]
    endpoint = (
        f"https://{host}/wday/cxs/"
        f"{source['workday_tenant']}/"
        f"{source['workday_site']}/jobs"
    )

    try:
        response = requests.post(
            endpoint,
            timeout=15,
            headers={
                **HEADERS,
                "Content-Type": "application/json",
            },
            json={
                "appliedFacets": {},
                "limit": 1,
                "offset": 0,
                "searchText": "design verification",
            },
        )

        if response.status_code == 200:
            count = len(response.json().get("jobPostings", []))
            return "REACHABLE", response.status_code, count

        return "ERROR", response.status_code, 0

    except (requests.RequestException, ValueError) as error:
        return f"ERROR: {error}", None, 0


def print_news_sources():
    print("\nNEWS SOURCES")
    print("=" * 70)

    for source in NEWS_SOURCES:
        print(f"\nSource: {source['name']}")
        print(f"Type:   {source['type']}")
        print(f"Active: {source['enabled']}")
        print(f"URL:    {source['url']}")

        if source["type"] == "rss":
            result, status, entries = check_rss(source)
            print(f"Health: {result}")
            print(f"HTTP:   {status}")
            print(f"Entries:{entries}")
        else:
            result, status = check_html(source)
            print(f"Health: {result}")
            print(f"HTTP:   {status}")


def print_job_sources():
    print("\nJOB SOURCES")
    print("=" * 70)

    for source in JOB_SOURCES:
        print(f"\nSource: {source['name']}")
        print(f"Type:   {source['type']}")
        print(f"Active: {source['enabled']}")
        print(f"URL:    {source['url']}")

        if source["type"] == "workday":
            result, status, count = check_workday(source)
            print(f"Health: {result}")
            print(f"HTTP:   {status}")
            print(f"Probe jobs: {count}")
        else:
            result, status = check_html(source)
            print(f"Health: {result}")
            print(f"HTTP:   {status}")


def main():
    print("\nIC WATCH SOURCE HEALTH CHECK")
    print_news_sources()
    print_job_sources()


if __name__ == "__main__":
    main()
