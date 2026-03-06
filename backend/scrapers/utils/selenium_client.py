import logging
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

# Must match CARD_SELECTORS in naukri_parser.py
# We wait for one of these to appear before returning HTML so that
# React has fully mounted job cards into the DOM.
CARD_WAIT_SELECTORS = [
    "div.cust-job-tuple",
    "div.srp-jobtuple-wrapper",
]


def create_driver(headless=True):
    logger.info("Creating Chrome driver (headless=%s)", headless)
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # ── Stability ─────────────────────────────────────────────────────────────
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    # ── Anti-bot spoofing ─────────────────────────────────────────────────────
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # ── Speed: block ONLY images and media ───────────────────────────────────
    # CRITICAL: Do NOT block CSS or fonts.
    # Naukri is a React SPA — its JS bundle reads computed styles to determine
    # when to mount job cards. Blocking CSS causes the bundle to hang or skip
    # the card render entirely, resulting in 0 cards on every page.
    # Blocking images + media alone still saves ~0.5–1 s per page.
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # ── Speed: disable unused Chrome subsystems ───────────────────────────────
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-background-networking")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--safebrowsing-disable-auto-update")

    # ── Page load strategy: NORMAL ────────────────────────────────────────────
    # DO NOT use "eager" — Naukri is a React SPA and "eager" fires on
    # DOMContentLoaded, which is before React mounts job cards. We stay on
    # "normal" (default) and use explicit WebDriverWait on the card selector.

    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    logger.info("Chrome driver created successfully")
    return driver


def fetch_rendered_html(driver, url, wait_selector="body", timeout=20):
    """
    Navigate to `url` and return page HTML only after job cards are in the DOM.

    Why not wait for `wait_selector="body"`?
    ─────────────────────────────────────────
    `body` appears almost immediately after the browser receives the first byte.
    On a React SPA like Naukri, the actual job cards are injected hundreds of
    milliseconds later by JS. Waiting for `body` returns HTML with an empty
    card container — BeautifulSoup then finds 0 cards.

    Fix: try each known card CSS selector in sequence. The first one that
    resolves means React finished mounting. If none resolve within `timeout`,
    we fall back to a small sleep and return whatever is rendered.
    """
    logger.debug("Navigating to URL: %s", url)
    driver.get(url)

    found = False
    # Split the total timeout evenly across selectors so we don't overspend
    # on a selector that will never match (e.g. wrong page type).
    per_selector_timeout = timeout / len(CARD_WAIT_SELECTORS)

    for selector in CARD_WAIT_SELECTORS:
        try:
            WebDriverWait(driver, per_selector_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            logger.debug("Card selector matched: %s  url=%s", selector, url)
            found = True
            break
        except TimeoutException:
            continue

    if not found:
        # No card selector appeared — could be an empty results page or a
        # transient load issue. Wait briefly for any late JS paint.
        logger.warning("No card selector appeared on %s — returning current DOM", url)
        time.sleep(1.5)

    html = driver.page_source
    logger.debug(
        "Fetched HTML: url=%s title=%s length=%s cards_found=%s",
        url, driver.title, len(html), found,
    )
    return html


def create_driver_pool(size=3, headless=True):
    """
    Create `size` independent Chrome drivers for parallel page fetching.
    Each driver is fully isolated — pass them into a DriverPool queue in
    naukri_scraper.py so threads never share a driver instance.
    """
    logger.info("Creating Chrome driver pool size=%s headless=%s", size, headless)
    drivers = [create_driver(headless=headless) for _ in range(size)]
    logger.info("Driver pool ready")
    return drivers