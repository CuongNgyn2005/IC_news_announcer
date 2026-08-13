# IC News Announcer

Telegram bot for semiconductor technology news and Vietnam IC-design jobs.

The bot has two pipelines:

```text
News sources -> IC/product filter -> source-text technical summary -> permanent URL dedupe -> Telegram
Job sources  -> IC-role prefilter -> job-detail enrichment -> Vietnam gate -> 7-day quiet period -> Telegram
```

## Automatic operation

IC Watch is designed to run from GitHub Actions, so a personal PC does not need
to stay on. The production workflow is `.github/workflows/ic-watch.yml` and is
scheduled once per day at:

- **09:00 Asia/Ho_Chi_Minh**

Each run creates a temporary GitHub-hosted runner, installs the Python
dependencies, runs the regression tests, collects news/jobs, sends eligible
items to Telegram, persists its state database, and exits.

The persistent database is stored only on the `bot-state` branch as
`state/ic_watch.db`; it is not committed to `main`. If that persistent database
does not exist, IC Watch enters baseline mode: currently visible accepted items
are recorded but **not sent**. This prevents an old job/news backlog from
flooding Telegram when persistent state is first created.

### Required GitHub Actions secrets

Before the workflow can send to Telegram, add these repository secrets in
GitHub **Settings -> Secrets and variables -> Actions**:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHANNEL_ID
```

Use the same values as the local `.env`; never commit them to the repository.

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
- experience requirement
- IC track
- posted date when available
- IELTS / TOEIC / TOEFL or English requirement when explicitly stated
- key technical/education qualifications from the source job description

Experience extraction reads the employer's detail text and also understands
common variants such as `3+ years`, `3-5 yrs`, `minimum 4 years`, `relevant
working experience`, and explicit fresh-graduate/no-experience wording. When a
page exposes structured `JobPosting` JSON-LD or Workday JSON, that structured
text is included as evidence. If a public detail page blocks direct runner
requests, a rendered-text fallback is attempted before reporting the field as
not stated.

The bot never invents a city, language score or experience requirement. If the
available source text does not provide one, the alert says that it is not
stated.

## Job announcement lifecycle

Jobs are intentionally **not permanent one-time announcements** anymore.
A successful job alert starts a **7-day quiet period** for that exact posting.
While the job remains inside that period it is suppressed. Once seven days have
elapsed, if the same posting is still present and still passes all Vietnam/IC
filters, it becomes eligible to appear again. A successful re-announcement
starts a new seven-day quiet period.

The stable job identity is based on source, company, title and posting URL;
derived fields such as city, seniority or IC-track classification do not create
a fake new posting when parsers improve.

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

Unlike jobs, **news remains permanent one-time announcement behavior**. Once an
article URL has been successfully sent/baselined, that URL stays deduplicated
and is not intentionally recycled after seven days.

## Vietnam semiconductor companies monitored

The job-source set is company-first and covers large international IC/EDA
employers and Vietnam-focused semiconductor teams, including:

- Marvell
- Ampere Computing
- SkyeChip
- HCLTech
- Truechip
- Infineon Technologies
- Ideas2Silicon
- Synopsys
- Qorvo
- Intel
- Renesas Electronics
- Cadence
- GSME
- FPT Semiconductor
- Faraday Technology Vietnam
- Viettel High Tech
- Quy Nhon Semiconductor (QNSC)
- NBIV
- BOS Semiconductors Vietnam
- CoAsia SEMI

General IC news from EE Times and IEEE Spectrum is also collected. Not every
company has a stable machine-readable careers/news feed; source-specific
collectors are preferred, and one failing source does not stop the rest of the
run.

## Local setup and validation

Local execution remains useful for development and debugging but is not required
for the scheduled production bot.

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

Run one local collection cycle:

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

## State and dedupe behavior

Locally, successful Telegram sends are saved in `data/ic_watch.db`. Under
GitHub Actions the same SQLite state is restored from and saved back to the
`bot-state` branch.

- News is permanently deduplicated by article URL.
- Jobs use a seven-day quiet period after each successful send.
- Re-announcing a job refreshes its stored `sent_at` time instead of adding a duplicate row.
- Failed Telegram sends are not recorded as successful sends, so they can be retried later.
- If persistent state is missing, the first automated run baselines current accepted items without sending.

## Source behavior

Some career and newsroom sites are dynamic or protected. Each collector is
isolated: one source failing logs `[JOB ERROR]`, `[HTML ERROR]` or
`[COMPANY ERROR]` and does not stop the remaining sources.

Marvell, Intel and Cadence use Workday collection; global Workday rows with an
explicit non-Vietnam location are discarded before expensive detail-page
requests. Ampere uses its public careers listing with a rendered fallback when
needed. Renesas uses its public SmartRecruiters career page. Synopsys, Qorvo and
GSME use their public career listings. FPT Semiconductor, Faraday Vietnam,
Viettel High Tech, QNSC, NBIV, BOS Semiconductors and other smaller teams use
their official public career or catalog pages where possible.

A configured `country_filter = "Vietnam"` is a search request, not proof that a
returned job is in Vietnam. The final filter requires observed Vietnam evidence
unless the particular source itself is explicitly Vietnam-only.

Company news is intentionally filtered more strictly than jobs so corporate
earnings, acquisitions and hiring announcements do not appear as technology
product news.

## Optional continuous local mode

`service.py` remains available for local experiments, but it is not needed for
the production schedule. GitHub Actions is the intended unattended runner.
