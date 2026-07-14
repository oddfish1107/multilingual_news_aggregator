import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Append the parent directory to sys.path so we can import our core modules for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawlers.crawler_engine import VnExpressCrawler
from src.utils.utils import filter_text
from src.analysis.sentiment_engine import SentimentEngine
from src.analysis.trend_analysis import TrendDetector

# ---- 1. Test Text Processing Logic ----
def test_filter_text():
    """Unit test ensuring the lambda-based text cleaning handles edge cases."""
    raw = "   Breaking \n  News \t is here.   "
    expected = "Breaking News is here."
    assert filter_text(raw) == expected
    assert filter_text("") == ""
    assert filter_text(None) == ""

# ---- 2. Test Crawler Parsing Logic ----
def test_vnexpress_parse():
    """Unit test ensuring the static HTML parser extracts data perfectly."""
    crawler = VnExpressCrawler()
    dummy_html = '''
    <html>
        <body>
            <article class="item-news">
                <h3 class="title-news"><a href="#">Test Title</a></h3>
                <p class="description"><a href="#">Test Content</a></p>
            </article>
        </body>
    </html>
    '''
    articles = crawler.parse(dummy_html)
    assert len(articles) == 1
    assert articles[0]['title'] == 'Test Title'
    assert articles[0]['content'] == 'Test Content'

# ---- 3. Test AI Sentiment Logic ----
def test_sentiment_classification_thresholds():
    """Unit test ensuring continuous scores map accurately to categorical buckets."""
    engine = SentimentEngine()
    assert engine.classify_sentiment(0.5) == 'positive'
    assert engine.classify_sentiment(0.0) == 'neutral'
    assert engine.classify_sentiment(-0.2) == 'negative'

@patch('src.analysis.sentiment_engine.TextBlob')
def test_sentiment_analysis(mock_textblob):
    """
    Test the AI analysis engine using a mocked NLP library.
    This guarantees our tests don't fail due to external API limitations/network drops.
    """
    mock_analysis = MagicMock()
    mock_analysis.sentiment.polarity = 0.8
    mock_textblob.return_value = mock_analysis
    
    engine = SentimentEngine()
    score = engine.analyze_text("This is an amazing unit test!")
    assert score == 0.8
    
# ---- 4. Test Trend Detection Logic ----
def test_trend_detection():
    """
    Unit test for the TF-IDF anomaly detection.
    Words that appear frequently across small corpuses should score high.
    """
    df = pd.DataFrame({
        'content': [
            "Apple announces new iPhone.",
            "Apple stock rises after iPhone event.",
            "Normal news day today."
        ]
    })
    detector = TrendDetector(max_features=2)
    trends = detector.get_trending_keywords(df)
    
    assert not trends.empty
    keywords = trends['Keyword'].tolist()
    # TF-IDF should easily flag 'apple' or 'iphone' as trending topics
    assert 'apple' in keywords or 'iphone' in keywords
