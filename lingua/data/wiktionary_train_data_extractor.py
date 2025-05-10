from playwright.sync_api import sync_playwright, Playwright
from parsel import Selector
from tqdm import tqdm
import logging
from urllib.parse import unquote

from lingua.database.crud import (
    get_words_for_review, 
    insert_word_definitions, 
    update_word_needs_review
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("definition_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def scrape_definitions_from_db(playwright: Playwright):
    """
    Scrapes definitions for words marked for review in the database.
    For each word:
    1. Accesses the word's URL
    2. Extracts definitions if available
    3. Inserts definitions into the word_definition table
    4. Updates the word's needs_review flag to False if definitions are found
    """
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Batch processing settings
    BATCH_SIZE = 100
    processed_count = 0
    success_count = 0
    
    try:
        # Get all word URLs where 'needs_review' is True
        words_to_scrape = get_words_for_review()
        total_words = len(words_to_scrape)
        logger.info(f"Found {total_words} words that need review")
        
        for word_obj in tqdm(words_to_scrape, desc="Scraping Definitions"):
            url = word_obj.word_url
            if not url:
                logger.warning(f"Empty URL for word_uuid: {word_obj.word_uuid}")
                continue
            
            # Extract the word name from URL
            word = unquote(url.split("/")[-1])
            word_uuid = word_obj.word_uuid
            
            try:
                logger.info(f"Processing word: {word} (UUID: {word_uuid})")
                page.goto(url, timeout=30000)  # Increased timeout for slow connections
                
                # Wait for content to load
                try:
                    page.wait_for_selector('//*[@id="mw-content-text"]/div[1]', timeout=15000)
                except Exception as e:
                    logger.warning(f"Wait timeout for {word}: {e}")
                    continue
                    
                page_html = page.content()
                
                # Parse content using Selector
                sel = Selector(text=page_html)
                content_div = sel.xpath('//*[@id="mw-content-text"]/div[1]')
                
                # Find all <b> tags that exactly match the word
                bolds = content_div.xpath(f'.//b[normalize-space(.)="{word}"]')
                
                # If direct match not found, try a more relaxed search
                if not bolds:
                    bolds = content_div.xpath(f'.//b[contains(., "{word}")]')
                
                definitions = []
                
                # Process each bold tag that might be the word heading
                for bold in bolds:
                    # Look for definition lists after the bold tag
                    ancestor = bold.xpath('./ancestor::*[self::p or self::div][1]')
                    
                    # Find all list elements (ordered or unordered) that follow the ancestor
                    lists = ancestor.xpath('./following-sibling::*[self::ul or self::ol][position()=1]')
                    
                    for lst in lists:
                        # Extract each list item as a definition
                        list_items = lst.xpath('./li')
                        for li in list_items:
                            definition_text = li.xpath('normalize-space(string())').get()
                            if definition_text and len(definition_text.strip()) > 0:
                                definitions.append(definition_text)
                    
                    # If no definitions found using that approach, try a fallback method
                    if not definitions:
                        fallback_lis = bold.xpath('./following::*[self::ul or self::ol][1]/li')
                        for li in fallback_lis:
                            definition_text = li.xpath('normalize-space(string())').get()
                            if definition_text and len(definition_text.strip()) > 0:
                                definitions.append(definition_text)
                
                # Update database if definitions were found
                if definitions:
                    logger.info(f"Found {len(definitions)} definitions for '{word}'")
                    
                    # Insert scraped definitions into word_definition table
                    insert_word_definitions(word_uuid, definitions, word_text=word)
                    
                    # Update needs_review to False
                    update_word_needs_review(word_uuid)
                    
                    success_count += 1
                else:
                    logger.warning(f"No definitions found for '{word}'")
                
                processed_count += 1
                
                # Log progress at regular intervals
                if processed_count % 20 == 0:
                    logger.info(f"Progress: {processed_count}/{total_words} words processed ({success_count} with definitions)")
                
            except Exception as e:
                logger.error(f"❌ Error scraping {word}: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Fatal error in scraper: {str(e)}")
    finally:
        browser.close()
        logger.info(f"Scraping completed. Processed {processed_count} words. Found definitions for {success_count} words.")

def main():
    """Main function to run the definition scraper"""
    logger.info("Starting definition scraper")
    with sync_playwright() as playwright:
        scrape_definitions_from_db(playwright)
    logger.info("Definition scraper finished")

if __name__ == "__main__":
    main()