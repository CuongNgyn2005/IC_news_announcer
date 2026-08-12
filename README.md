# IC News Announcer

Telegram bot for semiconductor technology news and Vietnam IC-design jobs.

The bot has two pipelines:

```text
News sources -> IC/product filter -> source-text technical summary -> SQLite dedupe -> Telegram
Job sources  -> IC-role prefilter -> job-detail enrichment -> Vietnam gate -> SQLite dedupe -> Telegram
```

## Job focus

The job filter prioritizes roles around:

- Design Verification / SoC Verification / UVM / SystemVerilog
- RTL Design / Logic Design / Digital Design
- Physical Design / P&R / STA / timing closure
- Analog / Mixed-Signal / Custom Layout / Mask Design
- DFT
- Silicon / Hardware Validation
- FPGA / Emulation
- Design Automation / CAD

Only Vietnam-targeted roles are announced. The source configuration is in
`config/sources.py`.

Each accepted job is enriched from the detail page when available. Telegram
uses the `JOBS ALERT` format and reports:

- exact job title
- company
- Vietnam city when the source exposes one
- normalized seniority such as Intern, Graduate, Junior, Senior, Staff or Principal
- IC track
- posted date when available
- experience requirement
- IELTS / TOEIC / TOEFL or English requirement when explicitly stated
- key technical/education qualifications from the source job description

The bot never invents a city, language score or experience requirement. If the
source does not provide one, the alert says that it is not stated.

## IC technology news summaries

Accepted news is summarized from RSS content and, when reachable, the original
article body. The Telegram message follows this structure:

```text
### 1. Core Technical Innovation
- Engineering Breakthrough
- Process Node & Fabrication
- Key Interconnect/Packaging

### 2. Hard Performance Metrics (PPA)
- Power Efficiency
- Performance Uplift
- Area / Density

### 3. Commercial & Scale Highlights
- Financial/CapEx Footprint
- Production Status & Timeline
- Primary Use Case
```

PPA means Power, Performance and Area. Numeric PPA fields are emitted only when
the available source text contains an actual metric. Missing facts are shown as
`Not stated in the source text available to the bot.` instead of being guessed.

## Companies monitored

Priority companies include Marvell, Ampere Computing, SkyeChip, HCLTech,
Truechip, Infineon Technologies, and Ideas2Silicon. General IC news from
EE Times and IEEE Spectrum is also collected.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```text
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=...
MAX_NEWS_TO_SEND=5
MAX_JOBS_TO_SEND=10
POLL_INTERVAL_MINUTES=60
```

Run one collection cycle:

```powershell
python main.py
```

Check source reachability:

```powershell
python check_sources.py
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## Dedupe behavior

Successful Telegram sends are saved in `data/ic_watch.db`.

- News is deduplicated by article URL.
- Jobs are deduplicated by a hash of source, company, title, location, and URL.
- Failed Telegram sends are not recorded, so they can be retried on the next run.

## Source behavior

Some career and newsroom sites are dynamic or protected. Each collector is
isolated: one source failing logs `[JOB ERROR]`, `[HTML ERROR]` or
`[COMPANY ERROR]` and does not stop the remaining sources.

Marvell jobs use the public Workday career endpoint and its job-detail endpoint.
Ampere uses the public careers JSON listing with a browser-like TLS client.
HCLTech and Infineon use their career search pages with Vietnam queries.
SkyeChip, Truechip and Ideas2Silicon use their public career/catalog pages.

A configured `country_filter = "Vietnam"` is a search request, not proof that a
returned job is in Vietnam. The final filter requires observed Vietnam evidence
unless a future source-specific collector can prove the location independently.

Company news is intentionally filtered more strictly than jobs so corporate
earnings, acquisitions and hiring announcements do not appear as technology
product news.

## Continuous mode

`python main.py` runs one collection cycle. To keep IC Watch running continuously:

```powershell
python service.py
```

The default polling interval is 60 minutes. Override it in `.env` with
`POLL_INTERVAL_MINUTES`. The service enforces a minimum interval of 15 minutes
to avoid hammering career/news websites. SQLite deduplication means repeated
cycles do not repost the same accepted item.
