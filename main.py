import concurrent.futures
from crawler_engine import VnExpressCrawler, BBCCrawler
from database_manager import DatabaseManager
from utils import timing_decorator, logger
import os

@timing_decorator
def main():
    logger.info("Starting Phase 1: Crawling & Storage")
    
    db_path = os.path.join(os.path.dirname(__file__), "news_aggregator.db")
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
        logger.info(f"Inserting {len(all_articles)} total articles into database...")
        db_manager.insert_articles(all_articles)
        
        # Export data to JSON and CSV formats
        logger.info("Exporting data to JSON and CSV...")
        json_path = os.path.join(os.path.dirname(__file__), "articles_export.json")
        csv_path = os.path.join(os.path.dirname(__file__), "articles_export.csv")
        
        db_manager.export_to_json(json_path)
        db_manager.export_to_csv(csv_path)
    else:
        logger.warning("No articles were scraped. Nothing to store or export.")
        
    logger.info("Phase 1 completed successfully.")

if __name__ == "__main__":
    main()
