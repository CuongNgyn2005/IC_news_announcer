# IC News Announcer

Telegram bot for semiconductor technology news and Vietnam IC-design jobs.

The bot has two pipelines:

```text
News sources -> IC/product filter -> SQLite dedupe -> Telegram
Job sources  -> Vietnam + IC-role filter -> SQLite dedupe -> Telegram
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

Run filter tests:

```powershell
python -m unittest discover -s tests
```

## Dedupe behavior

Successful Telegram sends are saved in `data/ic_watch.db`.

- News is deduplicated by article URL.
- Jobs are deduplicated by a hash of source, company, title, location, and URL.
- Failed Telegram sends are not recorded, so they can be retried on the next run.

## Source behavior

Some career sites are dynamic or protected. Each collector is isolated: one
source failing logs `[JOB ERROR]` or `[COMPANY ERROR]` and does not stop the
remaining sources.

Marvell jobs use the public Workday career endpoint. Ampere uses its
Ho Chi Minh City results page. HCLTech and Infineon use their career search
pages with Vietnam location filters. SkyeChip, Truechip and Ideas2Silicon use
their public career/catalog pages.

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
