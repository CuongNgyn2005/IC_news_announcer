import html
import json
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

TITLE_SENIORITY_RULES = (
    (r"\bstaff\s+to\s+senior\s+staff\b", "Staff / Senior Staff"),
    (r"\bsenior\s*/\s*staff\b|\bsr\.?\s*/\s*staff\b", "Senior / Staff"),
    (r"\bsenior\s+staff\b|\bsr\.?\s+staff\b", "Senior Staff"),
    (r"\bsenior\s+principal\b|\bsr\.?\s+principal\b", "Senior Principal"),
    (r"\bintern(?:ship)?\b|\btrainee\b", "Intern / Trainee"),
    (r"\bnew grad(?:uate)?\b|\bgraduate\b|\bfresher\b|\bentry[- ]level\b", "Graduate / Entry Level"),
    (r"\bjunior\b|\bjr\.?\b", "Junior"),
    (r"\bprincipal\b", "Principal"),
    (r"\bstaff\b", "Staff"),
    (r"\bmanager\b", "Manager"),
    (r"\blead\b", "Lead"),
    (r"\bsenior\b|\bsr\.?\b", "Senior"),
    (r"\bmid[- ]level\b|\bintermediate\b", "Mid Level"),
    (r"\bexperienced\b", "Experienced"),
)

YEAR_AMOUNT = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
YEAR_UNIT = r"(?:years?|yrs?)"

# Experience wording varies heavily across career systems. These patterns are
# intentionally requirement-oriented rather than generic year matching, so a
# company's age or a product year is not treated as candidate experience.
EXPERIENCE_PATTERNS = (
    re.compile(
        rf"\b({YEAR_AMOUNT})\s*(?:-|–|—|to)\s*({YEAR_AMOUNT})\s*{YEAR_UNIT}"
        rf"(?:\s+of)?(?:\s+(?:relevant|professional|industry|hands[- ]on|working|work))*\s+experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:(?:at least|min(?:imum)?(?: of)?|more than|over|from)\s*)?"
        rf"({YEAR_AMOUNT})\s*(?:\+|plus)?\s*{YEAR_UNIT}(?:\s+of)?"
        rf"(?:\s+(?:relevant|professional|industry|hands[- ]on|working|work))*\s+experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bexperience\s*(?:required|requirement)?\s*(?:of|:|-)?\s*"
        rf"({YEAR_AMOUNT})\s*(?:\+|plus)?\s*{YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:at least|min(?:imum)?(?: of)?|more than|over|from)\s+"
        rf"({YEAR_AMOUNT})\s*(?:\+|plus)?\s*{YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({YEAR_AMOUNT})\s*(?:\+|plus)\s*{YEAR_UNIT}\s+(?:of|in|with)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({YEAR_AMOUNT})\s*(?:-|–|—|to)\s*({YEAR_AMOUNT})\s*{YEAR_UNIT}"
        rf"\s+(?:of|in|with)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:have|has|with|requires?|requiring|preferred)\s+(?:at least\s+)?"
        rf"({YEAR_AMOUNT})\s*(?:\+|plus)?\s*{YEAR_UNIT}\s+(?:of|in|with)\b",
        re.IGNORECASE,
    ),
    # Compact title/listing forms such as "RTL Engineer (3-5 yrs)".
    re.compile(
        rf"\b({YEAR_AMOUNT})\s*(?:-|–|—|to)\s*({YEAR_AMOUNT})\s*{YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({YEAR_AMOUNT})\s*(?:\+|plus)\s*{YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
)

NO_EXPERIENCE_PATTERNS = (
    re.compile(r"\bno\s+(?:prior\s+|previous\s+)?experience\s+(?:is\s+)?required\b", re.IGNORECASE),
    re.compile(r"\bfresh\s+graduates?\s+(?:are\s+)?(?:welcome|encouraged|accepted)\b", re.IGNORECASE),
    re.compile(r"\bfreshers?\s+(?:are\s+)?(?:welcome|encouraged|accepted)\b", re.IGNORECASE),
)

EXPERIENCE_CONTEXT_TERMS = (
    "experience", "required", "requirement", "preferred", "qualification",
    "candidate", "must have", "hands-on", "hands on", "working in",
    "work in", "design", "verification", "validation", "rtl", "asic",
    "soc", "layout", "physical design", "dft", "fpga", "engineering",
)

ENGLISH_PATTERNS = (
    re.compile(r"\bIELTS\b[^\n.;]{0,45}", re.IGNORECASE),
    re.compile(r"\bTOEIC\b[^\n.;]{0,45}", re.IGNORECASE),
    re.compile(r"\bTOEFL\b[^\n.;]{0,45}", re.IGNORECASE),
)

QUALIFICATION_TERMS = (
    "bachelor", "master", "phd", "degree", "systemverilog", "verilog",
    "uvm", "vhdl", "rtl", "asic", "soc", "cadence", "synopsys",
    "primetime", "innovus", "virtuoso", "spectre", "calibre",
    "place and route", "static timing", "sta", "dft", "atpg", "mbist",
    "analog layout", "custom layout",
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
    headers = {**HEADERS, "Accept": accept, "Referer": referer or url}
    if curl_requests is not None:
        response = curl_requests.get(url, headers=headers, timeout=20, impersonate="chrome")
        response.raise_for_status()
        return response
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response


def _jobposting_jsonld_text(soup):
    pieces = []

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return

        item_type = value.get("@type", "")
        types = item_type if isinstance(item_type, list) else [item_type]
        if any(str(item).lower() == "jobposting" for item in types):
            for key in (
                "title",
                "description",
                "experienceRequirements",
                "qualifications",
                "skills",
                "responsibilities",
            ):
                item = value.get(key)
                if item:
                    pieces.append(_html_to_text(item))

            location = value.get("jobLocation")
            if location:
                pieces.append(_clean(json.dumps(location, ensure_ascii=False)))

        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in value:
                visit(value[key])

    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            visit(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

    return _clean(" ".join(piece for piece in pieces if piece))


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
            info.get("experienceRequirements", ""),
            info.get("qualifications", ""),
            info.get("timeType", ""),
        ]
        return _clean(" ".join(_html_to_text(piece) for piece in pieces))[:30000]

    soup = BeautifulSoup(response.text, "html.parser")
    structured = _jobposting_jsonld_text(soup)
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    visible = _clean(root.get_text(". ", strip=True))
    return _clean(f"{visible} {structured}")[:30000]


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
            response = _browser_get(url, accept=accept, referer=job.get("source_url") or job.get("link"))
            text = _extract_page_text(response)
            if len(text) >= 80:
                return text
        except Exception:
            continue

    # Some career sites block direct GitHub-runner requests while still being
    # publicly readable. Use a rendered-text fallback only after direct detail
    # retrieval failed; the alert link remains the employer's original URL.
    link = str(job.get("link", "") or "")
    if link.startswith("http"):
        try:
            response = requests.get("https://r.jina.ai/" + link, headers=HEADERS, timeout=15)
            response.raise_for_status()
            text = _clean(response.text)
            if len(text) >= 80:
                return text[:30000]
        except requests.RequestException:
            pass

    return ""


def extract_city(text):
    normalized = _clean(text)
    cities = []
    for pattern, city in CITY_RULES:
        if re.search(pattern, normalized, flags=re.IGNORECASE) and city not in cities:
            cities.append(city)
    return " / ".join(cities)


def extract_seniority(title, text=""):
    del text
    normalized_title = _clean(title)
    for pattern, level in TITLE_SENIORITY_RULES:
        if re.search(pattern, normalized_title, flags=re.IGNORECASE):
            return level
    return "Not stated"


def _sentence_candidates(text):
    cleaned = _clean(text)
    return [
        sentence.strip(" -•\t")
        for sentence in re.split(r"(?<=[.!?])\s+|\s*[•▪●]\s*", cleaned)
        if len(sentence.strip()) >= 12
    ]


def _looks_like_experience_requirement(sentence):
    lower = sentence.lower()
    return any(term in lower for term in EXPERIENCE_CONTEXT_TERMS)


def extract_experience(text):
    cleaned = _clean(text)
    sentences = _sentence_candidates(cleaned)

    for sentence in sentences:
        if any(pattern.search(sentence) for pattern in NO_EXPERIENCE_PATTERNS):
            return sentence[:220]

    # Prefer a complete requirement sentence because it preserves useful
    # qualifiers such as "at least", the domain, and whether it is preferred.
    for sentence in sentences:
        if not _looks_like_experience_requirement(sentence):
            continue
        if any(pattern.search(sentence) for pattern in EXPERIENCE_PATTERNS):
            return sentence[:220]

    # Fallback for pages whose HTML flattening removed sentence boundaries.
    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        start = max(0, match.start() - 90)
        end = min(len(cleaned), match.end() + 140)
        window = cleaned[start:end].strip()
        if _looks_like_experience_requirement(window):
            return window[:220]

    return "Not stated"


def extract_english_requirement(text):
    cleaned = _clean(text)
    for pattern in ENGLISH_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return _clean(match.group(0))[:180]
    for sentence in _sentence_candidates(cleaned):
        lower = sentence.lower()
        if "english" in lower and any(term in lower for term in ("fluent", "fluency", "proficient", "proficiency", "communication", "communicate", "written", "spoken", "speaking")):
            return sentence[:220]
    return "Not stated"


def extract_qualifications(text, limit=4):
    chosen = []
    for sentence in _sentence_candidates(text):
        lower = sentence.lower()
        if not any(term in lower for term in QUALIFICATION_TERMS) or sentence in chosen:
            continue
        chosen.append(sentence[:220])
        if len(chosen) >= limit:
            break
    return chosen


def extract_job_requirements(title, location, text):
    # Career search titles often include the exact city. Prefer that first,
    # then the listing location, and only then the broad detail page.
    title_city = extract_city(title)
    location_city = extract_city(location)
    city = title_city or location_city or extract_city(text)

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
    existing_context = _clean(" ".join([
        enriched.get("title", ""),
        enriched.get("location", ""),
        enriched.get("summary", ""),
        enriched.get("context", ""),
    ]))
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
