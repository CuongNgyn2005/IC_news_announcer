"""Production routing for job sources.

This wrapper keeps source failures isolated, fixes known source-specific URLs, and
avoids spending several minutes retrying JS-only career portals on every run.
"""

import re
from urllib.parse import urljoin

import requests

from collectors.jobs import (
    HEADERS,
    ROLE_DISCOVERY_TERMS,
    WORKDAY_SEARCH_TERMS,
    _dedupe,
    _extract_location,
    _job_record,
    _looks_like_job_title,
    _parse_html_job_page,
    _parse_markdown_job_links,
    _request_html,
    fetch_ampere_jobs,
    fetch_catalog_jobs,
    fetch_html_jobs,
    fetch_smartrecruiters_jobs,
    fetch_ttc_jobs,
    fetch_workday_jobs,
)
from config.sources import JOB_SOURCES


SOURCE_URL_OVERRIDES = {
    "BOS Semiconductors Vietnam Careers": "https://bossemiconductors.jobday.vn/",
}

# This official page is a 2022-2023 campaign and should never be emitted as a
# current vacancy merely because the page remains online.
STALE_SOURCE_NAMES = {
    "Viettel High Tech SoC Careers",
}

RENDERED_FALLBACK_TERMS = {
    "HCLTech Vietnam Careers": (
        "FPGA",
        "Verilog",
        "UVM",
        "RTL",
    ),
    "Infineon Vietnam Careers": (
        "physical design",
        "verification",
        "layout",
    ),
}


def _source_with_overrides(source):
    prepared = dict(source)
    override = SOURCE_URL_OVERRIDES.get(source.get("name"))
    if override:
        prepared["url"] = override
        prepared["source_url"] = override
    return prepared


def _rendered_markdown(url):
    response = requests.get(
        "https://r.jina.ai/" + url,
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    return response.text


def _markdown_links(text):
    return list(re.finditer(r"\[([^\]\n]{3,180})\]\((https?://[^)\s]+|/[^)\s]+)\)", text or ""))


def _parse_hcl_rendered(text, source):
    """Parse HCLTech search output where the title itself may be generic."""
    jobs = []
    for match in _markdown_links(text):
        title = re.sub(r"\s+Job Details\s*$", "", match.group(1), flags=re.I).strip()
        link = urljoin(source["url"], match.group(2))
        if "careers.hcltech.com/job/" not in link.lower():
            continue

        start = max(0, match.start() - 420)
        end = min(len(text), match.end() + 650)
        context = re.sub(r"\s+", " ", text[start:end]).strip()
        lower_context = context.lower()
        if not any(term in lower_context for term in ROLE_DISCOVERY_TERMS):
            continue

        location = _extract_location(context, "")
        if not location and "viet nam" not in lower_context and "vietnam" not in lower_context:
            continue

        jobs.append(_job_record(source, title, link, context, location=location or "Vietnam"))
    return _dedupe(jobs)


def fetch_hcl_jobs(source):
    jobs = []
    for term in RENDERED_FALLBACK_TERMS["HCLTech Vietnam Careers"]:
        params = {
            source.get("query_param", "q"): term,
            source.get("location_param", "locationsearch"): "Vietnam",
        }
        prepared_url = requests.Request("GET", source["url"], params=params).prepare().url
        try:
            markdown = _rendered_markdown(prepared_url)
            jobs.extend(_parse_hcl_rendered(markdown, source))
        except requests.RequestException as error:
            print(f"[HCL RENDER WARNING] {term} | {error}")
    return _dedupe(jobs)


def fetch_gsme_jobs(source):
    """Parse GSME's heading/location/More Info cards from its public page."""
    try:
        markdown = _rendered_markdown(source["url"])
    except requests.RequestException as error:
        print(f"[GSME RENDER WARNING] {error}")
        return []

    jobs = []
    heading_pattern = re.compile(r"^#{3,6}\s+(.+?)\s*$", re.MULTILINE)
    headings = list(heading_pattern.finditer(markdown))

    for index, heading in enumerate(headings):
        title = heading.group(1).strip()
        if not _looks_like_job_title(title):
            continue

        next_start = headings[index + 1].start() if index + 1 < len(headings) else min(len(markdown), heading.end() + 1200)
        block = markdown[heading.end():next_start]

        # The location is commonly the next heading, so also inspect a wider
        # window through the following two headings.
        wider_end = headings[index + 2].start() if index + 2 < len(headings) else min(len(markdown), heading.end() + 1600)
        window = markdown[heading.end():wider_end]
        location = _extract_location(window, "")
        if not location:
            continue

        link_match = re.search(r"\[More Info\]\((https?://[^)]+)\)", window, flags=re.I)
        if not link_match:
            link_match = re.search(r"(https://www\.gsme\.com/job-listings/[A-Za-z0-9_?&=./%-]+)", window)
        link = link_match.group(1) if link_match else source["url"]

        jobs.append(_job_record(source, title, link, f"{title} {window}", location=location))

    return _dedupe(jobs)


def fetch_query_html_jobs_fast(source):
    jobs = []

    for term in source.get("search_terms", WORKDAY_SEARCH_TERMS):
        params = {source.get("query_param", "q"): term}
        location_param = source.get("location_param")
        if location_param:
            params[location_param] = source.get("country_filter", "Vietnam")

        try:
            html, page_url = _request_html(source["url"], params=params)
            jobs.extend(_parse_html_job_page(html, source, page_url))
        except requests.RequestException as error:
            print(f"[JOB QUERY WARNING] {source['name']} | {term} | {error}")

    jobs = _dedupe(jobs)
    if jobs:
        return jobs

    terms = RENDERED_FALLBACK_TERMS.get(
        source.get("name"),
        tuple(source.get("search_terms", WORKDAY_SEARCH_TERMS))[:2],
    )

    for term in terms:
        params = {source.get("query_param", "q"): term}
        location_param = source.get("location_param")
        if location_param:
            params[location_param] = source.get("country_filter", "Vietnam")

        prepared_url = requests.Request("GET", source["url"], params=params).prepare().url
        try:
            markdown = _rendered_markdown(prepared_url)
            jobs.extend(
                _parse_markdown_job_links(
                    markdown,
                    source,
                    source["url"],
                    default_location=source.get("default_location", ""),
                )
            )
        except requests.RequestException as error:
            print(f"[JOB RENDER WARNING] {source['name']} | {term} | {error}")

    return _dedupe(jobs)


def fetch_jobs():
    jobs = []

    for raw_source in JOB_SOURCES:
        if not raw_source.get("enabled", False):
            continue

        source = _source_with_overrides(raw_source)

        if source.get("name") in STALE_SOURCE_NAMES:
            print(f"\n[JOB SOURCE SKIP] {source['name']} | official posting is expired")
            continue

        print(f"\n[JOB FETCH] {source['name']} ({source['type']})")

        try:
            if source.get("name") == "Ampere Computing Vietnam Careers":
                source_jobs = fetch_ampere_jobs(source)
            elif source.get("name") == "HCLTech Vietnam Careers":
                source_jobs = fetch_hcl_jobs(source)
            elif source.get("name") == "GSME Vietnam Careers":
                source_jobs = fetch_gsme_jobs(source)
            elif source["type"] == "workday":
                source_jobs = fetch_workday_jobs(source)
            elif source["type"] == "ttc_jobs":
                source_jobs = fetch_ttc_jobs(source)
            elif source["type"] == "smartrecruiters_jobs":
                source_jobs = fetch_smartrecruiters_jobs(source)
            elif source["type"] == "html_jobs":
                source_jobs = fetch_html_jobs(source)
            elif source["type"] == "query_html_jobs":
                source_jobs = fetch_query_html_jobs_fast(source)
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
