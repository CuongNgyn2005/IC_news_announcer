import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.sources import JOB_SOURCES


try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None


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


ROLE_DISCOVERY_TERMS = (
    "design verification",
    "verification engineer",
    "soc verification",
    "rtl design",
    "rtl engineer",
    "rtl verification",
    "logic design",
    "digital design",
    "physical design",
    "physical implementation",
    "backend implementation",
    "front-end implementation",
    "frontend implementation",
    "layout design",
    "layout engineer",
    "custom layout",
    "analog layout",
    "analog design",
    "circuit design",
    "dft engineer",
    "design for test",
    "sta engineer",
    "silicon validation",
    "hardware validation",
    "fpga",
    "ic design trainee",
    "soc design engineer",
)


DEFAULT_JOB_PATH_HINTS = (
    "/job/",
    "/jobs/",
    "/careers/job/",
    "/career/",
    "/tuyen-dung/",
)


VIETNAM_LOCATION_PATTERN = re.compile(
    r"(ho chi minh(?: city)?|hcmc|hanoi|ha noi|da nang|danang|"
    r"quy nhon|gia lai|bac ninh|hai phong|binh duong|dong nai|"
    r"can tho|da lat|viet\s*nam|vietnam)",
    flags=re.IGNORECASE,
)


NON_TITLE_PREFIXES = (
    "responsible ",
    "responsibilities ",
    "work ",
    "develop ",
    "support ",
    "familiar ",
    "knowledge ",
    "assist ",
    "coordinate ",
    "participate ",
    "strong ",
    "implement ",
    "led ",
    "end-to-end ",
    "collaborate ",
    "at least ",
    "understanding ",
    "definition ",
    "perform ",
    "requirements ",
)


TITLE_NOUNS = (
    "engineer",
    "designer",
    "architect",
    "manager",
    "lead",
    "intern",
    "trainee",
    "design",
    "verification",
    "layout",
    "dft",
    "sta",
    "fpga",
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


def _browser_get(url, params=None, accept="text/html", referer=None):
    headers = {
        **HEADERS,
        "Accept": accept,
        "Referer": referer or url,
    }

    if curl_requests is not None:
        response = curl_requests.get(
            url,
            headers=headers,
            params=params,
            timeout=25,
            impersonate="chrome",
        )
        response.raise_for_status()
        return response

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=25,
    )
    response.raise_for_status()
    return response


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
            "quy nhon": "Quy Nhon, Vietnam",
            "gia lai": "Gia Lai, Vietnam",
            "bac ninh": "Bac Ninh, Vietnam",
            "hai phong": "Hai Phong, Vietnam",
            "binh duong": "Binh Duong, Vietnam",
            "dong nai": "Dong Nai, Vietnam",
            "can tho": "Can Tho, Vietnam",
            "da lat": "Da Lat, Vietnam",
            "viet nam": "Vietnam",
            "vietnam": "Vietnam",
        }
        return replacements.get(location, match.group(0))

    return default


def _looks_like_role(text):
    lower = _clean(text).lower()
    return any(term in lower for term in ROLE_DISCOVERY_TERMS)


def _looks_like_job_title(text):
    value = _clean(text)
    lower = value.lower()

    if not (4 <= len(value) <= 140):
        return False
    if any(lower.startswith(prefix) for prefix in NON_TITLE_PREFIXES):
        return False
    if not _looks_like_role(value):
        return False

    words = value.split()
    has_title_noun = any(noun in lower for noun in TITLE_NOUNS)
    if len(words) > 14 and not any(
        noun in lower
        for noun in ("engineer", "designer", "architect", "manager", "lead")
    ):
        return False

    return has_title_noun


def _job_record(source, title, link, context, location="", posted=""):
    return {
        "source": source["name"],
        "source_url": source["url"],
        "company": source["company"],
        "title": _clean(title),
        "link": link,
        "location": location or _extract_location(
            context,
            source.get("default_location", ""),
        ),
        "country": "",
        "posted": _clean(posted),
        "summary": "",
        "context": _clean(context),
        "assume_vietnam": source.get("assume_vietnam", False),
        "skip_detail_fetch": not source.get("detail_fetch", True),
    }


def _is_job_link(source, url):
    lower_url = url.lower()
    hints = tuple(source.get("job_url_hints", ())) + DEFAULT_JOB_PATH_HINTS

    if any(hint.lower() in lower_url for hint in hints):
        return True

    allowed_domains = source.get("job_link_domains", ())
    host = urlparse(url).netloc.lower()
    return any(domain.lower() in host for domain in allowed_domains)


def _title_from_job_anchor(anchor):
    text = _clean(anchor.get_text(" ", strip=True))
    parent = anchor.find_parent(["li", "article", "div", "section", "tr"])

    if _looks_like_job_title(text):
        return text, parent

    if parent:
        heading = parent.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        heading_text = _clean(heading.get_text(" ", strip=True)) if heading else ""
        if _looks_like_job_title(heading_text):
            return heading_text, parent

    return text, parent


def _parse_html_job_page(html, source, page_url):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for anchor in soup.find_all("a", href=True):
        title, parent = _title_from_job_anchor(anchor)
        href = _clean(anchor.get("href", ""))

        if not title or not href:
            continue

        url = urljoin(page_url, href)
        lower_url = url.lower()

        if not _is_job_link(source, url):
            continue
        if url.rstrip("/") == page_url.rstrip("/"):
            continue
        if "/search/" in lower_url or lower_url.rstrip("/").endswith("/jobs"):
            continue
        if not _looks_like_job_title(title):
            continue

        context = _clean(
            parent.get_text(" ", strip=True)
            if parent
            else title
        )

        jobs.append(_job_record(source, title, url, context))

    return _dedupe(jobs)


def _parse_markdown_job_links(text, source, base_url, default_location=""):
    jobs = []
    pattern = re.compile(r"\[([^\]\n]{4,160})\]\(([^)\s]+)\)")

    for match in pattern.finditer(text or ""):
        title = _clean(match.group(1))
        href = _clean(match.group(2))
        url = urljoin(base_url, href)

        if not _is_job_link(source, url) or not _looks_like_job_title(title):
            continue

        start = max(0, match.start() - 220)
        end = min(len(text), match.end() + 320)
        context = _clean(text[start:end])
        location = _extract_location(context, default_location)
        jobs.append(_job_record(source, title, url, context, location=location))

    return _dedupe(jobs)


def _proxy_markdown(url):
    proxy_url = "https://r.jina.ai/" + url
    response = requests.get(proxy_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def fetch_html_jobs(source):
    html, page_url = _request_html(source["url"])
    return _parse_html_job_page(html, source, page_url)


def fetch_query_html_jobs(source):
    jobs = []

    for term in source.get("search_terms", WORKDAY_SEARCH_TERMS):
        params = {source.get("query_param", "q"): term}
        location_param = source.get("location_param")
        if location_param:
            params[location_param] = source.get("country_filter", "Vietnam")

        html, page_url = _request_html(source["url"], params=params)
        jobs.extend(_parse_html_job_page(html, source, page_url))

    jobs = _dedupe(jobs)
    if jobs:
        return jobs

    # Some modern career portals return an empty JS shell to requests. Jina
    # Reader is used only as a public-page rendering fallback; links still
    # point to the employer's official career site and detail validation is
    # performed against the official posting before announcement.
    for term in source.get("search_terms", WORKDAY_SEARCH_TERMS):
        params = {source.get("query_param", "q"): term}
        location_param = source.get("location_param")
        if location_param:
            params[location_param] = source.get("country_filter", "Vietnam")
        prepared = requests.Request("GET", source["url"], params=params).prepare().url
        try:
            markdown = _proxy_markdown(prepared)
            jobs.extend(_parse_markdown_job_links(markdown, source, source["url"]))
        except requests.RequestException:
            continue

    return _dedupe(jobs)


def _best_role_cell(cells):
    for cell in cells:
        text = _clean(cell.get_text(" ", strip=True))
        if _looks_like_job_title(text):
            return text
    return ""


def _parse_catalog_page(html, source, page_url):
    """Parse static career catalogs while rejecting requirement sentences."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        title = _best_role_cell(cells)
        if not title:
            continue
        context = _clean(row.get_text(" ", strip=True))
        anchor = row.find("a", href=True)
        link = urljoin(page_url, anchor.get("href", "")) if anchor else page_url
        jobs.append(_job_record(source, title, link, context))

    for heading in soup.find_all(["h2", "h3", "h4", "h5", "h6"]):
        title = _clean(heading.get_text(" ", strip=True))
        if not _looks_like_job_title(title):
            continue

        container = heading.find_parent(["article", "section", "div", "li"])
        context = _clean(container.get_text(" ", strip=True) if container else title)
        anchor = heading.find("a", href=True) or (
            container.find("a", href=True) if container else None
        )
        link = urljoin(page_url, anchor.get("href", "")) if anchor else page_url
        jobs.append(_job_record(source, title, link, context))

    for item in soup.find_all("li"):
        title = _clean(item.get_text(" ", strip=True))
        if not _looks_like_job_title(title):
            continue
        anchor = item.find("a", href=True)
        link = urljoin(page_url, anchor.get("href", "")) if anchor else page_url
        jobs.append(_job_record(source, title, link, title))

    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True))
        if not _looks_like_job_title(title):
            continue
        link = urljoin(page_url, anchor.get("href", ""))
        parent = anchor.find_parent(["tr", "li", "article", "section", "div"])
        context = _clean(parent.get_text(" ", strip=True) if parent else title)
        jobs.append(_job_record(source, title, link, context))

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

        if not _looks_like_job_title(title):
            continue

        jobs.append(_job_record(source, title, page_url, text))

    return _dedupe(jobs)


def fetch_catalog_jobs(source):
    html, page_url = _request_html(source["url"])
    return _parse_catalog_page(html, source, page_url)


def _parse_smartrecruiters_page(html, source, page_url):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    current_location = ""

    for node in soup.find_all(["h3", "a"]):
        if node.name == "h3":
            heading = _clean(node.get_text(" ", strip=True))
            current_location = heading if VIETNAM_LOCATION_PATTERN.search(heading) else ""
            continue

        if not current_location:
            continue

        href = _clean(node.get("href", ""))
        title = _clean(node.get_text(" ", strip=True))
        if not href or not title:
            continue

        url = urljoin(page_url, href)
        if "jobs.smartrecruiters.com" not in urlparse(url).netloc.lower():
            continue

        title = re.sub(
            r"\s+(?:Full[- ]time|Part[- ]time|Contract|Intern)$",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()

        if not _looks_like_job_title(title):
            continue

        jobs.append(
            _job_record(
                source,
                title,
                url,
                f"{title} {current_location}",
                location=_extract_location(current_location, current_location),
            )
        )

    return _dedupe(jobs)


def fetch_smartrecruiters_jobs(source):
    html, page_url = _request_html(source["url"])
    return _parse_smartrecruiters_page(html, source, page_url)


def fetch_ttc_jobs(source):
    """Fetch TalentTech/TTC Portals jobs through its public JSON listing feed."""
    json_url = source.get("json_url", urljoin(source["url"], "/search/jobs.json"))
    jobs = []
    page = 1
    max_pages = int(source.get("max_pages", 10))

    while page <= max_pages:
        response = _browser_get(
            json_url,
            params={"page": page},
            accept="application/json",
            referer=source.get("referer", source["url"]),
        )
        payload = response.json()
        entries = payload.get("entries") or []

        for entry in entries:
            title = _clean(entry.get("title", ""))
            location = _clean(entry.get("location", ""))
            permalink = _clean(entry.get("permalink", ""))

            if not title or not permalink or not VIETNAM_LOCATION_PATTERN.search(location):
                continue

            link = permalink if permalink.startswith("http") else urljoin(source["url"], permalink)
            jobs.append({
                "source": source["name"],
                "source_url": source["url"],
                "company": source["company"],
                "title": title,
                "link": link,
                "location": location,
                "country": "",
                "posted": _clean(entry.get("date_posted", entry.get("posted", ""))),
                "summary": _clean(entry.get("description", entry.get("summary", ""))),
                "context": " ".join([
                    title,
                    location,
                    _clean(entry.get("category", "")),
                    _clean(entry.get("description", "")),
                ]),
                "assume_vietnam": False,
                "skip_detail_fetch": False,
            })

        if not entries:
            break

        current_page = payload.get("current_page", page)
        per_page = payload.get("per_page", len(entries))
        total_entries = payload.get("total_entries")
        try:
            seen = int(current_page) * int(per_page)
        except (TypeError, ValueError):
            seen = page * len(entries)

        if isinstance(total_entries, int) and seen >= total_entries:
            break
        if len(entries) < int(per_page or len(entries)):
            break
        page += 1

    return _dedupe(jobs)


def fetch_ampere_jobs(source):
    """Fetch Ampere's official HCMC page, with rendered-text fallback."""
    city_url = "https://careers.amperecomputing.com/search/jobs/in/ho-chi-minh-city"

    try:
        response = _browser_get(city_url, accept="text/html", referer=source["url"])
        jobs = _parse_html_job_page(response.text, source, city_url)
        for job in jobs:
            if not job.get("location"):
                job["location"] = "Ho Chi Minh City, Vietnam"
        if jobs:
            return _dedupe(jobs)
    except Exception as error:
        print(f"[AMPERE DIRECT WARNING] {error}")

    try:
        markdown = _proxy_markdown(city_url)
        return _parse_markdown_job_links(
            markdown,
            source,
            city_url,
            default_location="Ho Chi Minh City, Vietnam",
        )
    except requests.RequestException as error:
        print(f"[AMPERE FALLBACK WARNING] {error}")
        return []


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
                headers={**HEADERS, "Content-Type": "application/json"},
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
                location = _clean(posting.get("locationsText", posting.get("location", "")))
                path = _clean(posting.get("externalPath", ""))
                if not title or not path:
                    continue

                link = (
                    f"https://{host}/en-US/{site}{path}"
                    if path.startswith("/")
                    else urljoin(source["url"], path)
                )
                detail_api_url = (
                    f"https://{host}/wday/cxs/{tenant}/{site}{path}"
                    if path.startswith("/")
                    else ""
                )
                jobs.append({
                    "source": source["name"],
                    "source_url": source["url"],
                    "company": source["company"],
                    "title": title,
                    "link": link,
                    "detail_api_url": detail_api_url,
                    "location": location,
                    "country": "",
                    "posted": _clean(posting.get("postedOn", "")),
                    "summary": "",
                    "context": " ".join([
                        title,
                        location,
                        _clean(posting.get("bulletFields", "")),
                    ]),
                    "assume_vietnam": False,
                    "skip_detail_fetch": False,
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
            if source.get("name") == "Ampere Computing Vietnam Careers":
                source_jobs = fetch_ampere_jobs(source)
            elif source["type"] == "workday":
                source_jobs = fetch_workday_jobs(source)
            elif source["type"] == "ttc_jobs":
                source_jobs = fetch_ttc_jobs(source)
            elif source["type"] == "smartrecruiters_jobs":
                source_jobs = fetch_smartrecruiters_jobs(source)
            elif source["type"] == "html_jobs":
                source_jobs = fetch_html_jobs(source)
            elif source["type"] == "query_html_jobs":
                source_jobs = fetch_query_html_jobs(source)
            elif source["type"] == "catalog_jobs":
                source_jobs = fetch_catalog_jobs(source)
            else:
                print(f"[UNKNOWN JOB SOURCE TYPE] {source['type']}")
                continue

            print(f"[JOB RESULT] {source['name']} | {len(source_jobs)} candidates")
            jobs.extend(source_jobs)

        except Exception as error:
            print(f"[JOB ERROR] {source['name']} | {error}")

    return _dedupe(jobs)
