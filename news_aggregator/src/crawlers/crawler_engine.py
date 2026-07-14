from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.utils.utils import timing_decorator, logging_decorator, logger, filter_text

class BaseCrawler(ABC):
    """Abstract base class for all news crawlers."""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url

    @abstractmethod
    def fetch_page(self, url: str) -> Any:
        """Fetches the page content. To be implemented by subclasses."""
        pass

    @abstractmethod
    def parse(self, html_content: Any) -> List[Dict[str, Any]]:
        """Parses the content and extracts articles. To be implemented by subclasses."""
        pass
        
    @logging_decorator
    @timing_decorator
    def crawl(self, url: str) -> List[Dict[str, Any]]:
        """Main crawl method that utilizes fetch and parse."""
        try:
            content = self.fetch_page(url)
            articles = self.parse(content)
            
            # Use map and lambda for batch processing (cleaning titles/content)
            # Map applies a formatting/cleaning lambda to each article dictionary
            processed_articles = list(map(
                lambda a: {
                    **a,
                    'title': filter_text(a.get('title', '')),
                    'url': a.get('url', ''),
                    'content': filter_text(a.get('content', '')),
                    'source': self.name,
                    'source_url': self.base_url
                }, 
                articles
            ))
            return processed_articles
            
        except Exception as e:
            logger.error(f"Crawl failed for {self.name} at {url}: {e}")
            return []


class VnExpressCrawler(BaseCrawler):
    """Crawler for VnExpress using BeautifulSoup (Static site scraping)."""
    
    def __init__(self):
        super().__init__(name="VnExpress", base_url="https://vnexpress.net")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_page(self, url: str) -> str:
        """Fetches HTML using requests (handling static requests)."""
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.text

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """Parses static HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Selectors specific to VnExpress article structure
        for article_elem in soup.select('article.item-news'):
            title_elem = article_elem.select_one('h3.title-news a')
            desc_elem = article_elem.select_one('p.description a')
            
            if title_elem and desc_elem:
                url = title_elem.get('href', '')
                articles.append({
                    'title': title_elem.text,
                    'url': url,
                    'content': desc_elem.text,
                    'category': 'News',
                    'date': None # Add date extraction as needed based on site
                })
        return articles


class BBCCrawler(BaseCrawler):
    """Crawler for BBC using Selenium (Dynamic site scraping)."""
    
    def __init__(self):
        super().__init__(name="BBC", base_url="https://www.bbc.com")
        
    def fetch_page(self, url: str) -> str:
        """Fetches HTML using Selenium for JavaScript rendering."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Requires chromedriver to be installed and in PATH
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            # You could add explicit waits here for dynamic elements
            return driver.page_source
        finally:
            driver.quit()

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """Parses HTML after JS rendering, using BeautifulSoup."""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Selectors specific to BBC structure
        for article_elem in soup.select('[data-testid="edgel"]'):
            title_elem = article_elem.select_one('h2')
            desc_elem = article_elem.select_one('p')
            link_elem = article_elem.select_one('a')
            
            if title_elem:
                url = link_elem.get('href', '') if link_elem else ''
                if url and url.startswith('/'):
                    url = f"https://www.bbc.com{url}"
                articles.append({
                    'title': title_elem.text,
                    'url': url,
                    'content': desc_elem.text if desc_elem else "No description",
                    'category': 'World',
                    'date': None
                })
        return articles
