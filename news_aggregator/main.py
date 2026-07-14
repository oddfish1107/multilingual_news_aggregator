import concurrent.futures
from src.crawlers.crawler_engine import VnExpressCrawler, BBCCrawler
from src.db.database_manager import DatabaseManager
from src.utils.utils import timing_decorator, logger
from src.pipeline.cleaner import NewsDataCleaner
import os

@timing_decorator
def main():
    logger.info("Starting Phase 1: Crawling & Storage")
    
    db_path = os.path.join(os.path.dirname(__file__), "data", "news_data_v2.db")
    db_manager = DatabaseManager(db_path)
    
    # Initialize crawlers with their respective target URLs
    crawlers = [
        (VnExpressCrawler(), "https://vnexpress.net/the-gioi"),
        (BBCCrawler(), "https://www.bbc.com/news/world")
    ]
    
    all_articles = []
    
    # Implementing multi-threading for concurrent crawling
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit crawling tasks to threads
        future_to_crawler = {
            executor.submit(crawler.crawl, url): crawler.name 
            for crawler, url in crawlers
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_crawler):
            crawler_name = future_to_crawler[future]
            try:
                articles = future.result()
                logger.info(f"{crawler_name} fetched {len(articles)} articles.")
                all_articles.extend(articles)
            except Exception as exc:
                logger.error(f"{crawler_name} generated an exception: {exc}")
                
    # Store aggregated data in the database
    if all_articles:
        logger.info(f"Cleaning and deduplicating {len(all_articles)} total articles...")
        cleaner = NewsDataCleaner(db_manager)
        clean_articles = cleaner.clean_and_deduplicate(all_articles)
        
        if clean_articles:
            logger.info(f"Inserting {len(clean_articles)} clean articles into database...")
            db_manager.insert_articles(clean_articles)
        else:
            logger.warning("All fetched articles were duplicates. Nothing to store.")
        
        # Run daily cleanup logic explicitly for demo purposes (can be cron-scheduled)
        cleaner.run_daily_database_cleanup()
        
        # Export data to JSON and CSV formats
        logger.info("Exporting data to JSON and CSV...")
        json_path = os.path.join(os.path.dirname(__file__), "data", "articles_export.json")
        csv_path = os.path.join(os.path.dirname(__file__), "data", "articles_export.csv")
        
        db_manager.export_to_json(json_path)
        db_manager.export_to_csv(csv_path)
    else:
        logger.warning("No articles were scraped. Nothing to store or export.")
        
    logger.info("Phase 1 completed successfully.")

if __name__ == "__main__":
    main()
