import re


STRONG_KEYWORDS = {
    "semiconductor": 8,
    "semiconductors": 8,
    "integrated circuit": 8,
    "integrated circuits": 8,
    "chip design": 8,
    "chip designer": 7,
    "wafer": 7,
    "foundry": 8,

    "asic": 8,
    "vlsi": 8,
    "fpga": 7,

    "electronic design automation": 8,
    "design verification": 8,
    "functional verification": 8,
    "systemverilog": 8,
    "hardware-assisted verification": 8,

    "physical design": 8,
    "place and route": 8,
    "place-and-route": 8,
    "static timing analysis": 8,
    "timing closure": 7,
    "floorplanning": 7,
    "clock tree synthesis": 8,

    "analog ic": 8,
    "mixed-signal": 7,
    "mixed signal": 7,

    "finfet": 8,
    "gaafet": 8,
    "gate-all-around": 8,
    "euv lithography": 8,
    "process node": 7,

    "chiplet": 8,
    "chiplets": 8,
    "advanced packaging": 7,
    "2.5d packaging": 7,
    "3d packaging": 7,

    "risc-v": 7,
}


CONTEXT_KEYWORDS = {
    "rtl": 6,
    "soc": 6,
    "eda": 6,
    "uvm": 6,
    "cts": 5,
    "dft": 6,

    "sram": 6,
    "dram": 6,
    "hbm": 6,

    "npu": 5,
    "gpu": 3,
    "silicon": 3,
}


SEMICONDUCTOR_CONTEXT = {
    "chip",
    "chips",
    "semiconductor",
    "semiconductors",
    "asic",
    "fpga",
    "vlsi",
    "processor",
    "microprocessor",
    "microarchitecture",
    "silicon",
    "wafer",
    "foundry",
    "transistor",
    "transistors",
    "logic",
    "hardware",
    "circuit",
    "circuits",
    "eda",
    "verification",
    "rtl",
    "soc",
    "ip core",
    "chiplet",
    "packaging",
    "memory",
    "die",
}


TRUSTED_IC_COMPANIES = {
    "ampere computing",
    "marvell",
    "infineon technologies",
    "truechip",
    "skyechip",
    "ideas2silicon",
}


COMPANY_PRODUCT_TERMS = {
    "ampereone",
    "processor",
    "cpu",
    "server",
    "compute",
    "cloud",
    "data center",
    "datacenter",
    "memory",
    "interconnect",
    "pcie",
    "cxl",
    "ethernet",
    "serdes",
    "switch",
    "switching",
    "accelerator",
    "ai",
    "arm",
    "chip",
    "silicon",
    "platform",
}


def contains_term(text, term):
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


def has_semiconductor_context(text):
    return any(
        contains_term(text, term)
        for term in SEMICONDUCTOR_CONTEXT
    )


def calculate_ic_score(article):
    title = article.get("title", "")
    summary = article.get("summary", "")

    combined_text = f"{title} {summary}"

    score = 0
    matched_keywords = []

    for keyword, weight in STRONG_KEYWORDS.items():

        if contains_term(title, keyword):
            score += weight * 2
            matched_keywords.append(keyword)

        elif contains_term(summary, keyword):
            score += weight
            matched_keywords.append(keyword)

    context_available = has_semiconductor_context(combined_text)

    if context_available:
        for keyword, weight in CONTEXT_KEYWORDS.items():

            if contains_term(title, keyword):
                score += weight * 2
                matched_keywords.append(keyword)

            elif contains_term(summary, keyword):
                score += weight
                matched_keywords.append(keyword)

    matched_keywords = list(dict.fromkeys(matched_keywords))

    return score, matched_keywords


def is_trusted_company_product(article):
    company = (
        article.get("company") or ""
    ).lower()

    if company not in TRUSTED_IC_COMPANIES:
        return False, []

    text = (
        article.get("title", "") + " " +
        article.get("summary", "")
    ).lower()

    matched_terms = [
        term
        for term in COMPANY_PRODUCT_TERMS
        if contains_term(text, term)
    ]

    return len(matched_terms) > 0, matched_terms


def is_ic_related(article, threshold=8):
    score, keywords = calculate_ic_score(article)

    if score >= threshold:
        return True, score, keywords

    company_related, company_terms = is_trusted_company_product(article)

    if company_related:
        # Trusted company + relevant product/technology term.
        company_score = 10

        return (
            True,
            company_score,
            company_terms,
        )

    return False, score, keywords