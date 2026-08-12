import html
import re

import requests
from bs4 import BeautifulSoup


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


CITY_RULES = (
    (r"\bho chi minh(?: city)?\b|\bhcmc\b|\bthu duc\b", "Ho Chi Minh City"),
    (r"\bhanoi\b|\bha noi\b", "Hanoi"),
    (r"\bda nang\b|\bdanang\b", "Da Nang"),
    (r"\bquy nhon\b", "Quy Nhon"),
    (r"\bbac ninh\b", "Bac Ninh"),
    (r"\bhai phong\b", "Hai Phong"),
    (r"\bbinh duong\b", "Binh Duong"),
    (r"\bdong nai\b", "Dong Nai"),
    (r"\bcan tho\b", "Can Tho"),
    (r"\bda lat\b", "Da Lat"),
)


SENIORITY_RULES = (
    (r"\bintern(?:ship)?\b|\btrainee\b", "Intern / Trainee"),
    (r"\bnew grad(?:uate)?\b|\bgraduate\b|\bfresher\b|\bentry[- ]level\b", "Graduate / Entry Level"),
    (r"\bjunior\b|\bjr\.?\b", "Junior"),
    (r"\bprincipal\b", "Principal"),
    (r"\bstaff\b", "Staff"),
    (r"\bmanager\b", "Manager"),
    (r"\blead\b", "Lead"),
    (r"\bsenior\b|\bsr\.?\b", "Senior"),
    (r"\bmid[- ]level\b|\bintermediate\b", "Mid Level"),
)


EXPERIENCE_PATTERNS = (
    re.compile(
        r"\b(?:(?:at least|min(?:imum)?(?: of)?)\s*)?"
        r"(\d+)\s*(?:\+|plus)?\s*(?:years?|yrs?)"
        r"(?:\s+of)?(?:\s+relevant)?\s+experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*(?:years?|yrs?)"
        r"(?:\s+of)?(?:\s+relevant)?\s+experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexperience\s*(?:of|:)?\s*(\d+)\s*(?:\+|plus)?"
        r"\s*(?:years?|yrs?)\b",
        re.IGNORECASE,
    ),
)


ENGLISH_PATTERNS = (
    re.compile(r"\bIELTS\b[^\n.;]{0,45}", re.IGNORECASE),
    re.compile(r"\bTOEIC\b[^\n.;]{0,45}", re.IGNORECASE),
    re.compile(r"\bTOEFL\b[^\n.;]{0,45}", re.IGNORECASE),
)


QUALIFICATION_TERMS = (
    "bachelor",
    "master",
    "phd",
    "degree",
    "systemverilog",
    "verilog",
    "uvm",
    "vhdl",
    "rtl",
    "asic",
    "soc",
    "cadence",
    "synopsys",
    "primetime",
    "innovus",
    "virtuoso",
    "spectre",
    "calibre",
    "place and route",
    "static timing",
    "sta",
    "dft",
    "atpg",
    "mbist",
    "analog layout",
    "custom layout",
)


def _clean(text):
    text = html.unescape(str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _html_to_text(value):
    if not isinstance(value, str):
        value = str(value or "")
    soup = BeautifulSoup(value, "html.parser")
    return _clean(soup.get_text(". ", strip=True))


def _browser_get(url, accept="text/html", referer=None):
    headers = {
        **HEADERS,
        "Accept": accept,
        "Referer": referer or url,
    }

    if curl_requests is not None:
        response = curl_requests.get(
            url,
            headers=headers,
            timeout=20,
            impersonate="chrome",
        )
        response.raise_for_status()
        return response

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response


def _extract_page_text(response):
    content_type = response.headers.get("content-type", "").lower()

    if "json" in content_type:
        payload = response.json()
        info = payload.get("jobPostingInfo", payload)
        pieces = [
            info.get("title", ""),
            info.get("location", ""),
            info.get("additionalLocations", ""),
            info.get("jobDescription", ""),
            info.get("timeType", ""),
        ]
        return _clean(" ".join(_html_to_text(piece) for piece in pieces))

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    root = soup.find("main") or soup.find("article") or soup.body or soup
    return _clean(root.get_text(". ", strip=True))[:30000]


def _fetch_detail_text(job):
    if job.get("skip_detail_fetch"):
        return ""

    urls = []

    if job.get("detail_api_url"):
        urls.append((job["detail_api_url"], "application/json"))
    if job.get("link"):
        urls.append((job["link"], "text/html"))

    for url, accept in urls:
        if not str(url).startswith("http"):
            continue

        try:
            response = _browser_get(
                url,
                accept=accept,
                referer=job.get("source_url") or job.get("link"),
            )
            text = _extract_page_text(response)
            if len(text) >= 80:
                return text
        except Exception:
            continue

    return ""


def extract_city(text):
    normalized = _clean(text)
    for pattern, city in CITY_RULES:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return city
    return ""


def extract_seniority(title, text=""):
    haystack = _clean(f"{title} {text}")
    for pattern, level in SENIORITY_RULES:
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            return level
    return "Not stated"


def _sentence_candidates(text):
    cleaned = _clean(text)
    return [
        sentence.strip(" -•\t")
        for sentence in re.split(r"(?<=[.!?])\s+|\s*[•▪●]\s*", cleaned)
        if len(sentence.strip()) >= 12
    ]


def extract_experience(text):
    cleaned = _clean(text)
    sentences = _sentence_candidates(cleaned)

    for sentence in sentences:
        if "experience" not in sentence.lower():
            continue
        if any(pattern.search(sentence) for pattern in EXPERIENCE_PATTERNS):
            return sentence[:220]

    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            start = max(0, match.start() - 60)
            end = min(len(cleaned), match.end() + 80)
            return cleaned[start:end].strip()[:220]

    return "Not stated"


def extract_english_requirement(text):
    cleaned = _clean(text)

    for pattern in ENGLISH_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return _clean(match.group(0))[:180]

    for sentence in _sentence_candidates(cleaned):
        lower = sentence.lower()
        if "english" in lower and any(
            term in lower
            for term in (
                "fluent",
                "fluency",
                "proficient",
                "proficiency",
                "communication",
                "communicate",
                "written",
                "spoken",
                "speaking",
            )
        ):
            return sentence[:220]

    return "Not stated"


def extract_qualifications(text, limit=4):
    chosen = []

    for sentence in _sentence_candidates(text):
        lower = sentence.lower()
        if not any(term in lower for term in QUALIFICATION_TERMS):
            continue
        if sentence in chosen:
            continue
        chosen.append(sentence[:220])
        if len(chosen) >= limit:
            break

    return chosen


def extract_job_requirements(title, location, text):
    combined = _clean(f"{location} {text}")
    city = extract_city(combined)

    return {
        "city": city,
        "seniority": extract_seniority(title, text),
        "experience_requirement": extract_experience(text),
        "english_requirement": extract_english_requirement(text),
        "qualification_requirements": extract_qualifications(text),
    }


def enrich_job(job):
    enriched = dict(job)
    detail_text = _fetch_detail_text(enriched)
    existing_context = _clean(
        " ".join(
            [
                enriched.get("title", ""),
                enriched.get("location", ""),
                enriched.get("summary", ""),
                enriched.get("context", ""),
            ]
        )
    )
    combined = _clean(f"{existing_context} {detail_text}")

    enriched["context"] = combined[:30000]
    requirements = extract_job_requirements(
        enriched.get("title", ""),
        enriched.get("location", ""),
        combined,
    )
    enriched.update(requirements)

    if requirements["city"]:
        enriched["location"] = f"{requirements['city']}, Vietnam"

    return enriched
