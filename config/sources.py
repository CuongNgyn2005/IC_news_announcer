NEWS_SOURCES = [
    # ============================================================
    # GENERAL IC / SEMICONDUCTOR NEWS
    # ============================================================

    {
        "name": "EE Times",
        "company": None,
        "category": "industry_news",
        "type": "rss",
        "url": "https://www.eetimes.com/feed/",
        "enabled": True,
        "priority": 2,
    },
    {
        "name": "IEEE Spectrum",
        "company": None,
        "category": "industry_news",
        "type": "rss",
        "url": "https://spectrum.ieee.org/feeds/feed.rss",
        "enabled": True,
        "priority": 2,
    },

    # Marvell rejects simple scraper requests with HTTP 403. Google
    # News RSS gives us indexed Marvell newsroom URLs while still
    # linking users to Marvell's original articles.
    {
        "name": "Marvell Newsroom",
        "company": "Marvell",
        "category": "company_product",
        "type": "rss",
        "url": (
            "https://news.google.com/rss/search?"
            "q=site%3Amarvell.com%2Fcompany%2Fnewsroom+"
            "Marvell+semiconductor+when%3A30d"
            "&hl=en-US&gl=US&ceid=US%3Aen"
        ),
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Ampere Computing Newsroom",
        "company": "Ampere Computing",
        "category": "company_product",
        "type": "company",
        "url": "https://amperecomputing.com/company/newsroom",
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "SkyeChip Media Releases",
        "company": "SkyeChip",
        "category": "company_product",
        "type": "html",
        "url": "https://skyechip.com/category/media-release/",
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "HCLTech Semiconductor",
        "company": "HCLTech",
        "category": "company_product",
        "type": "rss",
        "url": (
            "https://news.google.com/rss/search?"
            "q=site%3Ahcltech.com%2Fpress-releases+HCLTech+"
            "%28semiconductor+OR+silicon+OR+chip%29+when%3A365d"
            "&hl=en-US&gl=US&ceid=US%3Aen"
        ),
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Truechip",
        "company": "Truechip",
        "category": "company_product",
        "type": "truechip",
        "url": "https://www.truechip.net/",
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Infineon Technology News",
        "company": "Infineon Technologies",
        "category": "company_product",
        "type": "html",
        "url": "https://www.infineon.com/about/press/technology-news",
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "FPT Semiconductor News",
        "company": "FPT Semiconductor",
        "category": "company_product",
        "type": "rss",
        "url": (
            "https://news.google.com/rss/search?"
            "q=site%3Afpt-semiconductor.com+%22FPT+Semiconductor%22+"
            "%28chip+OR+semiconductor+OR+IC%29+when%3A90d"
            "&hl=en-US&gl=US&ceid=US%3Aen"
        ),
        "enabled": True,
        "priority": 1,
    },

    # Ideas2Silicon currently exposes technology and careers pages but
    # no stable official news feed. Keep this disabled rather than poll
    # a known-empty feed.
    {
        "name": "Ideas2Silicon News",
        "company": "Ideas2Silicon",
        "category": "company_product",
        "type": "html",
        "url": "https://www.ideas2silicon.com/technology.html",
        "enabled": False,
        "priority": 1,
    },

    # Additional industry sources retained for later news expansion.
    {
        "name": "Synopsys",
        "company": "Synopsys",
        "category": "company_product",
        "type": "html",
        "url": "https://news.synopsys.com/",
        "enabled": False,
        "priority": 2,
    },
    {
        "name": "Cadence",
        "company": "Cadence",
        "category": "company_product",
        "type": "html",
        "url": "https://www.cadence.com/en_US/home.html",
        "enabled": False,
        "priority": 2,
    },
    {
        "name": "imec",
        "company": "imec",
        "category": "research",
        "type": "html",
        "url": "https://www.imec-int.com/en/imec-press-releases",
        "enabled": False,
        "priority": 2,
    },
    {
        "name": "Semiconductor Engineering",
        "company": None,
        "category": "industry_news",
        "type": "html",
        "url": "https://semiengineering.com/",
        "enabled": False,
        "priority": 2,
    },
]


# ============================================================================
# VIETNAM IC / SEMICONDUCTOR JOB SOURCES
#
# Sources are deliberately company-first instead of relying on generic job
# boards. The final filter still requires Vietnam evidence and a target IC role.
# Static pages with old vacancies are safe on GitHub Actions because the first
# persistent run baselines existing accepted items instead of announcing them.
# ============================================================================

JOB_SOURCES = [
    {
        "name": "Marvell Vietnam Careers",
        "company": "Marvell",
        "type": "workday",
        "url": "https://marvell.wd1.myworkdayjobs.com/MarvellCareers",
        "workday_tenant": "marvell",
        "workday_site": "MarvellCareers",
        "country_filter": "Vietnam",
        "search_terms": [
            "design verification",
            "rtl",
            "logic design",
            "physical design",
            "layout",
            "analog design",
            "dft",
            "silicon validation",
            "fpga",
        ],
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Ampere Computing Vietnam Careers",
        "company": "Ampere Computing",
        "type": "ttc_jobs",
        "url": "https://careers.amperecomputing.com/",
        "json_url": "https://careers.amperecomputing.com/search/jobs.json",
        "referer": "https://careers.amperecomputing.com/search/jobs",
        "country_filter": "Vietnam",
        "max_pages": 10,
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "SkyeChip Careers",
        "company": "SkyeChip",
        "type": "catalog_jobs",
        "url": "https://skyechip.com/career-opportunities/",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "HCLTech Vietnam Careers",
        "company": "HCLTech",
        "type": "query_html_jobs",
        "url": "https://careers.hcltech.com/search/",
        "query_param": "q",
        "location_param": "locationsearch",
        "country_filter": "Vietnam",
        "search_terms": [
            "design verification",
            "systemverilog",
            "rtl",
            "physical design",
            "analog",
            "dft",
            "silicon validation",
            "fpga",
        ],
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Truechip Careers",
        "company": "Truechip",
        "type": "catalog_jobs",
        "url": "https://www.truechip.net/explore-careers",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Infineon Vietnam Careers",
        "company": "Infineon Technologies",
        "type": "query_html_jobs",
        "url": "https://jobs.infineon.com/careers",
        "query_param": "query",
        "location_param": "location",
        "country_filter": "Vietnam",
        "search_terms": [
            "verification",
            "physical design",
            "layout",
            "analog",
            "digital design",
            "rtl",
            "dft",
            "validation",
        ],
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Ideas2Silicon Careers",
        "company": "Ideas2Silicon",
        "type": "catalog_jobs",
        "url": "https://www.ideas2silicon.com/career.html",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },

    # Major foreign IC/EDA design centres with current Vietnam openings.
    {
        "name": "Synopsys Vietnam Careers",
        "company": "Synopsys",
        "type": "html_jobs",
        "url": "https://careers.synopsys.com/jobs-in-vietnam",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Qorvo Engineering Careers",
        "company": "Qorvo",
        "type": "html_jobs",
        "url": "https://careers.qorvo.com/go/Engineering-Careers/8587200/",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Renesas Vietnam Careers",
        "company": "Renesas Electronics",
        "type": "smartrecruiters_jobs",
        "url": (
            "https://careers.smartrecruiters.com/"
            "RenesasElectronics?search=Vietnam"
        ),
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Cadence Careers",
        "company": "Cadence",
        "type": "workday",
        "url": "https://cadence.wd1.myworkdayjobs.com/External_Careers",
        "workday_tenant": "cadence",
        "workday_site": "External_Careers",
        "country_filter": "Vietnam",
        "search_terms": [
            "physical design",
            "design verification",
            "rtl",
            "layout",
            "analog",
            "dft",
            "application engineer",
        ],
        "enabled": True,
        "priority": 2,
    },

    # Vietnam-headquartered / Vietnam-specific IC design teams.
    {
        "name": "FPT Semiconductor Careers",
        "company": "FPT Semiconductor",
        "type": "catalog_jobs",
        "url": "https://fpt-semiconductor.com/careers/",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Faraday Technology Vietnam Careers",
        "company": "Faraday Technology",
        "type": "catalog_jobs",
        "url": "https://www.faraday-tech.com/en/content/Careers/RecruitingVietnam",
        "country_filter": "Vietnam",
        "default_location": "Ho Chi Minh City, Vietnam",
        "assume_vietnam": True,
        "detail_fetch": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Viettel High Tech SoC Careers",
        "company": "Viettel High Tech",
        "type": "catalog_jobs",
        "url": "https://viettelhightech.com/en/tuyen-dung/soc-design-engineer",
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "detail_fetch": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "Quy Nhon Semiconductor Careers",
        "company": "Quy Nhon Semiconductor",
        "type": "catalog_jobs",
        "url": "https://qnsc.vn/",
        "country_filter": "Vietnam",
        "default_location": "Quy Nhon, Vietnam",
        "assume_vietnam": True,
        "detail_fetch": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "NBIV Semiconductor Careers",
        "company": "NBIV",
        "type": "catalog_jobs",
        "url": "https://nbiv.com.vn/development/",
        "country_filter": "Vietnam",
        "default_location": "Ho Chi Minh City, Vietnam",
        "assume_vietnam": True,
        "detail_fetch": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "BOS Semiconductors Vietnam Careers",
        "company": "BOS Semiconductors",
        "type": "catalog_jobs",
        "url": "https://www.bos-semi.com/careers-vietnam",
        "country_filter": "Vietnam",
        "default_location": "Ho Chi Minh City, Vietnam",
        "assume_vietnam": True,
        "detail_fetch": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "CoAsia SEMI Employment",
        "company": "CoAsia SEMI",
        "type": "html_jobs",
        "url": "https://www.coasiasemi.com/bbs/board.php?bo_table=employment",
        "job_url_hints": ["bo_table=employment&wr_id="],
        "country_filter": "Vietnam",
        "default_location": "",
        "assume_vietnam": False,
        "enabled": True,
        "priority": 2,
    },
]
