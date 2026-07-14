import pytest
import pandas as pd
import sqlite3
import os
from src.pipeline.cleaner import NewsDataCleaner

class MockDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test_news.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE Sources (id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL);
        CREATE TABLE Articles (
            id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE, content TEXT, content_hash TEXT UNIQUE,
            source_id INTEGER, alt_sources TEXT, date TEXT, category TEXT, sentiment_score REAL
        );
        INSERT INTO Sources (id, name, url) VALUES (1, 'VnExpress', 'https://vnexpress.net');
        INSERT INTO Articles (title, url, content, content_hash, source_id, date) 
        VALUES ('Test Article 1', 'http://test.com/1', 'This is a test article.', 'hash1', 1, datetime('now'));
    """)
    conn.commit()
    conn.close()
    return MockDatabaseManager(str(db_path))

def test_normalize_text():
    cleaner = NewsDataCleaner(None)
    assert cleaner.normalize_text("  <p>Hello World!</p>  ") == "hello world!"

def test_generate_fingerprint():
    cleaner = NewsDataCleaner(None)
    hash1 = cleaner.generate_fingerprint("test content")
    hash2 = cleaner.generate_fingerprint("test content")
    assert hash1 == hash2
    assert len(hash1) == 64

def test_exact_deduplicate():
    cleaner = NewsDataCleaner(None)
    df = pd.DataFrame([
        {'title': 'A', 'url': 'http://a.com', 'content_hash': '1'},
        {'title': 'A ', 'url': 'http://b.com', 'content_hash': '2'}, # Duplicate norm_title
        {'title': 'C', 'url': 'http://a.com', 'content_hash': '3'}, # Duplicate URL
        {'title': 'D', 'url': 'http://d.com', 'content_hash': '1'}  # Duplicate content hash
    ])
    dedup_df = cleaner.exact_deduplicate(df)
    assert len(dedup_df) == 1
    assert dedup_df.iloc[0]['title'] == 'A'

def test_fuzzy_deduplicate(mock_db):
    cleaner = NewsDataCleaner(mock_db)
    new_df = pd.DataFrame([
        # Almost identical to the DB article
        {'title': 'Test Article 1 Update', 'content': 'This is a test article with slight changes.', 'source': 'BBC', 'url': 'http://bbc.com/1', 'content_hash': 'newhash'}
    ])
    dedup_df = cleaner.fuzzy_deduplicate(new_df, threshold=0.6) # Lower threshold for short text
    
    # It should be dropped from new_df
    assert len(dedup_df) == 0
    
    # Check DB to see if alt_sources was updated
    conn = sqlite3.connect(mock_db.db_path)
    cur = conn.cursor()
    cur.execute("SELECT alt_sources FROM Articles WHERE id = 1")
    alt_sources = cur.fetchone()[0]
    conn.close()
    
    assert 'BBC' in alt_sources
