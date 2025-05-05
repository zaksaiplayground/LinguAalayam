import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin
import pandas as pd
from tqdm import tqdm
import pathlib

_BASE_URL = "https://samam.net/glossary/"
_TOTAL_PAGES = 493
_OUTPUT_DIR_FILE = pathlib.Path("data/raw/samam/glossary_df.csv")

async def scrape_glossary(browser, url):
    data = []

    page = await browser.new_page()
    await page.goto(url)
    await page.wait_for_selector('#entries-table')  # XPath not needed

    rows = page.locator('table#entries-table tr')
    count = await rows.count()

    for i in range(1, count):  # skip header
        row_text = await rows.nth(i).inner_text()
        columns = row_text.split('\t')
        if len(columns) == 4:
            data.append([col.strip() for col in columns])

    await page.close()

    return pd.DataFrame(data, columns=["Malayalam", "Kannada", "Tamil", "Telugu"])

async def main():
    glossary_df = pd.DataFrame()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        for page_num in tqdm(range(1, _TOTAL_PAGES + 1)):
            url = urljoin(_BASE_URL, f"?page={page_num}")
            df = await scrape_glossary(browser, url)
            glossary_df = pd.concat([glossary_df, df])
        await browser.close()
    glossary_df.to_csv(_OUTPUT_DIR_FILE, index=False, sep="\t")

if __name__ == "__main__":
    asyncio.run(main())
