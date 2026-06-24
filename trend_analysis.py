import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class TrendDetector:
    """
    Detects trending topics and keywords from text data using TF-IDF.
    
    Why TF-IDF? 
    TF-IDF (Term Frequency-Inverse Document Frequency) highlights words 
    that are frequent in a specific document (article) but rare across the entire dataset. 
    This algorithm is highly effective for finding "anomalous" or uniquely surging 
    topics compared to standard stop words (like "the", "and"), dynamically extracting 
    the core subject matter of breaking news.
    """
    def __init__(self, max_features=15):
        self.max_features = max_features

    def get_trending_keywords(self, df: pd.DataFrame, content_col='content') -> pd.DataFrame:
        """
        Calculates trending keywords across the given DataFrame.
        Returns a DataFrame of top keywords and their aggregated TF-IDF scores.
        """
        if df.empty or content_col not in df.columns:
            logger.warning("No data available for trend detection.")
            return pd.DataFrame()

        # Handle missing text to avoid vectorizer errors
        corpus = df[content_col].fillna("").astype(str).tolist()
        
        # We use English stop words to filter out non-topical vocabulary.
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            # Raised if corpus is essentially empty or only contains stop words
            return pd.DataFrame()

        # Get the vocabulary (the actual words)
        feature_names = vectorizer.get_feature_names_out()
        
        # Sum the TF-IDF scores across all documents to find the overall 'trend' weight
        summed_tfidf = tfidf_matrix.sum(axis=0).A1
        
        # Map words to their summed scores
        keyword_scores = dict(zip(feature_names, summed_tfidf))
        
        # Sort and get the top N trending features
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:self.max_features]
        
        trend_df = pd.DataFrame(sorted_keywords, columns=['Keyword', 'Trend Score'])
        return trend_df
