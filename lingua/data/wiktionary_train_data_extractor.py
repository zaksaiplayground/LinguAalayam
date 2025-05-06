from playwright.sync_api import sync_playwright, Playwright
from parsel import Selector
from tqdm import tqdm
from lingua.database.crud import (
    get_words_for_review, 
    insert_word_definitions, 
    update_word_needs_review
)


def scrape_definitions_from_db(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Get all word URLs where 'needs_review' is True
    words_to_scrape = get_words_for_review()
    for word_obj in tqdm(words_to_scrape, desc="Scraping Definitions"):
        url = word_obj.word_url
        if not url:
            continue

        word = url.split("/")[-1]
        word_uuid = word_obj.word_uuid
        try:
            page.goto(url)
            page.wait_for_selector('//*[@id="mw-content-text"]/div[1]')
            page_html = page.content()

            sel = Selector(text=page_html)
            content_div = sel.xpath('//*[@id="mw-content-text"]/div[1]')
            bolds = content_div.xpath(f'.//b[normalize-space(text())="{word}"]')

            definitions = []
            for bold in bolds:
                ancestor = bold.xpath('./ancestor::*[self::p or self::div][1]')
                lists = ancestor.xpath('./following-sibling::*[self::ul or self::ol]')
                for lst in lists:
                    list_items = lst.xpath('./li')
                    for li in list_items:
                        definitions.append(li.xpath('normalize-space(string())').get())

                if not definitions:
                    fallback_lis = bold.xpath('./following::*[self::ul or self::ol][1]/li')
                    for li in fallback_lis:
                        definitions.append(li.xpath('normalize-space(string())').get())

            # Update word in DB
            if definitions:
                # Insert scraped definitions into word_definition table
                insert_word_definitions(word_uuid, definitions)

                # After successful insertion of definitions, update needs_review to False
                update_word_needs_review(word_uuid)

        except Exception as e:
            print(f"❌ Error scraping {word}: {e}")
            continue

    browser.close()
    
def main():
    with sync_playwright() as playwright:
        scrape_definitions_from_db(playwright)

if __name__ == "__main__":
    main()
