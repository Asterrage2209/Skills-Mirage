import random
import time

import requests

HEADERS = [
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    },
]


def fetch(url):
    headers = random.choice(HEADERS)

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    time.sleep(random.uniform(1.5, 3.5))

    return response.text
