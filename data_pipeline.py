import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataPipeline:
    """Handles fetching, cleaning, and formatting data from SQLite using Pandas."""
    
    def __init__(self, db_path: str = "news_aggregator.db"):
        self.db_path = db_path
        
    def fetch_articles(self) -> pd.DataFrame:
        """Fetches articles from SQLite database into a Pandas DataFrame."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT a.id, a.title, a.content, s.name as source, a.date, a.category, a.sentiment_score
                    FROM Articles a
                    JOIN Sources s ON a.source_id = s.id
                """
                df = pd.read_sql_query(query, conn)
                logger.info(f"Fetched {len(df)} articles from database.")
                return df
        except sqlite3.Error as e:
            logger.error(f"Error fetching data from SQLite: {e}")
            raise
            
    def clean_and_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans missing data and removes duplicate articles."""
        initial_count = len(df)
        
        # Drop rows where essential content is missing
        df.dropna(subset=['title', 'content'], inplace=True)
        
        # Remove exact duplicates based on title and source
        df.drop_duplicates(subset=['title', 'source'], keep='first', inplace=True)
        
        # Standardize missing dates or categories
        df['category'] = df['category'].fillna('Unknown')
        
        logger.info(f"Cleaned data. Reduced from {initial_count} to {len(df)} rows.")
        return df
        
    def setup_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts date columns to datetime objects for time-series analysis."""
        if 'date' in df.columns:
            # Convert to datetime, handling missing or unparseable dates
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df

    def update_sentiment_scores(self, article_scores: list):
        """Batch updates sentiment scores in the database.
        
        Args:
            article_scores (list): List of tuples containing (score, article_id)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "UPDATE Articles SET sentiment_score = ? WHERE id = ?",
                    article_scores
                )
                conn.commit()
                logger.info(f"Successfully updated {len(article_scores)} sentiment scores in database.")
        except sqlite3.Error as e:
            logger.error(f"Error updating sentiment scores: {e}")
            raise
