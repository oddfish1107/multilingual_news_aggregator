import sqlite3
import json
import csv
from typing import List, Dict, Any
from src.utils.utils import timing_decorator, logging_decorator, logger
import os

class DatabaseManager:
    """Manages the SQLite database operations for the news aggregator."""
    
    def __init__(self, db_path: str = "news_data_v2.db"):
        self.db_path = db_path
        self._initialize_db()
        
    @logging_decorator
    def _initialize_db(self):
        """Creates the normalized database schema if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create Sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL
                    )
                """)
                
                # Create Articles table with deduplication columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE,
                        content TEXT NOT NULL,
                        content_hash TEXT UNIQUE,
                        source_id INTEGER,
                        alt_sources TEXT,
                        date TEXT,
                        category TEXT,
                        sentiment_score REAL,
                        FOREIGN KEY (source_id) REFERENCES Sources(id)
                    )
                """)
                
                # Create Keywords table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT UNIQUE NOT NULL
                    )
                """)
                
                # Create Article_Keywords junction table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Article_Keywords (
                        article_id INTEGER,
                        keyword_id INTEGER,
                        PRIMARY KEY (article_id, keyword_id),
                        FOREIGN KEY (article_id) REFERENCES Articles(id),
                        FOREIGN KEY (keyword_id) REFERENCES Keywords(id)
                    )
                """)
                
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
            
    def get_or_create_source(self, name: str, url: str) -> int:
        """Retrieves an existing source ID or creates a new one."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Sources WHERE name = ?", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            cursor.execute("INSERT INTO Sources (name, url) VALUES (?, ?)", (name, url))
            conn.commit()
            return cursor.lastrowid
            
    @timing_decorator
    def insert_articles(self, articles_data: List[Dict[str, Any]]):
        """Inserts a batch of articles into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for article in articles_data:
                source_id = self.get_or_create_source(article['source'], article.get('source_url', ''))
                # Implement UPSERT using content_hash
                cursor.execute("""
                    INSERT INTO Articles (title, url, content, content_hash, source_id, alt_sources, date, category, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(content_hash) DO UPDATE SET 
                        alt_sources = CASE 
                            WHEN alt_sources IS NULL OR alt_sources = '' THEN excluded.alt_sources 
                            WHEN instr(alt_sources, excluded.alt_sources) = 0 THEN alt_sources || ',' || excluded.alt_sources
                            ELSE alt_sources 
                        END
                """, (
                    article['title'], 
                    article.get('url'),
                    article['content'], 
                    article.get('content_hash', ''),
                    source_id, 
                    article.get('alt_sources', ''),
                    article.get('date'), 
                    article.get('category'), 
                    article.get('sentiment_score', 0.0)
                ))
            conn.commit()

    @timing_decorator
    def export_to_json(self, output_path: str = "articles.json"):
        """Exports all articles to a JSON file."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.title, a.url, a.content, s.name as source, a.date, a.category, a.sentiment_score
                FROM Articles a
                JOIN Sources s ON a.source_id = s.id
            """)
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Exported {len(data)} articles to {output_path}")

    @timing_decorator
    def export_to_csv(self, output_path: str = "articles.csv"):
        """Exports all articles to a CSV file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.title, a.url, a.content, s.name as source, a.date, a.category, a.sentiment_score
                FROM Articles a
                JOIN Sources s ON a.source_id = s.id
            """)
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("No data to export.")
                return
                
            headers = [description[0] for description in cursor.description]
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            logger.info(f"Exported {len(rows)} articles to {output_path}")
