import hashlib
import os

import requests
from dotenv import load_dotenv

from collectors.job_details import enrich_job
from collectors.jobs import fetch_jobs
from collectors.news import fetch_news
from database.db import (
    article_exists,
    initialize_database,
    job_exists,
    save_article,
    save_job,
)
from filters.ic_filter import is_ic_related
from filters.job_filter import classify_job, is_vietnam_job
from filters.recency import is_recent_article
from summarizers.news_summary import (
    format_technical_summary,
    summarize_article,
)


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
MAX_NEWS_TO_SEND = int(os.getenv("MAX_NEWS_TO_SEND", "5"))
MAX_JOBS_TO_SEND = int(os.getenv("MAX_JOBS_TO_SEND", "10"))
BASELINE_ONLY = os.getenv("IC_WATCH_BASELINE_ONLY", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def send_telegram_message(message):
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set in .env"
        )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _make_job_key(job):
    raw = "|".join(
        [
            job.get("source", ""),
            job.get("company", ""),
            job.get("title", ""),
            job.get("location", ""),
            job.get("link", ""),
        ]
    ).lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _display_location(job):
    city = job.get("city", "").strip()
    if city:
        return f"{city}, Vietnam"

    location = (job.get("location") or "").strip()
    if location and location.lower() not in {"vietnam", "viet nam"}:
        return location

    return "Vietnam (city not stated by source)"


def _requirements_text(job):
    qualifications = job.get("qualification_requirements", [])
    if qualifications:
        qualification_text = "\n".join(
            f"  • {item}" for item in qualifications[:4]
        )
    else:
        qualification_text = "  • Not stated in the source text available to the bot."

    return (
        f"• Experience: {job.get('experience_requirement') or 'Not stated'}\n"
        f"• English / IELTS / TOEIC: "
        f"{job.get('english_requirement') or 'Not stated'}\n"
        "• Key qualifications:\n"
        f"{qualification_text}"
    )


def process_news():
    articles = fetch_news()
    print(f"\nCollected {len(articles)} news candidates")

    accepted = []

    for article in articles:
        related, score, keywords = is_ic_related(article)

        if not related:
            print(f"[NEWS REJECT] {score:2d} | {article['title']}")
            continue

        if not is_recent_article(article):
            print(
                f"[NEWS OLD] {article.get('published', '')} | "
                f"{article['title']}"
            )
            continue

        article["ic_score"] = score
        article["keywords"] = keywords
        accepted.append(article)
        print(
            f"[NEWS ACCEPT] {score:2d} | "
            f"{article['title']} | {keywords}"
        )

    print(f"\nIC news: {len(accepted)}/{len(articles)}")

    if BASELINE_ONLY:
        baseline_count = 0
        for article in accepted:
            if article_exists(article["link"]):
                continue
            save_article(article)
            baseline_count += 1
            print(f"[NEWS BASELINE] {article['title']}")
        print(
            f"News baseline finished. Recorded {baseline_count} existing articles; "
            "sent 0."
        )
        return

    sent_count = 0

    for article in accepted:
        if MAX_NEWS_TO_SEND > 0 and sent_count >= MAX_NEWS_TO_SEND:
            break

        if article_exists(article["link"]):
            print(f"[NEWS DUPLICATE] {article['title']}")
            continue

        print(f"[NEWS SUMMARIZE] {article['title']}")
        technical_summary = summarize_article(article)
        summary_text = format_technical_summary(technical_summary)

        company = article.get("company")
        company_line = f"🏢 Company: {company}\n" if company else ""
        published_line = (
            f"🗓 Published: {article['published']}\n"
            if article.get("published")
            else ""
        )

        message = (
            "📰 IC TECHNOLOGY NEWS\n\n"
            f"{article['title']}\n\n"
            f"{company_line}"
            f"🗞 Source: {article['source']}\n"
            f"{published_line}\n"
            f"{summary_text}\n\n"
            f"🔗 Read full article: {article['link']}"
        )

        print(f"[NEWS SEND] {article['title']}")

        try:
            send_telegram_message(message)
            save_article(article)
            sent_count += 1
        except (requests.RequestException, RuntimeError) as error:
            print(f"[TELEGRAM ERROR] {article['title']} | {error}")

    print(f"News finished. Sent {sent_count} new articles.")


def process_jobs():
    jobs = fetch_jobs()
    print(f"\nCollected {len(jobs)} job candidates")

    accepted = []

    for raw_job in jobs:
        if (
            raw_job.get("detail_api_url")
            and raw_job.get("location")
            and not is_vietnam_job(raw_job)
        ):
            print(
                f"[JOB REJECT LOCATION] | "
                f"{raw_job.get('company', '')} | "
                f"{raw_job.get('title', '')} | "
                f"{raw_job.get('location', '')}"
            )
            continue

        pre_related, _, pre_score, _ = classify_job(
            raw_job,
            threshold=5,
            require_vietnam=False,
        )

        if not pre_related:
            print(
                f"[JOB REJECT] {pre_score:2d} | "
                f"{raw_job.get('company', '')} | "
                f"{raw_job.get('title', '')}"
            )
            continue

        job = enrich_job(raw_job)
        related, role, score, terms = classify_job(job)

        if related:
            job["role"] = role
            job["job_score"] = score
            job["matched_terms"] = terms
            job["job_key"] = _make_job_key(job)
            accepted.append(job)
            print(
                f"[JOB ACCEPT] {score:2d} | "
                f"{job.get('company', '')} | "
                f"{job['title']} | "
                f"{_display_location(job)} | "
                f"{job.get('seniority', 'Not stated')} | {role}"
            )
        else:
            print(
                f"[JOB REJECT] {score:2d} | "
                f"{job.get('company', '')} | "
                f"{job.get('title', '')} | "
                f"{job.get('location', '')}"
            )

    accepted.sort(
        key=lambda item: (
            -item.get("job_score", 0),
            item.get("company", ""),
            item.get("title", ""),
        )
    )

    print(f"\nTarget Vietnam IC jobs: {len(accepted)}/{len(jobs)}")

    if BASELINE_ONLY:
        baseline_count = 0
        for job in accepted:
            if job_exists(job["job_key"]):
                continue
            save_job(job)
            baseline_count += 1
            print(f"[JOB BASELINE] {job['company']} | {job['title']}")
        print(
            f"Jobs baseline finished. Recorded {baseline_count} existing jobs; sent 0."
        )
        return

    sent_count = 0

    for job in accepted:
        if MAX_JOBS_TO_SEND > 0 and sent_count >= MAX_JOBS_TO_SEND:
            break

        if job_exists(job["job_key"]):
            print(f"[JOB DUPLICATE] {job['company']} | {job['title']}")
            continue

        posted_line = (
            f"🗓 Posted: {job['posted']}\n"
            if job.get("posted")
            else ""
        )

        message = (
            "🚨 JOBS ALERT\n\n"
            f"💼 {job['title']}\n"
            f"🏢 Company: {job.get('company', '')}\n"
            f"📍 Location: {_display_location(job)}\n"
            f"🏷 Level: {job.get('seniority') or 'Not stated'}\n"
            f"🎯 IC Track: {job.get('role', '')}\n"
            f"{posted_line}\n"
            "Requirements to qualify:\n"
            f"{_requirements_text(job)}\n\n"
            f"🔗 Apply / full description: {job.get('link', '')}"
        )

        print(f"[JOB SEND] {job['company']} | {job['title']}")

        try:
            send_telegram_message(message)
            save_job(job)
            sent_count += 1
        except (requests.RequestException, RuntimeError) as error:
            print(f"[TELEGRAM ERROR] {job['title']} | {error}")

    print(f"Jobs finished. Sent {sent_count} new jobs.")


def main():
    initialize_database()
    if BASELINE_ONLY:
        print("IC Watch baseline mode: recording current accepted items without Telegram sends.")
    process_news()
    process_jobs()


if __name__ == "__main__":
    main()
