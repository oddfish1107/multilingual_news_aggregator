import unittest
import sys
import os
from unittest.mock import patch

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawlers.crawler_engine import VnExpressCrawler, BBCCrawler
from src.utils.utils import filter_text

class TestCrawlers(unittest.TestCase):
    
    def setUp(self):
        self.vn_crawler = VnExpressCrawler()
        self.bbc_crawler = BBCCrawler()

    def test_filter_text(self):
        """Test the lambda-based text filtering utility."""
        raw_text = "   This is \n  some \t messy text.   "
        expected = "This is some messy text."
        self.assertEqual(filter_text(raw_text), expected)
        self.assertEqual(filter_text(""), "")
        self.assertEqual(filter_text(None), "")

    @patch('src.crawlers.crawler_engine.requests.get')
    def test_vnexpress_crawler_parse(self, mock_get):
        """Test parsing logic of VnExpressCrawler."""
        # Provide some dummy HTML to simulate a response
        dummy_html = '''
        <html>
            <body>
                <article class="item-news">
                    <h3 class="title-news"><a href="#">Test Title 1</a></h3>
                    <p class="description"><a href="#">Test Description 1</a></p>
                </article>
            </body>
        </html>
        '''
        articles = self.vn_crawler.parse(dummy_html)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'Test Title 1')
        self.assertEqual(articles[0]['content'], 'Test Description 1')
        self.assertEqual(articles[0]['category'], 'News')

    @patch('src.crawlers.crawler_engine.webdriver.Chrome')
    def test_bbc_crawler_parse(self, mock_chrome):
        """Test parsing logic of BBCCrawler."""
        dummy_html = '''
        <html>
            <body>
                <div data-testid="edgel">
                    <h2>BBC Test Title</h2>
                    <p>BBC Test Description</p>
                </div>
            </body>
        </html>
        '''
        articles = self.bbc_crawler.parse(dummy_html)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'BBC Test Title')
        self.assertEqual(articles[0]['content'], 'BBC Test Description')

if __name__ == '__main__':
    unittest.main()
