import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.sources import JOB_SOURCES


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


WORKDAY_SEARCH_TERMS = (
    "design verification",
    "verification engineer",
    "rtl",
    "logic design",
    "physical design",
    "layout",
    "analog design",
    "dft",
    "silicon validation",
    "fpga",
)


VIETNAM_LOCATION_PATTERN = re.compile(
    r"(ho chi minh(?: city)?|hcmc|hanoi|ha noi|da nang|danang|viet\s*nam|vietnam)",
    flags=re.IGNORECASE,
)


def _clean(text):
    if text is None:
        return ""
    if isinstance(text, (list, tuple, set)):
        text = " ".join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    return re.sub(r"\s+", " ", text).strip()


def _request_html(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=25,
    )
    response.raise_for_status()
    return response.text, response.url


def _job_key(job):
    return "|".join(
        [
            _clean(job.get("company", "")).lower(),
            _clean(job.get("title", "")).lower(),
            _clean(job.get("location", "")).lower(),
            _clean(job.get("link", "")).lower(),
        ]
    )


def _dedupe(jobs):
    unique = []
    seen = set()
    for job in jobs:
        key = _job_key(job)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def _extract_location(context, default=""):
    text = _clean(context)
    match = VIETNAM_LOCATION_PATTERN.search(text)

    if match:
        location = match.group(0).lower()
        replacements = {
            "hcmc": "Ho Chi Minh City, Vietnam",
            "ho chi minh": "Ho Chi Minh City, Vietnam",
            "ho chi minh city": "Ho Chi Minh City, Vietnam",
            "hanoi": "Hanoi, Vietnam",
            "ha noi": "Hanoi, Vietnam",
            "da nang": "Da Nang, Vietnam",
            "danang": "Da Nang, Vietnam",
            "viet nam": "Vietnam",
            "vietnam": "Vietnam",
        }
        return replacements.get(location, match.group(0))

    return default


def _parse_html_job_page(html, source, page_url):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True))
        href = _clean(anchor.get("href", ""))

        if not title or not href:
            continue

        url = urljoin(page_url, href)
        lower_url = url.lower()
        is_job_link = (
            "/job/" in lower_url
            or "/jobs/" in lower_url
            or "/careers/job/" in lower_url
        )

        if not is_job_link:
            continue
        if (
            "/search/" in lower_url
            or lower_url.rstrip("/").endswith("/jobs")
        ):
            continue

        parent = anchor.find_parent(
            ["li", "article", "div", "section", "tr"]
        )
        context = _clean(
            parent.get_text(" ", strip=True)
            if parent
            else title
        )
        location = _extract_location(
            context,
            source.get("default_location", ""),
        )

        jobs.append({
            "source": source["name"],
            "company": source["company"],
            "title": title,
            "link": url,
            "location": location,
            "country": source.get("country_filter", ""),
            "posted": "",
            "summary": "",
            "context": context,
            "assume_vietnam": source.get("assume_vietnam", False),
        })

    return _dedupe(jobs)


def fetch_html_jobs(source):
    html, page_url = _request_html(source["url"])
    return _parse_html_job_page(html, source, page_url)


def fetch_query_html_jobs(source):
    jobs = []

    for term in source.get("search_terms", WORKDAY_SEARCH_TERMS):
        params = {source.get("query_param", "q"): term}
        location_param = source.get("location_param")
        if location_param:
            params[location_param] = source.get(
                "country_filter",
                "Vietnam",
            )

        html, page_url = _request_html(source["url"], params=params)
        jobs.extend(_parse_html_job_page(html, source, page_url))

    return _dedupe(jobs)


def fetch_catalog_jobs(source):
    html, _ = _request_html(source["url"])
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for heading in soup.find_all(["h2", "h3", "h4", "h5", "h6"]):
        title = _clean(heading.get_text(" ", strip=True))
        if len(title) < 6:
            continue

        container = heading.find_parent(
            ["article", "section", "div", "li"]
        )
        context = _clean(
            container.get_text(" ", strip=True)
            if container
            else title
        )

        jobs.append({
            "source": source["name"],
            "company": source["company"],
            "title": title,
            "link": source["url"],
            "location": source.get("default_location", ""),
            "country": source.get("country_filter", ""),
            "posted": "",
            "summary": "",
            "context": context,
            "assume_vietnam": source.get("assume_vietnam", False),
        })

    for node in soup.find_all(string=re.compile(r"Job\s*ID", re.I)):
        text = _clean(node.parent.get_text(" ", strip=True))
        if not text:
            continue

        title = re.sub(
            r"\s*\(\s*Job\s*ID\s*:.*?\)\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        if len(title) < 6:
            continue

        jobs.append({
            "source": source["name"],
            "company": source["company"],
            "title": title,
            "link": source["url"],
            "location": source.get("default_location", ""),
            "country": source.get("country_filter", ""),
            "posted": "",
            "summary": "",
            "context": text,
            "assume_vietnam": source.get("assume_vietnam", False),
        })

    return _dedupe(jobs)


def fetch_workday_jobs(source):
    parsed = urlparse(source["url"])
    host = parsed.netloc
    tenant = source["workday_tenant"]
    site = source["workday_site"]
    endpoint = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    jobs = []

    for search_term in source.get("search_terms", WORKDAY_SEARCH_TERMS):
        offset = 0

        while offset < 100:
            response = requests.post(
                endpoint,
                headers={
                    **HEADERS,
                    "Content-Type": "application/json",
                },
                json={
                    "appliedFacets": {},
                    "limit": 20,
                    "offset": offset,
                    "searchText": search_term,
                },
                timeout=25,
            )
            response.raise_for_status()

            payload = response.json()
            postings = payload.get("jobPostings", [])

            for posting in postings:
                title = _clean(posting.get("title", ""))
                location = _clean(
                    posting.get(
                        "locationsText",
                        posting.get("location", ""),
                    )
                )
                path = _clean(posting.get("externalPath", ""))

                if not title or not path:
                    continue

                link = (
                    f"https://{host}/en-US/{site}{path}"
                    if path.startswith("/")
                    else urljoin(source["url"], path)
                )

                jobs.append({
                    "source": source["name"],
                    "company": source["company"],
                    "title": title,
                    "link": link,
                    "location": location,
                    "country": "",
                    "posted": _clean(posting.get("postedOn", "")),
                    "summary": "",
                    "context": " ".join(
                        [
                            title,
                            location,
                            _clean(posting.get("bulletFields", "")),
                        ]
                    ),
                    "assume_vietnam": False,
                })

            total = payload.get("total")
            offset += len(postings)

            if not postings:
                break
            if isinstance(total, int) and offset >= total:
                break
            if len(postings) < 20:
                break

    return _dedupe(jobs)


def fetch_jobs():
    jobs = []

    for source in JOB_SOURCES:
        if not source.get("enabled", False):
            continue

        print(f"\n[JOB FETCH] {source['name']} ({source['type']})")

        try:
            if source["type"] == "workday":
                source_jobs = fetch_workday_jobs(source)
            elif source["type"] == "html_jobs":
                source_jobs = fetch_html_jobs(source)
            elif source["type"] == "query_html_jobs":
                source_jobs = fetch_query_html_jobs(source)
            elif source["type"] == "catalog_jobs":
                source_jobs = fetch_catalog_jobs(source)
            else:
                print(f"[UNKNOWN JOB SOURCE TYPE] {source['type']}")
                continue

            print(
                f"[JOB RESULT] {source['name']} | "
                f"{len(source_jobs)} candidates"
            )
            jobs.extend(source_jobs)

        except (
            requests.RequestException,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            print(f"[JOB ERROR] {source['name']} | {error}")

    return _dedupe(jobs)
