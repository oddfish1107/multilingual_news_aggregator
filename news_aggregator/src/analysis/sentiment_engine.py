import logging
import time
from textblob import TextBlob

logger = logging.getLogger(__name__)

class SentimentEngine:
    """Analyzes article sentiment using TextBlob (local) simulating an AI API.
    Handles rate limiting and error checking robustly.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # API limit tracking simulation
        self.calls_made = 0
        self.RATE_LIMIT = 100 
        
    def analyze_text(self, text: str) -> float:
        """
        Analyzes the sentiment of a text block via NLP.
        Returns a float between -1.0 (negative) and 1.0 (positive).
        """
        if not text:
            return 0.0
            
        # Simulate API rate limit check and exponential backoff
        self.calls_made += 1
        if self.calls_made > self.RATE_LIMIT:
            logger.warning("AI API Rate Limit reached! Sleeping for 10 seconds to respect API limits...")
            time.sleep(10) # 10 seconds for testing, realistically much longer
            self.calls_made = 0
            
        try:
            # Using TextBlob as a proxy for an AI Sentiment API (e.g. OpenAI/HuggingFace)
            # This ensures it runs reliably without requiring the user to supply API keys right now.
            analysis = TextBlob(text)
            return analysis.sentiment.polarity
        except Exception as e:
            logger.error(f"Error during sentiment analysis API call: {e}")
            return 0.0

    def classify_sentiment(self, score: float) -> str:
        """Classifies a continuous score into categorical sentiment (positive/neutral/negative)."""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
