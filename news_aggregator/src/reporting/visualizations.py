import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os

logger = logging.getLogger(__name__)

class Visualizations:
    """Generates analytical charts using Matplotlib and Seaborn."""
    
    def __init__(self, output_dir: str = "plots"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def plot_sentiment_timeline(self, df: pd.DataFrame):
        """Outputs a sentiment timeline over time."""
        if 'date' not in df.columns or df['date'].isnull().all():
            logger.warning("No valid date data found for timeline plot. Skipping timeline visualization.")
            return
            
        plt.figure(figsize=(12, 6))
        # Group by date and calculate mean sentiment
        daily_sentiment = df.groupby(df['date'].dt.date)['sentiment_score'].mean().reset_index()
        
        sns.lineplot(data=daily_sentiment, x='date', y='sentiment_score', marker='o')
        plt.title('Average Daily Sentiment Over Time')
        plt.xlabel('Date')
        plt.ylabel('Average Sentiment Score (-1 to 1)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'sentiment_timeline.png')
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved sentiment timeline chart to {output_path}")

    def plot_source_comparison(self, df: pd.DataFrame):
        """Outputs a source comparison chart for sentiment."""
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=df, x='source', y='sentiment_score', palette='Set3')
        plt.title('Sentiment Distribution by News Source')
        plt.xlabel('News Source')
        plt.ylabel('Sentiment Score (-1 to 1)')
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'source_comparison.png')
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved source comparison chart to {output_path}")

    def plot_topic_heatmap(self, df: pd.DataFrame):
        """Outputs a heatmap of sentiment by category and source."""
        if 'category' not in df.columns:
            logger.warning("No category data found for heatmap.")
            return
            
        plt.figure(figsize=(10, 8))
        # Create a pivot table: rows=category, cols=source, values=mean sentiment
        pivot_data = df.pivot_table(
            values='sentiment_score', 
            index='category', 
            columns='source', 
            aggfunc='mean'
        )
        
        if pivot_data.empty:
            logger.warning("Pivot data is empty, skipping heatmap.")
            return

        sns.heatmap(pivot_data, annot=True, cmap='RdYlGn', center=0, fmt=".2f", cbar_kws={'label': 'Sentiment Score'})
        plt.title('Average Sentiment Heatmap by Source and Category')
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'topic_heatmap.png')
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved topic heatmap to {output_path}")
