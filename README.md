# IC News Announcer

Telegram bot for semiconductor technology news and Vietnam IC-design jobs.

The bot has two pipelines:

```text
News sources -> IC/product filter -> source-text technical summary -> persistent dedupe -> Telegram
Job sources  -> IC-role prefilter -> job-detail enrichment -> Vietnam gate -> persistent dedupe -> Telegram
```

## Automatic operation

IC Watch is designed to run from GitHub Actions, so a personal PC does not need
to stay on. The scheduled workflow is `.github/workflows/ic-watch.yml` and runs
at:

- 09:00 Asia/Ho_Chi_Minh every day
- 15:00 Asia/Ho_Chi_Minh every day

Each run creates a temporary GitHub-hosted runner, installs the Python
dependencies, runs the regression tests, collects news/jobs, sends genuinely
new accepted items to Telegram, persists its dedupe database, and exits.

The persistent database is stored only on the `bot-state` branch as
`state/ic_watch.db`; it is not committed to `main`. On the first automated run,
IC Watch enters baseline mode: currently visible accepted items are recorded but
**not sent**. This prevents an old job/news backlog from flooding Telegram when
a new source is introduced. Later scheduled runs announce only new items.

### Required GitHub Actions secrets

Before the workflow can send to Telegram, add these repository secrets in
GitHub **Settings -> Secrets and variables -> Actions**:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHANNEL_ID
```

Use the same values as the local `.env`; never commit them to the repository.
After adding both secrets, the workflow can also be tested manually from
**Actions -> IC Watch Scheduled Run -> Run workflow**.

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

## Vietnam semiconductor companies monitored

The job-source set is company-first and now covers a broader mix of large
international design/EDA companies and Vietnam-focused semiconductor teams:

- Marvell
- Ampere Computing
- SkyeChip
- HCLTech
- Truechip
- Infineon Technologies
- Ideas2Silicon
- Synopsys
- Qorvo
- Renesas Electronics
- Cadence
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

## Dedupe behavior

Locally, successful Telegram sends are saved in `data/ic_watch.db`. Under
GitHub Actions the same SQLite state is restored from and saved back to the
`bot-state` branch.

- News is deduplicated by article URL.
- Jobs are deduplicated by a hash of source, company, title, location, and URL.
- Failed Telegram sends are not recorded, so they can be retried on the next run.
- The first automated run baselines existing accepted items without sending.

## Source behavior

Some career and newsroom sites are dynamic or protected. Each collector is
isolated: one source failing logs `[JOB ERROR]`, `[HTML ERROR]` or
`[COMPANY ERROR]` and does not stop the remaining sources.

Marvell and Cadence use Workday collection; Ampere uses its public careers JSON
listing with a browser-like TLS client. Renesas uses its public SmartRecruiters
career page. FPT Semiconductor, Faraday Vietnam, Viettel High Tech, QNSC, NBIV,
BOS Semiconductors and other smaller teams use their official public career or
catalog pages where possible.

A configured `country_filter = "Vietnam"` is a search request, not proof that a
returned job is in Vietnam. The final filter requires observed Vietnam evidence
unless the particular source itself is explicitly Vietnam-only.

Company news is intentionally filtered more strictly than jobs so corporate
earnings, acquisitions and hiring announcements do not appear as technology
product news.

## Optional continuous local mode

`service.py` remains available for local experiments, but it is not needed for
the production schedule. GitHub Actions is the intended unattended runner.
