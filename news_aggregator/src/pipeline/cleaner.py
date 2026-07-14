import pandas as pd
import hashlib
import re
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.utils.utils import timing_decorator, logging_decorator, logger
import sqlite3
from datetime import datetime, timedelta

class NewsDataCleaner:
    """Handles data normalization, exact deduplication, and fuzzy semantic deduplication."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def normalize_text(self, text: str) -> str:
        """Normalizes text by lowercasing, stripping whitespace, and removing HTML."""
        if not text:
            return ""
        # Remove HTML tags if any slipped through
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespaces
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        # Lowercase
        return clean_text.lower()

    def generate_fingerprint(self, text: str) -> str:
        """Generates an SHA-256 hash of the cleaned text."""
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @timing_decorator
    def exact_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Performs exact deduplication based on URL, normalized title, and content hash."""
        if df.empty:
            return df
            
        initial_len = len(df)
        
        # Add a normalized title column for exact matching
        df['norm_title'] = df['title'].apply(self.normalize_text)
        
        # Deduplicate by URL (if exists)
        if 'url' in df.columns:
            df = df.drop_duplicates(subset=['url'], keep='first')
            
        # Deduplicate by normalized title
        df = df.drop_duplicates(subset=['norm_title'], keep='first')
        
        # Deduplicate by content hash
        if 'content_hash' in df.columns:
            df = df.drop_duplicates(subset=['content_hash'], keep='first')
            
        # Drop the temporary column
        df = df.drop(columns=['norm_title'])
        
        final_len = len(df)
        logger.info(f"Exact Deduplication: Removed {initial_len - final_len} exact duplicates within the batch.")
        return df

    @timing_decorator
    def fuzzy_deduplicate(self, new_df: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
        """
        Uses TF-IDF and Cosine Similarity to find near-duplicates in the new data
        against articles from the last 72 hours in the database.
        Appends alternative sources instead of keeping duplicate articles.
        """
        if new_df.empty:
            return new_df

        # Fetch recent articles from DB (last 72 hours)
        recent_articles = []
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, a.title, a.content, s.name as source, a.content_hash, a.alt_sources 
                    FROM Articles a
                    JOIN Sources s ON a.source_id = s.id
                    WHERE a.date >= datetime('now', '-3 days')
                """)
                recent_articles = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Fuzzy Deduplication DB fetch failed: {e}")

        # If DB is empty, just return the new batch
        if not recent_articles:
            return new_df
            
        db_df = pd.DataFrame(recent_articles)
        
        # Prepare corpora
        new_texts = new_df['title'] + " " + new_df['content']
        db_texts = db_df['title'] + " " + db_df['content']
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        
        try:
            # Fit on both sets to ensure vocabulary matches
            all_texts = pd.concat([db_texts, new_texts])
            vectorizer.fit(all_texts)
            
            db_vectors = vectorizer.transform(db_texts)
            new_vectors = vectorizer.transform(new_texts)
            
            # Calculate cosine similarity matrix (new_articles x db_articles)
            sim_matrix = cosine_similarity(new_vectors, db_vectors)
            
            duplicates_to_drop = []
            
            for i in range(len(new_df)):
                # Find the maximum similarity with any DB article
                max_sim_idx = sim_matrix[i].argmax()
                max_sim_score = sim_matrix[i][max_sim_idx]
                
                if max_sim_score >= threshold:
                    # Near duplicate found
                    new_source = new_df.iloc[i]['source']
                    matched_db_article = db_df.iloc[max_sim_idx]
                    
                    # Log the duplicate
                    logger.debug(f"Fuzzy Match ({max_sim_score:.2f}): '{new_df.iloc[i]['title']}' matches '{matched_db_article['title']}'")
                    
                    # We will append the new source to the alt_sources of the DB article.
                    # Since we use UPSERT in the DB layer based on content_hash, 
                    # we can update the new article's content_hash to match the DB article's hash.
                    # This will trigger an UPDATE in the database instead of an INSERT.
                    new_df.at[new_df.index[i], 'content_hash'] = matched_db_article['content_hash']
                    new_df.at[new_df.index[i], 'alt_sources'] = new_source
                    
                    # Wait, if we keep it, UPSERT will overwrite the title/content with the new one.
                    # If we want to KEEP the earliest published, we should NOT send it for UPSERT.
                    # BUT we want to append the source.
                    # Let's just drop it from new_df and perform an explicit UPDATE on the DB.
                    duplicates_to_drop.append(new_df.index[i])
                    
                    try:
                        with sqlite3.connect(self.db_manager.db_path) as conn:
                            cursor = conn.cursor()
                            article_id = int(matched_db_article['id'])
                            cursor.execute("SELECT alt_sources FROM Articles WHERE id = ?", (article_id,))
                            row = cursor.fetchone()
                            current_alt = row[0] if row and row[0] else ""
                            
                            if new_source not in current_alt:
                                new_alt = f"{current_alt},{new_source}" if current_alt else new_source
                                cursor.execute("UPDATE Articles SET alt_sources = ? WHERE id = ?", (new_alt, article_id))
                            conn.commit()
                    except Exception as e:
                        logger.error(f"Failed to update alt_sources in DB: {e}")
            
            initial_len = len(new_df)
            new_df = new_df.drop(index=duplicates_to_drop)
            final_len = len(new_df)
            
            logger.info(f"Fuzzy Deduplication: Merged {initial_len - final_len} near-duplicates (threshold={threshold}).")
            return new_df
            
        except Exception as e:
            logger.error(f"Fuzzy deduplication computation failed: {e}")
            return new_df

    @timing_decorator
    def clean_and_deduplicate(self, raw_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Main pipeline entrypoint to clean data and remove exact and fuzzy duplicates."""
        if not raw_articles:
            return []
            
        df = pd.DataFrame(raw_articles)
        
        # 1. Clean and Generate Hashes
        df['clean_content'] = df['content'].apply(self.normalize_text)
        df['content_hash'] = df['clean_content'].apply(self.generate_fingerprint)
        df = df.drop(columns=['clean_content'])
        
        # 2. Exact Deduplication (within the batch)
        df = self.exact_deduplicate(df)
        
        # 3. Fuzzy Deduplication (against Database)
        df = self.fuzzy_deduplicate(df)
        
        return df.to_dict('records')

    @logging_decorator
    @timing_decorator
    def run_daily_database_cleanup(self):
        """
        Scheduled maintenance task.
        Scans recent database records to merge any near-duplicates that might have 
        bypassed the batch deduplication process.
        """
        logger.info("Running daily database cleanup and semantic deduplication...")
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, a.title, a.content, s.name as source, a.alt_sources 
                    FROM Articles a
                    JOIN Sources s ON a.source_id = s.id
                    WHERE a.date >= datetime('now', '-3 days')
                """)
                articles = [dict(row) for row in cursor.fetchall()]
                
            if not articles:
                logger.info("No recent articles to clean up.")
                return
                
            df = pd.DataFrame(articles)
            texts = df['title'] + " " + df['content']
            
            vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
            vectors = vectorizer.fit_transform(texts)
            sim_matrix = cosine_similarity(vectors)
            
            duplicates_merged = 0
            to_delete_ids = []
            
            # Find pairs with similarity > 0.85
            for i in range(len(df)):
                if df.iloc[i]['id'] in to_delete_ids:
                    continue
                    
                for j in range(i + 1, len(df)):
                    if sim_matrix[i][j] >= 0.85 and df.iloc[j]['id'] not in to_delete_ids:
                        # Keep i, delete j. Merge source from j to i
                        id_keep = df.iloc[i]['id']
                        id_del = df.iloc[j]['id']
                        source_del = df.iloc[j]['source']
                        
                        to_delete_ids.append(id_del)
                        duplicates_merged += 1
                        
                        with sqlite3.connect(self.db_manager.db_path) as conn:
                            cur = conn.cursor()
                            id_keep_int = int(id_keep)
                            cur.execute("SELECT alt_sources FROM Articles WHERE id = ?", (id_keep_int,))
                            row = cur.fetchone()
                            current_alt = row[0] if row and row[0] else ""
                            
                            if source_del not in current_alt:
                                new_alt = f"{current_alt},{source_del}" if current_alt else source_del
                                cur.execute("UPDATE Articles SET alt_sources = ? WHERE id = ?", (new_alt, id_keep_int))
                                
                            # Delete the duplicate
                            cur.execute("DELETE FROM Articles WHERE id = ?", (int(id_del),))
                            conn.commit()
                            
            logger.info(f"Daily Cleanup complete: Scanned {len(articles)} records, merged {duplicates_merged} near-duplicates.")
            
        except Exception as e:
            logger.error(f"Daily database cleanup failed: {e}")
