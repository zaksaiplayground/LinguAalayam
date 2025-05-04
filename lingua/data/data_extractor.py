from playwright.sync_api import sync_playwright, Playwright
from parsel import Selector
from urllib.parse import urlparse, unquote
import pandas as pd
import pathlib

_DATA_DIR = pathlib.Path("data/raw/")
_WORD_URL_DIR = "word_urls"


def scrape_definitions_from_word_url(playwright: Playwright, word_url_df):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    all_words_per_alphabet_df = pd.DataFrame()
    no_definition_df = pd.DataFrame()

    for url in word_url_df["word_url"]:
        parsed = urlparse(url)
        word_encoded = parsed.path.split("/")[-1]
        word = unquote(word_encoded)

        page.goto(url)
        page.wait_for_selector('//*[@id="mw-content-text"]/div[1]')
        page_html = page.content()

        sel = Selector(text=page_html)
        content_div = sel.xpath('//*[@id="mw-content-text"]/div[1]')
        # Look for <b> with the word
        bolds = content_div.xpath(f'.//b[normalize-space(text())="{word}"]')

        definitions = []
        for bold in bolds:
            ancestor = bold.xpath('./ancestor::*[self::p or self::div][1]')
            lists = ancestor.xpath('./following-sibling::*[self::ul or self::ol]')

            for lst in lists:
                list_items = lst.xpath('./li')
                for li in list_items:
                    definitions.append(li.xpath('normalize-space(string())').get())
                    
            # If nothing found, fallback: try next siblings of bold directly
            if not definitions:
                fallback_lis = bold.xpath('./following::*[self::ul or self::ol][1]/li')
                for li in fallback_lis:
                    definitions.append(li.xpath('normalize-space(string())').get())


        if definitions:
            temp_df = pd.DataFrame({"word": [word]*len(definitions), "definitions": definitions})
            all_words_per_alphabet_df = pd.concat([all_words_per_alphabet_df, temp_df])
        else:
            print(f"NO DEF FOUND FOR WORD: {word} and URL: {url}")
            temp_df = pd.DataFrame({"word": [word], "url": [url]})
            no_definition_df = pd.concat([no_definition_df, temp_df])
    
    del temp_df
    print(f"Writing {all_words_per_alphabet_df.shape[0]} definitions to disk.")
    all_words_per_alphabet_df.to_csv("all_words_per_alphabet_df.csv", sep="\t")
    print(f"{no_definition_df.shape[0]} definitions not found. Saving urls to disk.")
    no_definition_df.to_csv("no_definition_df.csv", "\t")

if __name__ == "__main__":
    word_url_dir = pathlib.Path(_DATA_DIR, _WORD_URL_DIR)
    is_empty = not any(word_url_dir.iterdir())

    if is_empty:
        print("Word URLs required to run this script. Run url_scrapper.py first.")
        exit(1)
    
    with sync_playwright() as playwright:
        for word_urls in word_url_dir.iterdir():
            word_url_df = pd.read_csv(word_urls)
            scrape_definitions_from_word_url(playwright, word_url_df)
            break