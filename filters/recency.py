from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


DATE_FORMATS = (
    "%Y-%m-%d",
    "%b %d, %Y",
    "%B %d, %Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
)


def parse_published_date(value):
    text = str(value or "").strip()
    if not text:
        return None

    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass

    candidates = [text, text[:10], text[:12], text[:20]]
    for candidate in candidates:
        candidate = candidate.strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    return None


def is_recent_article(article, max_days=60, now=None):
    """Reject only articles whose available publication date is clearly stale.

    Some company pages do not expose a machine-readable date. Those undated
    items are still allowed because persistent URL deduplication baselines the
    existing catalog and only newly appearing URLs can be announced later.
    """
    published = parse_published_date(article.get("published", ""))
    if published is None:
        return True

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    return published >= current - timedelta(days=max_days)
