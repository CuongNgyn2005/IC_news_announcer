"""Production routing for job sources.

This wrapper keeps source failures isolated, fixes known source-specific URLs, and
avoids spending several minutes retrying JS-only career portals on every run.
"""

from urllib.parse import urljoin

import requests

from collectors.jobs import (
    HEADERS,
    WORKDAY_SEARCH_TERMS,
    _dedupe,
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


# These public pages are authoritative entry points even when the older
# marketing URL in config redirects or no longer exposes the vacancies.
SOURCE_URL_OVERRIDES = {
    "BOS Semiconductors Vietnam Careers": "https://bossemiconductors.jobday.vn/",
}


# Only use a few rendered searches after the ordinary HTML queries return no
# jobs. This bounds a blocked/JS-only source to seconds rather than minutes.
RENDERED_FALLBACK_TERMS = {
    "HCLTech Vietnam Careers": (
        "design verification",
        "fpga",
        "rtl",
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


def fetch_query_html_jobs_fast(source):
    """Query server-rendered results first, then a bounded render fallback."""
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
            print(
                f"[JOB QUERY WARNING] {source['name']} | {term} | {error}"
            )

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

        prepared_url = requests.Request(
            "GET",
            source["url"],
            params=params,
        ).prepare().url

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
            print(
                f"[JOB RENDER WARNING] {source['name']} | {term} | {error}"
            )

    return _dedupe(jobs)


def fetch_jobs():
    jobs = []

    for raw_source in JOB_SOURCES:
        if not raw_source.get("enabled", False):
            continue

        source = _source_with_overrides(raw_source)
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
                source_jobs = fetch_query_html_jobs_fast(source)
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

        except Exception as error:
            print(f"[JOB ERROR] {source['name']} | {error}")

    return _dedupe(jobs)
