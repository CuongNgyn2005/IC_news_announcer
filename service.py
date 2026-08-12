import os
import time
from datetime import datetime

from dotenv import load_dotenv

from main import main


load_dotenv()

POLL_INTERVAL_MINUTES = max(
    15,
    int(os.getenv("POLL_INTERVAL_MINUTES", "60")),
)


def run_forever():
    print(
        "IC Watch service started. "
        f"Polling every {POLL_INTERVAL_MINUTES} minutes."
    )

    while True:
        started = datetime.now().astimezone()
        print(
            "\n"
            + "=" * 70
            + f"\nIC Watch cycle: {started.isoformat(timespec='seconds')}"
            + "\n"
            + "=" * 70
        )

        try:
            main()
        except Exception as error:
            # Keep the service alive if a single cycle has an
            # unexpected failure. Individual collectors already
            # isolate normal HTTP/source errors.
            print(f"[CYCLE ERROR] {type(error).__name__}: {error}")

        time.sleep(POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    run_forever()
