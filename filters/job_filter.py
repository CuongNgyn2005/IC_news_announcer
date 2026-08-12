import re


TARGET_ROLE_RULES = {
    "Design Verification": {
        "design verification": 10,
        "verification engineer": 9,
        "soc verification": 10,
        "ip verification": 10,
        "functional verification": 9,
        "pre-silicon verification": 10,
        "rtl verification": 9,
        "verification & validation": 7,
        "verification and validation": 7,
        "uvm": 6,
        "systemverilog": 5,
    },
    "RTL / Logic Design": {
        "rtl design": 10,
        "rtl designer": 10,
        "rtl engineer": 10,
        "logic design": 10,
        "logic engineer": 9,
        "digital design": 8,
        "soc design": 8,
        "front-end design": 8,
        "frontend design": 8,
        "microarchitecture": 8,
        "microarchitect": 8,
        "verilog": 5,
        "vhdl": 5,
    },
    "Physical Design": {
        "physical design": 10,
        "physical implementation": 9,
        "backend implementation": 9,
        "design implementation": 9,
        "place and route": 9,
        "place-and-route": 9,
        "p&r": 8,
        "timing closure": 8,
        "static timing analysis": 8,
        "floorplan": 7,
        "floorplanning": 7,
        "sta engineer": 8,
    },
    "Analog / Custom Layout": {
        "analog layout": 10,
        "custom layout": 10,
        "mask design": 10,
        "layout design": 9,
        "layout engineer": 9,
        "analog design": 8,
        "analog mixed signal": 9,
        "analog mixed-signal": 9,
        "mixed signal": 8,
        "mixed-signal": 8,
        "circuit design": 8,
        "circuit designer": 8,
    },
    "DFT": {
        "design for test": 10,
        "dft engineer": 10,
        " dft ": 8,
        "scan engineer": 8,
        "mbist": 8,
        "atpg": 8,
    },
    "Silicon Validation": {
        "silicon validation": 10,
        "post-silicon": 10,
        "post silicon": 10,
        "hardware validation": 8,
        "phy validation": 8,
        "validation engineer": 7,
    },
    "FPGA / Emulation": {
        "fpga engineer": 8,
        "fpga design": 8,
        "emulation engineer": 8,
        "fpga prototyping": 8,
        "hardware emulation": 8,
    },
    "Design Automation / CAD": {
        "design automation": 8,
        "cad engineer": 8,
        "eda engineer": 8,
        "methodology engineer": 7,
    },
}


SEMICONDUCTOR_ANCHORS = {
    "asic",
    "soc",
    "silicon",
    "semiconductor",
    "rtl",
    "verilog",
    "systemverilog",
    "uvm",
    "vlsi",
    "chip",
    "ic design",
    "integrated circuit",
    "fpga",
    "eda",
    "cadence",
    "synopsys",
    "place and route",
    "physical design",
    "dft",
    "mbist",
    "atpg",
}


EXCLUDE_TERMS = {
    "solidworks",
    "creo",
    "mechanical design",
    "industrial design",
    "product designer",
    "graphic design",
    "ui designer",
    "ux designer",
    "web designer",
}


TRUSTED_SEMICONDUCTOR_EMPLOYERS = {
    "marvell",
    "ampere computing",
    "infineon technologies",
    "truechip",
    "skyechip",
    "ideas2silicon",
    "synopsys",
    "qorvo",
    "fpt semiconductor",
    "faraday technology",
    "renesas electronics",
    "viettel high tech",
    "quy nhon semiconductor",
    "qnsc",
    "nbiv",
    "bos semiconductors",
    "coasia semi",
    "cadence",
}


VIETNAM_TERMS = {
    "vietnam",
    "viet nam",
    "ho chi minh",
    "hcmc",
    "hcm city",
    "hanoi",
    "ha noi",
    "da nang",
    "danang",
    "quy nhon",
    "gia lai",
    "bac ninh",
    "hai phong",
    "binh duong",
    "dong nai",
    "can tho",
    "da lat",
}


def _normalize(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _contains(text, term):
    if term.startswith(" ") or term.endswith(" "):
        return term in f" {text} "

    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def is_vietnam_job(job):
    location_text = _normalize(
        " ".join(
            [
                job.get("location", ""),
                job.get("context", ""),
            ]
        )
    )

    if any(_contains(location_text, term) for term in VIETNAM_TERMS):
        return True

    return bool(job.get("assume_vietnam", False))


def classify_job(job, threshold=7, require_vietnam=True):
    """Classify IC roles; optionally postpone the Vietnam gate.

    main.py first runs this with require_vietnam=False so only potentially
    relevant IC roles incur a job-detail request. After detail enrichment it
    runs the normal Vietnam-gated classification again.
    """
    title = _normalize(job.get("title", ""))
    description = _normalize(job.get("summary", ""))
    context = _normalize(job.get("context", ""))
    text = " ".join([title, description, context])

    if not title:
        return False, None, 0, []

    if any(_contains(text, term) for term in EXCLUDE_TERMS):
        return False, None, 0, []

    best_role = None
    best_score = 0
    best_terms = []

    for role, rules in TARGET_ROLE_RULES.items():
        score = 0
        matched = []

        for term, weight in rules.items():
            if _contains(title, term):
                score += weight * 2
                matched.append(term.strip())
            elif _contains(text, term):
                score += weight
                matched.append(term.strip())

        if score > best_score:
            best_role = role
            best_score = score
            best_terms = list(dict.fromkeys(matched))

    if best_score >= threshold and best_role == "Design Verification":
        company = _normalize(job.get("company", ""))
        strong_dv = any(
            term in best_terms
            for term in (
                "soc verification",
                "ip verification",
                "rtl verification",
                "uvm",
                "systemverilog",
            )
        )

        has_ic_context = any(
            _contains(text, anchor)
            for anchor in SEMICONDUCTOR_ANCHORS
        )

        if company not in TRUSTED_SEMICONDUCTOR_EMPLOYERS:
            if not has_ic_context:
                return False, None, best_score, best_terms
        elif not strong_dv and not has_ic_context:
            if "verification engineer" not in best_terms:
                return False, None, best_score, best_terms

    if best_score < threshold:
        return False, None, best_score, best_terms

    if require_vietnam and not is_vietnam_job(job):
        return False, best_role, best_score, best_terms

    return True, best_role, best_score, best_terms
