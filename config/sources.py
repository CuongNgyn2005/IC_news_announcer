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

    # The direct HCLTech newsroom intermittently times out from plain
    # requests. Use a narrow RSS query so the bot gets semiconductor
    # announcements without crawling the full corporate newsroom.
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

    # Ideas2Silicon currently exposes technology and careers pages but
    # no stable official news feed. Keep this disabled instead of
    # repeatedly polling an empty Google News query.
    {
        "name": "Ideas2Silicon News",
        "company": "Ideas2Silicon",
        "category": "company_product",
        "type": "html",
        "url": "https://www.ideas2silicon.com/technology.html",
        "enabled": False,
        "priority": 1,
    },

    # Additional industry sources kept ready for later expansion.
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

    # Ampere's TTC/TalentTech HTML board returns 403 to ordinary
    # requests. Its public JSON listing feed is queried with a
    # browser-like TLS client and filtered to observed Vietnam rows.
    {
        "name": "Ampere Computing Vietnam Careers",
        "company": "Ampere Computing",
        "type": "ttc_jobs",
        "url": "https://careers.amperecomputing.com/",
        "json_url": (
            "https://careers.amperecomputing.com/"
            "search/jobs.json"
        ),
        "country_filter": "Vietnam",
        "max_pages": 10,
        "assume_vietnam": False,
        "enabled": True,
        "priority": 1,
    },

    # SkyeChip has Vietnam entities/offices, but its public careers
    # catalog does not identify which listed roles are open in Vietnam.
    # Do not label every global catalog role as Vietnam automatically.
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

    # Truechip's catalog is global and currently does not expose a
    # Vietnam location on each role, so only explicitly Vietnam-tagged
    # entries are allowed through the location gate.
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

    # The official I2S careers page is a global contact page and does
    # not list the Vietnam openings shown by I2S Vietnam social posts.
    # Keep it monitored, but never convert its global text into a
    # Vietnam job without explicit location evidence.
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
]
