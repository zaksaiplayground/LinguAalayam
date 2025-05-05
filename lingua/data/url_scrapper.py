from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from parsel import Selector
from urllib.parse import urljoin
import asyncio
from lingua.database.crud import upsert_alphabet, get_all_alphabets, add_word, soft_delete_alphabets
from tqdm import tqdm
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

_BASE_URL = "https://ml.wiktionary.org"
MAX_CONCURRENT_BROWSERS = 5

async def scrape_alphabet_url(playwright, website):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(website)
    await page.wait_for_selector('//*[@id="mwCA"]')
    page_html = await page.content()
    await browser.close()

    sel = Selector(text=page_html)
    container = sel.xpath('//*[@id="mwBw"]')
    links = container.xpath('.//a')

    for link in tqdm(links):
        href = link.xpath('.//@href').get()
        if href:
            absolute_url = urljoin("https:", href)
            alphabet = absolute_url.split("/")[-1]
            upsert_alphabet(alphabet, absolute_url)

    logger.info("✅ Saved alphabet URLs to database.")


async def wait_for_either(page, selectors, timeout=10000):
    start = time.time()
    while True:
        for sel in selectors:
            try:
                el = await page.query_selector(f"xpath={sel}")
                if el:
                    return sel  # Return the matched selector
            except:
                pass

        if (time.time() - start) * 1000 > timeout:
            raise PlaywrightTimeoutError(f"Timeout waiting for one of: {selectors}")

        await asyncio.sleep(0.2)  # Short sleep between checks


async def process_alphabet(playwright, ml_record, semaphore):
    """Process a single alphabet with its own browser instance"""
    async with semaphore:  # Limit concurrent browsers
        alphabet_url = ml_record.url
        alphabet = alphabet_url.split("/")[-1]
        logger.info(f"🔤 Starting scrape for alphabet: {alphabet}")
        
        # Create checkpointing data
        checkpoint_file = f"checkpoint_{alphabet}.txt"
        processed_urls = set()
        is_complete = False
        
        # Load checkpoint if exists
        try:
            with open(checkpoint_file, 'r') as f:
                processed_urls = set(line.strip() for line in f.readlines())
            logger.info(f"📋 Loaded checkpoint for {alphabet} with {len(processed_urls)} processed URLs")
        except FileNotFoundError:
            logger.info(f"No checkpoint found for {alphabet}, starting fresh")
        
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(alphabet_url)
            page_number = 1
            
            while True:
                # Wait for either of the selectors
                selector_used = await wait_for_either(page, [
                    '//*[@id="mw-content-text"]/div[3]',
                    '//*[@id="mw-content-text"]/div[2]'
                ])
                
                page_html = await page.content()
                new_links = extract_links(page_html=page_html, selector_used=selector_used)
                
                # Process links in batches to avoid hammering the database
                for link in tqdm(new_links, desc=f"Page {page_number}"):
                    if link not in processed_urls:
                        add_word(alphabet=alphabet, word_url=link)
                        # Update checkpoint file after each word
                        with open(checkpoint_file, 'a') as f:
                            f.write(f"{link}\n")
                        processed_urls.add(link)
                
                # Check for next button
                next_button = await page.query_selector('xpath=//*[@id="mw-content-text"]/div[4]//a')
                if not next_button:
                    logger.info(f"⛔ No more pages for alphabet {alphabet}")
                    is_complete = True
                    break
                
                logger.info(f"➡️ Moving to page {page_number + 1} for alphabet {alphabet}")
                await next_button.click()
                await page.wait_for_load_state("networkidle")
                page_number += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing alphabet {alphabet}: {str(e)}")
        finally:
            await browser.close()
            
            # Delete checkpoint file if processing completed successfully
            if is_complete:
                try:
                    import os
                    os.remove(checkpoint_file)
                    logger.info(f"🗑️ Deleted checkpoint file for completed alphabet {alphabet}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete checkpoint file for {alphabet}: {str(e)}")
            
            logger.info(f"✅ Completed scraping for alphabet {alphabet}")


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


async def scrape_word_url_per_alphabet(playwright, ml_records):
    # Create a semaphore to limit concurrent browsers
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)
    
    # Create tasks for each alphabet
    tasks = []
    for record in ml_records:
        task = asyncio.create_task(process_alphabet(playwright, record, semaphore))
        tasks.append(task)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)


async def main_async():
    async with async_playwright() as playwright:
        existing_alphabets = get_all_alphabets()
        if len(existing_alphabets) < 50:
            logger.info("Less than 50 alphabets recorded. Either scrapping for the first time.")
            logger.info("Or db corrupted and rerunning scrapping - DB cleanup required if rerunning.")
            soft_delete_alphabets()
            website = f"{_BASE_URL}/wiki/%E0%B4%B5%E0%B4%BF%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B4%BF%E0%B4%A8%E0%B4%BF%E0%B4%98%E0%B4%A3%E0%B5%8D%E0%B4%9F%E0%B5%81:%E0%B4%89%E0%B4%B3%E0%B5%8D%E0%B4%B3%E0%B4%9F%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B4%82"
            await scrape_alphabet_url(playwright, website)
        else:
            logger.info("✅ Alphabet URLs already in DB. Skipping scraping.")

        ml_records = get_all_alphabets()
        
        if ml_records:
            await scrape_word_url_per_alphabet(playwright, ml_records)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()