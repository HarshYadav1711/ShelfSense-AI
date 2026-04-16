from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {
    "One": Decimal("1.00"),
    "Two": Decimal("2.00"),
    "Three": Decimal("3.00"),
    "Four": Decimal("4.00"),
    "Five": Decimal("5.00"),
}


@dataclass
class ScrapedBook:
    source_id: str
    title: str
    author: str | None
    rating: Decimal | None
    reviews_count: int | None
    description: str | None
    book_url: str


class BooksToScrapeSeleniumClient:
    def __init__(self, headless: bool = True, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1200")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, timeout_seconds)

    def close(self):
        self.driver.quit()

    def fetch_batch(self, limit: int) -> List[ScrapedBook]:
        results: List[ScrapedBook] = []
        page_url = BASE_URL

        while len(results) < limit and page_url:
            self.driver.get(page_url)
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.product_pod")))
            cards = self.driver.find_elements(By.CSS_SELECTOR, "article.product_pod")
            next_page_url = self._next_page_url(page_url)
            detail_targets = []

            for card in cards:
                if len(results) >= limit:
                    break

                link = card.find_element(By.CSS_SELECTOR, "h3 a")
                detail_targets.append(
                    {
                        "detail_url": urljoin(page_url, link.get_attribute("href")),
                        "title": link.get_attribute("title").strip(),
                        "rating": self._extract_rating(card),
                    }
                )

            for target in detail_targets:
                if len(results) >= limit:
                    break
                results.append(
                    self._fetch_detail(
                        target["detail_url"],
                        target["title"],
                        target["rating"],
                    )
                )

            page_url = next_page_url

        return results

    def _fetch_detail(self, detail_url: str, title: str, rating: Decimal | None) -> ScrapedBook:
        self.driver.get(detail_url)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product_main")))

        source_id = self._read_table_value("UPC")
        description = self._extract_description()

        return ScrapedBook(
            source_id=source_id,
            title=title,
            author=None,
            rating=rating,
            reviews_count=None,
            description=description,
            book_url=detail_url,
        )

    def _extract_rating(self, card) -> Decimal | None:
        rating_element = card.find_element(By.CSS_SELECTOR, ".star-rating")
        classes = rating_element.get_attribute("class").split()
        for css_class in classes:
            if css_class in RATING_MAP:
                return RATING_MAP[css_class]
        return None

    def _extract_description(self) -> str | None:
        try:
            description_element = self.driver.find_element(By.CSS_SELECTOR, "#product_description + p")
            return description_element.text.strip() or None
        except NoSuchElementException:
            return None

    def _read_table_value(self, header: str) -> str:
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table.table-striped tr")
        for row in rows:
            key = row.find_element(By.TAG_NAME, "th").text.strip()
            if key == header:
                return row.find_element(By.TAG_NAME, "td").text.strip()
        raise NoSuchElementException(f"Missing table header: {header}")

    def _next_page_url(self, current_page_url: str) -> str | None:
        try:
            next_link = self.driver.find_element(By.CSS_SELECTOR, "li.next a")
        except NoSuchElementException:
            return None
        return urljoin(current_page_url, next_link.get_attribute("href"))


def scrape_books(limit: int, retries: int = 2) -> List[ScrapedBook]:
    last_error: Exception | None = None

    for _attempt in range(retries + 1):
        client = None
        try:
            client = BooksToScrapeSeleniumClient()
            return client.fetch_batch(limit=limit)
        except TimeoutException as exc:
            last_error = exc
        finally:
            if client is not None:
                client.close()

    if last_error is not None:
        raise last_error

    return []
