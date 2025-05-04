from playwright.sync_api import sync_playwright, Playwright, TimeoutError as PlaywrightTimeoutError
from parsel import Selector
from urllib.parse import urljoin
import pandas as pd
import pathlib

_BASE_URL = "https://ml.wiktionary.org"
_DATA_DIR = pathlib.Path("data/raw/")
_ML_ALPHABET_URL_FILENAME = "ml_df.csv"
_WORD_URL_DIR = "word_urls"

def scrape_alphabet_url(playwright: Playwright, website: str):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(website)
    page.wait_for_selector('//*[@id="mwCA"]')
    page_html = page.content()
    browser.close()

    sel = Selector(text=page_html)
    container = sel.xpath('//*[@id="mwBw"]')
    links = container.xpath('.//a')

    ml_alphabet_urls = []
    for link in links:
        href = link.xpath('.//@href').get()
        if href:
            absolute_url = urljoin("https:", href)
            ml_alphabet_urls.append(absolute_url)

    alphabet_url_file = pathlib.Path(_DATA_DIR, _ML_ALPHABET_URL_FILENAME)
    pd.DataFrame({'alphabet': ml_alphabet_urls}).to_csv(alphabet_url_file, index=False)
    print(f"\n✅ Saved {len(ml_alphabet_urls)} alphabet URLs.")


def wait_for_either(page, selectors, timeout=10000):
    import time
    start = time.time()
    while True:
        for sel in selectors:
            try:
                el = page.query_selector(f"xpath={sel}")
                if el:
                    return sel  # Return the matched selector
            except:
                pass

        if (time.time() - start) * 1000 > timeout:
            raise PlaywrightTimeoutError(f"Timeout waiting for one of: {selectors}")

        time.sleep(0.2)  # Short sleep between checks


def scrape_word_url_per_alphabet(playwright: Playwright, ml_df: pd.DataFrame):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    pathlib.Path(_DATA_DIR, _WORD_URL_DIR).mkdir(parents=True, exist_ok=True)

    for alphabet_url in ml_df["alphabet"]:
        print(alphabet_url[-1])
        ml_word_url_per_alphabet = []
        print(f"\n🔤 Scraping: {alphabet_url}")
        page.goto(alphabet_url)
        while True:
            # last page for an alphabet has only 2 divs
            selector_used = wait_for_either(page, [
                '//*[@id="mw-content-text"]/div[3]',
                '//*[@id="mw-content-text"]/div[2]'
            ])
            page_html = page.content()
            new_links = extract_links(page_html=page_html, selector_used=selector_used)
            ml_word_url_per_alphabet.extend(new_links)

            next_button = page.query_selector('xpath=//*[@id="mw-content-text"]/div[4]//a')
            if not next_button:
                print("⛔ No more pages for this alphabet.")
                word_url_file = pathlib.Path(_DATA_DIR, _WORD_URL_DIR, f"word-{alphabet_url[-1]}.csv")
                pd.DataFrame({'word_url': ml_word_url_per_alphabet}).to_csv(word_url_file, index=False)
                print(f"\n✅ Saved {len(ml_word_url_per_alphabet)} word URLs for alphabet {alphabet_url[-1]}.")
                break
            print("➡️ Moving to next page...")
            next_button.click()
            page.wait_for_load_state("networkidle")

    browser.close()

def extract_links(page_html, selector_used):
    sel = Selector(text=page_html)
    container = sel.xpath(selector_used)
    links = container.xpath('.//a')

    extracted = []
    for link in links:
        href = link.xpath('.//@href').get()
        if href:
            absolute_url = urljoin(_BASE_URL, href)
            extracted.append(absolute_url)

    return extracted

if __name__ == "__main__":

    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    ml_alphabet_url_file = pathlib.Path(_DATA_DIR, _ML_ALPHABET_URL_FILENAME)

    with sync_playwright() as playwright:
        # Only scrape alphabet URLs if file doesn't exist
        if not ml_alphabet_url_file.exists():
            website = f"{_BASE_URL}/wiki/%E0%B4%B5%E0%B4%BF%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B4%BF%E0%B4%A8%E0%B4%BF%E0%B4%98%E0%B4%A3%E0%B5%8D%E0%B4%9F%E0%B5%81:%E0%B4%89%E0%B4%B3%E0%B5%8D%E0%B4%B3%E0%B4%9F%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B4%82"
            scrape_alphabet_url(playwright, website)
        else:
            print(f"\n✅ File {_ML_ALPHABET_URL_FILENAME} exists. Skipping ML alphabet URL scraping.")

        ml_df = pd.read_csv(_ML_ALPHABET_URL_FILENAME)
        if not ml_df.empty:
            scrape_word_url_per_alphabet(playwright, ml_df)