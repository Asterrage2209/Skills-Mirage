import logging
import random
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


def create_driver(headless=True):
    logger.info("Creating Chrome driver (headless=%s)", headless)
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Use a real user agent
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=options)
    
    # Execute CDP command to fake navigator.webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    logger.info("Chrome driver created successfully")
    return driver


def fetch_rendered_html(driver, url, wait_selector="body", timeout=20):
    logger.debug("Navigating to URL: %s", url)
    driver.get(url)

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        logger.debug("Wait selector found: %s", wait_selector)
    except TimeoutException:
        # Return whatever HTML loaded; caller decides if usable.
        logger.warning("Timeout waiting for selector '%s' on URL: %s", wait_selector, url)

    time.sleep(random.uniform(1.0, 2.0))
    html = driver.page_source
    logger.debug("Fetched rendered HTML: url=%s title=%s length=%s", url, driver.title, len(html))
    return html
