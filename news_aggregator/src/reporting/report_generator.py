import pandas as pd
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates automated daily reports and exports data into CSV/JSON."""
    
    def generate_daily_report(self, df: pd.DataFrame, output_prefix: str = "daily_report"):
        """Summarizes the day's news and sentiment, exporting to CSV and JSON."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # For a true daily report, we'd filter by today's date:
        # today_df = df[df['date'].dt.date == pd.to_datetime('today').date()]
        # Here we summarize the passed DataFrame as the target "run" data
        today_df = df
        
        if today_df.empty:
            logger.warning("No data available to generate daily report.")
            return
            
        # Compile Summary Statistics
        summary = {
            "report_date": today_str,
            "total_articles": len(today_df),
            "average_sentiment": round(float(today_df['sentiment_score'].mean()), 4),
            "sources_analyzed": int(today_df['source'].nunique()),
            "sentiment_breakdown": {
                "positive": int(len(today_df[today_df['sentiment_score'] > 0.1])),
                "neutral": int(len(today_df[(today_df['sentiment_score'] >= -0.1) & (today_df['sentiment_score'] <= 0.1)])),
                "negative": int(len(today_df[today_df['sentiment_score'] < -0.1]))
            }
        }
        
        # Export JSON Summary
        json_path = f"{output_prefix}_{today_str}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4)
        logger.info(f"Generated JSON summary report: {json_path}")
        
        # Export Detailed CSV Data
        csv_path = f"{output_prefix}_details_{today_str}.csv"
        # Select useful columns for the detail report
        report_cols = ['title', 'source', 'category', 'sentiment_score']
        if 'date' in today_df.columns:
            report_cols.append('date')
            
        today_df[report_cols].to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Generated CSV detailed report: {csv_path}")
