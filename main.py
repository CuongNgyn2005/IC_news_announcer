import os
import requests
from dotenv import load_dotenv

from collectors.news import fetch_news
from filters.ic_filter import is_ic_related
from database.db import (
    initialize_database,
    article_exists,
    save_article,
)


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def send_telegram_message(message):
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


def main():
    articles = fetch_news()

    print(f"Collected {len(articles)} articles")

    accepted = []

    for article in articles:
        related, score, keywords = is_ic_related(article)

        if related:
            article["ic_score"] = score
            article["keywords"] = keywords

            accepted.append(article)

            print(
                f"[ACCEPT] {score:2d} | "
                f"{article['title']} | {keywords}"
            )

        else:
            print(
                f"[REJECT] {score:2d} | "
                f"{article['title']}"
            )

    print(f"\nIC articles: {len(accepted)}/{len(articles)}")

    sent_count = 0
    max_articles_to_send = 5

    for article in accepted:

        if sent_count >= max_articles_to_send:
            break

        if article_exists(article["link"]):
            print(
                f"[SKIP DUPLICATE] "
                f"{article['title']}"
            )
            continue

        tags = " ".join(
            "#" + keyword
            .replace("-", "")
            .replace(" ", "_")
            for keyword in article["keywords"][:5]
        )

        message = (
            f"📰 IC TECHNOLOGY NEWS\n\n"
            f"{article['title']}\n\n"
            f"🏢 Source: {article['source']}\n"
            f"🎯 IC score: {article['ic_score']}\n"
            f"🏷 {tags}\n\n"
            f"🔗 {article['link']}"
        )

        print(
            f"[SEND] "
            f"{article['title']}"
        )

        try:
            send_telegram_message(message)

            save_article(article)

            sent_count += 1

        except requests.RequestException as error:
            print(
                f"[TELEGRAM ERROR] "
                f"{article['title']}"
            )
            print(error)

    print(
        f"\nFinished. "
        f"Sent {sent_count} new articles."
    )


if __name__ == "__main__":
    initialize_database()
    main()