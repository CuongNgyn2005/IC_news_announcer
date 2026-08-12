import hashlib
import os

import requests
from dotenv import load_dotenv

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
from filters.job_filter import classify_job


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

MAX_NEWS_TO_SEND = int(os.getenv("MAX_NEWS_TO_SEND", "5"))
MAX_JOBS_TO_SEND = int(os.getenv("MAX_JOBS_TO_SEND", "10"))


def send_telegram_message(message):
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID "
            "must be set in .env"
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


def _tag(text):
    cleaned = "".join(
        char if char.isalnum() else "_"
        for char in text
    )
    cleaned = "_".join(
        part for part in cleaned.split("_") if part
    )
    return f"#{cleaned}" if cleaned else ""


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


def process_news():
    articles = fetch_news()
    print(f"\nCollected {len(articles)} news candidates")

    accepted = []

    for article in articles:
        related, score, keywords = is_ic_related(article)

        if related:
            article["ic_score"] = score
            article["keywords"] = keywords
            accepted.append(article)
            print(
                f"[NEWS ACCEPT] {score:2d} | "
                f"{article['title']} | {keywords}"
            )
        else:
            print(
                f"[NEWS REJECT] {score:2d} | "
                f"{article['title']}"
            )

    print(f"\nIC news: {len(accepted)}/{len(articles)}")
    sent_count = 0

    for article in accepted:
        if sent_count >= MAX_NEWS_TO_SEND:
            break

        if article_exists(article["link"]):
            print(f"[NEWS DUPLICATE] {article['title']}")
            continue

        tags = " ".join(
            tag
            for tag in (
                _tag(keyword)
                for keyword in article["keywords"][:5]
            )
            if tag
        )

        company = article.get("company")
        company_line = f"🏢 Company: {company}\n" if company else ""

        message = (
            "📰 IC TECHNOLOGY NEWS\n\n"
            f"{article['title']}\n\n"
            f"{company_line}"
            f"🗞 Source: {article['source']}\n"
            f"🎯 IC score: {article['ic_score']}\n"
            f"🏷 {tags}\n\n"
            f"🔗 {article['link']}"
        )

        print(f"[NEWS SEND] {article['title']}")

        try:
            send_telegram_message(message)
            save_article(article)
            sent_count += 1
        except (requests.RequestException, RuntimeError) as error:
            print(
                f"[TELEGRAM ERROR] "
                f"{article['title']} | {error}"
            )

    print(f"News finished. Sent {sent_count} new articles.")


def process_jobs():
    jobs = fetch_jobs()
    print(f"\nCollected {len(jobs)} job candidates")

    accepted = []

    for job in jobs:
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
                f"{job.get('location', '')} | "
                f"{role}"
            )
        else:
            print(
                f"[JOB REJECT] {score:2d} | "
                f"{job.get('company', '')} | "
                f"{job['title']} | "
                f"{job.get('location', '')}"
            )

    accepted.sort(
        key=lambda item: (
            -item.get("job_score", 0),
            item.get("company", ""),
            item.get("title", ""),
        )
    )

    print(
        f"\nTarget Vietnam IC jobs: "
        f"{len(accepted)}/{len(jobs)}"
    )

    sent_count = 0

    for job in accepted:
        if sent_count >= MAX_JOBS_TO_SEND:
            break

        if job_exists(job["job_key"]):
            print(
                f"[JOB DUPLICATE] "
                f"{job['company']} | {job['title']}"
            )
            continue

        matched = ", ".join(job.get("matched_terms", [])[:5])
        posted_line = (
            f"🗓 Posted: {job['posted']}\n"
            if job.get("posted")
            else ""
        )

        message = (
            "💼 VIETNAM IC JOB\n\n"
            f"{job['title']}\n\n"
            f"🏢 Company: {job.get('company', '')}\n"
            f"📍 Location: {job.get('location') or 'Vietnam'}\n"
            f"🎯 Focus: {job.get('role', '')}\n"
            f"{posted_line}"
            f"🔎 Matched: {matched}\n\n"
            f"🔗 {job.get('link', '')}"
        )

        print(f"[JOB SEND] {job['company']} | {job['title']}")

        try:
            send_telegram_message(message)
            save_job(job)
            sent_count += 1
        except (requests.RequestException, RuntimeError) as error:
            print(
                f"[TELEGRAM ERROR] {job['title']} | {error}"
            )

    print(f"Jobs finished. Sent {sent_count} new jobs.")


def main():
    initialize_database()
    process_news()
    process_jobs()


if __name__ == "__main__":
    main()
