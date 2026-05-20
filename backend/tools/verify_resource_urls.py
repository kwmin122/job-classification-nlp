from __future__ import annotations

import csv
import html
import re
import socket
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = BACKEND_ROOT / "app" / "data" / "learning_resources.csv"
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def fetch(url: str) -> tuple[int, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            )
        },
    )
    context = ssl.create_default_context()
    with urlopen(request, timeout=12, context=context) as response:
        status = response.status
        final_url = response.geturl()
        content_type = response.headers.get("content-type", "")
        body = response.read(120_000)

    title = ""
    if "text/html" in content_type:
        text = body.decode("utf-8", errors="ignore")
        match = TITLE_RE.search(text)
        if match:
            title = html.unescape(" ".join(match.group(1).split()))
    return status, final_url, title


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    failures: list[str] = []
    for row in rows:
        url = row["url"]
        try:
            status, final_url, title = fetch(url)
        except (HTTPError, URLError, TimeoutError, socket.timeout, ssl.SSLError) as error:
            failures.append(f"{row['id']} {url} -> {error}")
            continue

        if status >= 400:
            failures.append(f"{row['id']} {url} -> HTTP {status}")
            continue

        print(f"{row['id']}\t{status}\t{final_url}\t{title[:90]}")

    if failures:
        print("\nFAILURES", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
