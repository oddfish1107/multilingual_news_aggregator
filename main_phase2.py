import logging
import os
from data_pipeline import DataPipeline
from sentiment_engine import SentimentEngine
from visualizations import Visualizations
from report_generator import ReportGenerator

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Phase 2: Analysis & AI Integration")
    
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, "news_aggregator.db")
    
    # 1. Initialize Modules
    pipeline = DataPipeline(db_path=db_path)
    sentiment_engine = SentimentEngine()
    viz = Visualizations(output_dir=os.path.join(base_dir, "plots"))
    reporter = ReportGenerator()
    
    # 2. Data Pipeline: Fetch and Clean
    df = pipeline.fetch_articles()
    
    if df.empty:
        logger.warning("No articles found in the database. Please run Phase 1 crawler first.")
        return
        
    df = pipeline.clean_and_deduplicate(df)
    df = pipeline.setup_time_series(df)
    
    # 3. Sentiment Engine: Analyze & Update Database
    logger.info("Starting AI Sentiment Analysis...")
    updates = []
    
    # Iterate through articles to calculate sentiment
    for index, row in df.iterrows():
        # TextBlob acts as our AI API proxy here
        score = sentiment_engine.analyze_text(row['content'])
        df.at[index, 'sentiment_score'] = score
        updates.append((score, row['id']))
        
    # Write updated scores back to SQLite
    pipeline.update_sentiment_scores(updates)
    
    # 4. Visualizations: Generate Analytical Charts
    logger.info("Generating Visualizations...")
    viz.plot_sentiment_timeline(df)
    viz.plot_source_comparison(df)
    viz.plot_topic_heatmap(df)
    
    # 5. Automated Daily Report
    logger.info("Generating Automated Daily Reports...")
    report_output_path = os.path.join(base_dir, "daily_report")
    reporter.generate_daily_report(df, output_prefix=report_output_path)
    
    logger.info("Phase 2 pipeline completed successfully. Plots and reports have been generated.")

if __name__ == "__main__":
    main()
