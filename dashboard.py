import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from trend_analysis import TrendDetector

# ---- SYSTEM OPTIMIZATION: Caching the Data Fetch Layer ----
# Using @st.cache_data ensures that Streamlit caches the results of this expensive I/O operation.
# Even with thousands of rows in the SQLite DB, the database is queried only once per session 
# (or until the TTL expires), drastically improving dashboard load times and user experience.
@st.cache_data(ttl=600) # Cache expires after 10 minutes
def load_data(db_path="news_aggregator.db"):
    if not os.path.exists(db_path):
        return pd.DataFrame()
        
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT a.id, a.title, a.content, s.name as source, a.date, a.category, a.sentiment_score
                FROM Articles a
                JOIN Sources s ON a.source_id = s.id
            """
            df = pd.read_sql_query(query, conn)
            # Ensure dates are datetime objects for interactive filtering
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="News Sentiment Dashboard", layout="wide")
    st.title("🌐 Multilingual News Aggregator & Sentiment Dashboard")
    st.markdown("Live analytics, sentiment tracking, and topic detection powered by AI.")

    # Load data via the optimized cached function
    df = load_data()
    
    if df.empty:
        st.warning("No data found. Please run the Phase 1 & Phase 2 backend scripts to populate the database.")
        return

    # ---- INTERACTIVE FILTERS ----
    st.sidebar.header("Dashboard Filters")
    
    # 1. Source Filter
    all_sources = ["All"] + list(df['source'].unique())
    selected_source = st.sidebar.selectbox("Filter by News Source:", all_sources)
    
    # 2. Sentiment Polarity Filter
    sentiment_filter = st.sidebar.radio("Filter by Sentiment Polarity:", ["All", "Positive (>0.1)", "Neutral", "Negative (<-0.1)"])
    
    # Apply Filters to create the view
    filtered_df = df.copy()
    if selected_source != "All":
        filtered_df = filtered_df[filtered_df['source'] == selected_source]
        
    if sentiment_filter == "Positive (>0.1)":
        filtered_df = filtered_df[filtered_df['sentiment_score'] > 0.1]
    elif sentiment_filter == "Negative (<-0.1)":
        filtered_df = filtered_df[filtered_df['sentiment_score'] < -0.1]
    elif sentiment_filter == "Neutral":
        filtered_df = filtered_df[(filtered_df['sentiment_score'] >= -0.1) & (filtered_df['sentiment_score'] <= 0.1)]

    st.write(f"### Currently Viewing: {len(filtered_df)} Articles")

    # ---- VISUALIZATIONS ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Sentiment Timeline")
        valid_dates = filtered_df.dropna(subset=['date'])
        if not valid_dates.empty:
            # Group by date for the timeline rolling average
            daily_sentiment = valid_dates.groupby(valid_dates['date'].dt.date)['sentiment_score'].mean().reset_index()
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=daily_sentiment, x='date', y='sentiment_score', marker='o', ax=ax)
            ax.set_title("Average Daily Sentiment")
            ax.set_ylabel("Score (-1 to 1)")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No timeline data available for current filters.")

    with col2:
        st.subheader("🏢 Source Comparison")
        if not filtered_df.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.boxplot(data=filtered_df, x='source', y='sentiment_score', palette='Set3', ax=ax)
            ax.set_title("Sentiment Distribution by Source")
            st.pyplot(fig)
        else:
            st.info("No source data available for current filters.")

    st.subheader("🔥 Topic Tracking & Trend Detection")
    st.markdown("Utilizing Term Frequency-Inverse Document Frequency (TF-IDF) to surface anomalous topic surges.")
    
    # Using our custom TF-IDF trend detector
    trend_detector = TrendDetector(max_features=10)
    trending_keywords = trend_detector.get_trending_keywords(filtered_df, content_col='content')
    
    if not trending_keywords.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=trending_keywords, x='Trend Score', y='Keyword', palette='magma', ax=ax)
        ax.set_title("Top Trending Topics")
        st.pyplot(fig)
    else:
        st.info("Not enough text data to detect meaningful trends.")
        
    st.subheader("🗺️ Sentiment Heatmap")
    if not filtered_df.empty and 'category' in filtered_df.columns:
        pivot_data = filtered_df.pivot_table(values='sentiment_score', index='category', columns='source', aggfunc='mean')
        if not pivot_data.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.heatmap(pivot_data, annot=True, cmap='RdYlGn', center=0, fmt=".2f", ax=ax)
            ax.set_title("Average Sentiment by Category and Source")
            st.pyplot(fig)
    else:
        st.info("No categorical data available for heatmap.")

if __name__ == "__main__":
    main()
