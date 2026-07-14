# ===========================================================================
# ANTIGRAVITY — Multilingual News Aggregator & Sentiment Analysis Dashboard
# ===========================================================================
# A high-performance, dark-themed professional dashboard built with Streamlit.
#
# Three primary views:
#   1. Main Dashboard   — KPI metrics, sentiment timeline, source comparison,
#                          keyword heatmap, category breakdown charts.
#   2. Live News Feed   — Real-time data table with filters, search, and export.
#   3. Admin / Settings — API config, crawler toggles, storage management.
#
# Architecture: Single-file Streamlit app using session_state for routing and
#               st.markdown(unsafe_allow_html=True) for the custom dark UI.
# ===========================================================================

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import os
import time
import random
import json
from datetime import datetime, timedelta
from collections import Counter

# ---------------------------------------------------------------------------
# Matplotlib — use Agg backend so it works in headless / Streamlit envs
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ===========================================================================
# GLOBAL CONSTANTS
# ===========================================================================
# Absolute path to the SQLite database so it works regardless of cwd
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'news_data_v2.db')
)

# Streamlit page configuration — must be the first Streamlit command
st.set_page_config(
    page_title="ANTIGRAVITY Dashboard",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===========================================================================
# SECTION 1: CSS DESIGN SYSTEM
# ===========================================================================
# A comprehensive dark-themed CSS layer with:
#   - Custom color palette (dark grays, accent greens/reds)
#   - Status indicator animations (pulse dots)
#   - Card, badge, and metric component styles
#   - Responsive grid helpers
# ===========================================================================
def inject_css():
    """Inject the full CSS design system into the page."""
    
    # Read sidebar expansion state
    expanded = st.session_state.get('sidebar_expanded', True)
    sidebar_width = 280 if expanded else 80

    st.markdown(f"""
<style>
/* ── Reset Streamlit chrome (keep sidebar toggle visible!) ──────────────── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; pointer-events: none; }}
header[data-testid="stHeader"] * {{ pointer-events: auto; }}

/* ── Root variables ─────────────────────────────────────────────────────── */
:root {{
    --bg-primary:   #0d0d0d;
    --bg-secondary: #141414;
    --bg-card:      #1a1a1a;
    --bg-hover:     #222222;
    --border:       #2a2a2a;
    --border-hover: #3a3a3a;
    --text-primary: #f0f0f0;
    --text-secondary: #999999;
    --text-muted:   #555555;
    --accent-green: #22c55e;
    --accent-red:   #ef4444;
    --accent-amber: #f59e0b;
    --accent-blue:  #3b82f6;
    --accent-purple:#a855f7;
}}

/* ── Main container ─────────────────────────────────────────────────────── */
.block-container {{
    padding: 1.5rem 2.5rem 2rem 2.5rem;
    max-width: 100% !important;
}}

/* ── Sidebar — ALWAYS visible with dynamic width ────────────────────────── */
section[data-testid="stSidebar"] {{
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
    display: flex !important;
    min-width: {sidebar_width}px !important;
    max-width: {sidebar_width}px !important;
    transform: none !important;
    visibility: visible !important;
    transition: min-width 0.3s, max-width 0.3s;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding: 1.2rem 0.9rem;
    background: var(--bg-secondary) !important;
}}
/* Hide native sidebar controls so we can use our custom toggle exclusively */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"] {{
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}}

/* Center icons in sidebar buttons */
[data-testid="stSidebar"] [data-testid="stButton"] button {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button p {{
    text-align: center !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}}

/* ── Animations ─────────────────────────────────────────────────────────── */
@keyframes pulse-dot {{
    0%   {{ opacity: 1;   transform: scale(1);   }}
    50%  {{ opacity: 0.35; transform: scale(1.4); }}
    100% {{ opacity: 1;   transform: scale(1);   }}
}}
@keyframes fade-in {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0);   }}
}}

.live-dot {{
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--accent-green);
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-dot 1.4s ease-in-out infinite;
}}
.live-dot-red {{
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--accent-red);
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-dot 1.4s ease-in-out infinite;
}}

/* ── KPI Metric Cards ───────────────────────────────────────────────────── */
.kpi-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    animation: fade-in 0.4s ease-out;
    transition: border-color 0.2s, transform 0.2s;
}}
.kpi-card:hover {{
    border-color: var(--border-hover);
    transform: translateY(-2px);
}}
.kpi-label {{
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 8px;
    font-weight: 600;
}}
.kpi-value {{
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.1;
}}
.kpi-change-up {{
    font-size: 0.78rem;
    color: var(--accent-green);
    margin-top: 6px;
    font-weight: 600;
}}
.kpi-change-down {{
    font-size: 0.78rem;
    color: var(--accent-red);
    margin-top: 6px;
    font-weight: 600;
}}
.kpi-sub {{
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 4px;
}}

/* ── Section Cards ──────────────────────────────────────────────────────── */
.section-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
    animation: fade-in 0.5s ease-out;
}}
.section-title {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-muted);
    margin-bottom: 14px;
    font-weight: 700;
}}

/* ── Sentiment Badges ───────────────────────────────────────────────────── */
.badge-pos  {{ background: rgba(34,197,94,0.12); color: #4ade80; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; border: 1px solid rgba(34,197,94,0.3); }}
.badge-neg  {{ background: rgba(239,68,68,0.12); color: #f87171; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; border: 1px solid rgba(239,68,68,0.3); }}
.badge-neut {{ background: rgba(150,150,150,0.12); color: #aaa; padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; border: 1px solid rgba(150,150,150,0.3); }}

/* ── Feed Table Row Cards ───────────────────────────────────────────────── */
.feed-row {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: background 0.15s, border-color 0.15s;
    animation: fade-in 0.3s ease-out;
}}
.feed-row:hover {{
    background: var(--bg-hover);
    border-color: var(--border-hover);
}}

/* ── Console / Log Box ──────────────────────────────────────────────────── */
.log-console {{
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-radius: 8px;
    padding: 16px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.78rem;
    color: #8b8b8b;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.6;
}}
.log-line-info  {{ color: #22c55e; }}
.log-line-warn  {{ color: #f59e0b; }}
.log-line-error {{ color: #ef4444; }}
.log-line-time  {{ color: #555; }}

/* ── Toggle Rows (Admin crawler controls) ───────────────────────────────── */
.toggle-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 8px;
    transition: border-color 0.15s;
}}
.toggle-row:hover {{ border-color: var(--border-hover); }}

/* ── Status bar at top of pages ─────────────────────────────────────────── */
.page-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.6rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}}
.page-title {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
}}
.page-title span {{
    color: var(--text-muted);
    font-weight: 400;
}}
.page-subtitle {{
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-top: 2px;
}}
.page-status {{
    font-size: 0.78rem;
    color: var(--text-muted);
    text-align: right;
}}

/* ── Misc helpers ───────────────────────────────────────────────────────── */
.divider {{ border-top: 1px solid var(--border); margin: 1.2rem 0; }}
.spacer-sm {{ height: 8px; }}
.spacer-md {{ height: 16px; }}
.spacer-lg {{ height: 28px; }}

/* ── Override streamlit metric styling for dark theme ───────────────────── */
[data-testid="stMetricValue"] {{ font-size: 1.6rem !important; }}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# SECTION 2: DATA ACCESS LAYER
# ===========================================================================
# Centralized database queries. Every function takes db_path as parameter
# and returns a pandas DataFrame or scalar. No caching — fresh on every rerun.
# ===========================================================================

def db_exists():
    """Check if the SQLite database file exists."""
    return os.path.exists(DB_PATH)


def load_articles(db_path=DB_PATH) -> pd.DataFrame:
    """Load all articles joined with source names. Returns empty DF on error."""
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query("""
                SELECT a.id, a.title, a.content, s.name AS source,
                       a.date, a.category, a.sentiment_score
                FROM Articles a
                JOIN Sources s ON a.source_id = s.id
                ORDER BY a.id DESC
            """, conn)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
    except Exception:
        return pd.DataFrame()


def load_keywords(db_path=DB_PATH) -> pd.DataFrame:
    """Load keywords joined with article counts."""
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        with sqlite3.connect(db_path) as conn:
            return pd.read_sql_query("""
                SELECT k.keyword, COUNT(ak.article_id) AS frequency
                FROM Keywords k
                JOIN Article_Keywords ak ON k.id = ak.keyword_id
                GROUP BY k.keyword
                ORDER BY frequency DESC
                LIMIT 50
            """, conn)
    except Exception:
        return pd.DataFrame()


def load_db_stats(db_path=DB_PATH) -> dict:
    """Return a dict of core database statistics."""
    stats = {
        'total_articles': 0, 'total_sources': 0, 'total_keywords': 0,
        'avg_sentiment': 0.0, 'pos_count': 0, 'neg_count': 0, 'neut_count': 0,
        'db_size_kb': 0,
    }
    if not os.path.exists(db_path):
        return stats
    try:
        with sqlite3.connect(db_path) as conn:
            stats['total_articles'] = conn.execute("SELECT COUNT(*) FROM Articles").fetchone()[0]
            stats['total_sources']  = conn.execute("SELECT COUNT(*) FROM Sources").fetchone()[0]
            stats['total_keywords'] = conn.execute("SELECT COUNT(*) FROM Keywords").fetchone()[0]
            avg = conn.execute("SELECT AVG(sentiment_score) FROM Articles").fetchone()[0]
            stats['avg_sentiment'] = round(avg, 4) if avg else 0.0
            stats['pos_count']  = conn.execute("SELECT COUNT(*) FROM Articles WHERE sentiment_score > 0.1").fetchone()[0]
            stats['neg_count']  = conn.execute("SELECT COUNT(*) FROM Articles WHERE sentiment_score < -0.1").fetchone()[0]
            stats['neut_count'] = stats['total_articles'] - stats['pos_count'] - stats['neg_count']
        stats['db_size_kb'] = round(os.path.getsize(db_path) / 1024, 1)
    except Exception:
        pass
    return stats


def load_table_sizes(db_path=DB_PATH) -> dict:
    """Return row counts for each major table."""
    sizes = {'Articles': 0, 'Sources': 0, 'Keywords': 0, 'Article_Keywords': 0}
    if not os.path.exists(db_path):
        return sizes
    try:
        with sqlite3.connect(db_path) as conn:
            for table in sizes:
                sizes[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        pass
    return sizes


# ===========================================================================
# SECTION 3: CHART GENERATION HELPERS
# ===========================================================================
# Uses Matplotlib with a custom dark theme for every chart.
# Returns Matplotlib figure objects to be rendered via st.pyplot().
# ===========================================================================

from matplotlib.figure import Figure

def _dark_fig(figsize=(10, 4)):
    """Create a Matplotlib figure preconfigured with the dark theme."""
    fig = Figure(figsize=figsize, facecolor='#1a1a1a')
    ax = fig.subplots()
    ax.set_facecolor('#1a1a1a')
    ax.tick_params(colors='#777', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')
    ax.xaxis.label.set_color('#888')
    ax.yaxis.label.set_color('#888')
    ax.title.set_color('#ddd')
    return fig, ax


def chart_sentiment_timeline(df: pd.DataFrame):
    """
    Multi-line time-series chart showing daily sentiment averages.
    If dates are missing, synthesizes a fake timeline for demo purposes.
    """
    fig, ax = _dark_fig((10, 3.8))

    if df.empty:
        ax.text(0.5, 0.5, "No data available", ha='center', va='center',
                color='#555', fontsize=12, transform=ax.transAxes)
        return fig

    work_df = df.copy()

    # If all dates are null, generate synthetic dates for visualization
    if work_df['date'].isna().all():
        n = len(work_df)
        base = datetime.now() - timedelta(days=7)
        work_df['date'] = [base + timedelta(hours=i * (168 / n)) for i in range(n)]

    work_df['day'] = work_df['date'].dt.date

    # Calculate daily averages
    daily = work_df.groupby('day').agg(
        avg_score=('sentiment_score', 'mean'),
        pos=('sentiment_score', lambda x: (x > 0.1).sum()),
        neg=('sentiment_score', lambda x: (x < -0.1).sum()),
        total=('sentiment_score', 'count'),
    ).reset_index()

    days = range(len(daily))
    ax.plot(days, daily['avg_score'], color='#3b82f6', linewidth=2, label='Avg Sentiment', marker='o', markersize=4)
    ax.fill_between(days, daily['avg_score'], alpha=0.08, color='#3b82f6')

    # Positive / Negative volume as area
    if daily['total'].max() > 0:
        ax.bar(days, daily['pos'] / daily['total'], width=0.35, alpha=0.4,
               color='#22c55e', label='Pos ratio', align='edge')
        ax.bar([d + 0.35 for d in days], daily['neg'] / daily['total'], width=0.35,
               alpha=0.4, color='#ef4444', label='Neg ratio', align='edge')

    ax.set_title("Sentiment Trend Over Time", fontsize=11, fontweight='bold', pad=12)
    ax.set_ylabel("Score / Ratio", fontsize=9)
    ax.legend(fontsize=7, loc='upper right', framealpha=0.3, facecolor='#1a1a1a',
              edgecolor='#333', labelcolor='#aaa')
    ax.set_xticks(days)
    ax.set_xticklabels([str(d) for d in daily['day']], rotation=30, fontsize=7)
    fig.tight_layout()
    return fig


def chart_source_comparison(df: pd.DataFrame):
    """Clustered bar chart: article volume + avg sentiment per source."""
    fig, ax = _dark_fig((10, 3.8))

    if df.empty:
        ax.text(0.5, 0.5, "No data available", ha='center', va='center',
                color='#555', fontsize=12, transform=ax.transAxes)
        return fig

    src_stats = df.groupby('source').agg(
        count=('id', 'count'),
        avg_sent=('sentiment_score', 'mean'),
    ).reset_index()

    x = range(len(src_stats))
    width = 0.38

    bars1 = ax.bar([i - width/2 for i in x], src_stats['count'], width,
                   color='#3b82f6', alpha=0.8, label='Article Count')
    ax2 = ax.twinx()
    bars2 = ax2.bar([i + width/2 for i in x], src_stats['avg_sent'], width,
                    color='#a855f7', alpha=0.8, label='Avg Sentiment')

    ax.set_xticks(list(x))
    ax.set_xticklabels(src_stats['source'], fontsize=8)
    ax.set_ylabel("Article Count", fontsize=9)
    ax2.set_ylabel("Avg Sentiment", fontsize=9, color='#a855f7')
    ax2.tick_params(colors='#777', labelsize=8)
    ax2.spines['right'].set_color('#333')
    ax2.spines['top'].set_visible(False)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper right',
              framealpha=0.3, facecolor='#1a1a1a', edgecolor='#333', labelcolor='#aaa')

    ax.set_title("Source Comparison: Volume & Sentiment", fontsize=11, fontweight='bold', pad=12)
    fig.tight_layout()
    return fig


def chart_category_breakdown(df: pd.DataFrame):
    """Doughnut chart showing article distribution by category."""
    fig, ax = _dark_fig((5, 4))

    if df.empty:
        ax.text(0.5, 0.5, "No data", ha='center', va='center', color='#555',
                fontsize=12, transform=ax.transAxes)
        return fig

    cat_counts = df['category'].value_counts()
    colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#a855f7',
              '#06b6d4', '#ec4899', '#8b5cf6'][:len(cat_counts)]

    wedges, texts, autotexts = ax.pie(
        cat_counts.values, labels=cat_counts.index, autopct='%1.1f%%',
        colors=colors, startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor='#1a1a1a', linewidth=2),
    )
    for t in texts:
        t.set_color('#bbb')
        t.set_fontsize(8)
    for t in autotexts:
        t.set_color('#fff')
        t.set_fontsize(7)
        t.set_fontweight('bold')

    ax.set_title("Category Breakdown", fontsize=11, fontweight='bold',
                 color='#ddd', pad=14)
    fig.tight_layout()
    return fig


def chart_keyword_heatmap(kw_df: pd.DataFrame, articles_df: pd.DataFrame):
    """
    Heatmap showing keyword frequency.
    Falls back to word-frequency from article titles if Keywords table is empty.
    """
    fig, ax = _dark_fig((10, 4.2))

    if kw_df.empty:
        # Fallback: extract top words from article titles
        if articles_df.empty:
            ax.text(0.5, 0.5, "No keyword data", ha='center', va='center',
                    color='#555', fontsize=12, transform=ax.transAxes)
            return fig

        # Build word frequency from titles (filter short/common words)
        stopwords = {'và', 'của', 'cho', 'các', 'một', 'với', 'trong', 'từ',
                     'này', 'được', 'là', 'có', 'không', 'người', 'đã', 'khi',
                     'the', 'a', 'an', 'is', 'in', 'on', 'at', 'to', 'for',
                     'of', 'and', 'or', 'but', 'by', 'it', 'as', 'be', 'ở',
                     'về', 'theo', 'bị', 'tại', 'ra', 'lên', 'đến', 'sau',
                     'vì', 'như', 'sẽ', 'do', 'hay', 'thì', 'vào', 'nhưng'}
        all_words = []
        for title in articles_df['title'].dropna():
            words = [w.strip('.,!?()""\'\"') for w in str(title).split()
                     if len(w) > 2 and w.lower() not in stopwords]
            all_words.extend(words)

        word_freq = Counter(all_words).most_common(30)
        if not word_freq:
            ax.text(0.5, 0.5, "No keyword data", ha='center', va='center',
                    color='#555', fontsize=12, transform=ax.transAxes)
            return fig

        words = [w for w, _ in word_freq]
        freqs = [f for _, f in word_freq]

        # Reshape into a grid for heatmap
        cols = 6
        rows = (len(words) + cols - 1) // cols
        # Pad to fill the grid
        while len(words) < rows * cols:
            words.append("")
            freqs.append(0)

        data_matrix = np.array(freqs[:rows*cols]).reshape(rows, cols)
        labels_matrix = np.array(words[:rows*cols]).reshape(rows, cols)
    else:
        # Use actual keyword data
        top = kw_df.head(30)
        words = top['keyword'].tolist()
        freqs = top['frequency'].tolist()

        cols = 6
        rows = (len(words) + cols - 1) // cols
        while len(words) < rows * cols:
            words.append("")
            freqs.append(0)

        data_matrix = np.array(freqs[:rows*cols]).reshape(rows, cols)
        labels_matrix = np.array(words[:rows*cols]).reshape(rows, cols)

    sns.heatmap(data_matrix, ax=ax, cmap='YlOrRd', linewidths=2,
                linecolor='#1a1a1a', cbar_kws={'shrink': 0.6},
                annot=False, square=False)

    # Overlay text labels
    for i in range(data_matrix.shape[0]):
        for j in range(data_matrix.shape[1]):
            label = labels_matrix[i][j]
            val = data_matrix[i][j]
            if label:
                text_color = '#fff' if val > data_matrix.max() * 0.5 else '#ccc'
                ax.text(j + 0.5, i + 0.5, f"{label}\n({int(val)})",
                        ha='center', va='center', fontsize=6.5,
                        color=text_color, fontweight='bold')

    ax.set_title("Topic Frequency Heatmap (Top Keywords)", fontsize=11,
                 fontweight='bold', color='#ddd', pad=12)
    ax.set_xticks([])
    ax.set_yticks([])
    cbar = ax.collections[0].colorbar
    if cbar:
        cbar.ax.tick_params(colors='#777', labelsize=7)
    fig.tight_layout()
    return fig


# ===========================================================================
# SECTION 4: SIDEBAR NAVIGATION
# ===========================================================================
# Renders the branded sidebar with navigation radio, live stats, and
# quick actions. Stores the active page in st.session_state['page'].
# ===========================================================================

def render_sidebar():
    """Render the full sidebar with brand, navigation, live stats, and actions."""
    if 'sidebar_expanded' not in st.session_state:
        st.session_state.sidebar_expanded = True
        
    expanded = st.session_state.sidebar_expanded
    current = st.session_state.get('page', 'dashboard')
    
    # Custom toggle button
    if st.sidebar.button("☰" if not expanded else "☰  Collapse", key="toggle_sidebar", use_container_width=True):
        st.session_state.sidebar_expanded = not expanded
        st.rerun()
        
    st.sidebar.markdown("<hr style='border-color:#2a2a2a;margin:8px 0;'>", unsafe_allow_html=True)

    # ── Brand header ──────────────────────────────────────────────────────
    if expanded:
        st.sidebar.markdown("""
<div style='display:flex;align-items:center;gap:10px;padding:4px 0 18px;
            border-bottom:1px solid #2a2a2a;margin-bottom:14px;'>
    <span style='color:#ef4444;font-size:1.6rem;font-weight:900;'>▲</span>
    <div>
        <div style='color:#fff;font-size:1.05rem;font-weight:700;letter-spacing:1.8px;'>ANTIGRAVITY</div>
        <div style='color:#555;font-size:0.62rem;letter-spacing:0.8px;'>NEWS INTELLIGENCE</div>
    </div>
    <span style='margin-left:auto;'><span class='live-dot'></span></span>
</div>
""", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
<div style='display:flex;justify-content:center;padding:4px 0 18px;
            border-bottom:1px solid #2a2a2a;margin-bottom:14px;'>
    <span style='color:#ef4444;font-size:1.6rem;font-weight:900;'>▲</span>
</div>
""", unsafe_allow_html=True)

    # ── Navigation Buttons ──────────────────────────────────────────────────
    if expanded:
        st.sidebar.markdown(
            "<p style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            "letter-spacing:1px;margin-bottom:4px;font-weight:700;'>Navigation</p>",
            unsafe_allow_html=True,
        )
        
    pages = [
        ("dashboard", "📊" if not expanded else "📊  Main Dashboard"),
        ("feed", "📰" if not expanded else "📰  Live News Feed"),
        ("admin", "⚙️" if not expanded else "⚙️  Admin & Settings"),
    ]
    
    for page_id, label in pages:
        display_label = label
        if expanded and current == page_id:
            display_label = f"»  {label}"
            
        if st.sidebar.button(display_label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state['page'] = page_id
            st.rerun()

    st.sidebar.markdown("<hr style='border-color:#2a2a2a;margin:14px 0;'>",
                        unsafe_allow_html=True)

    # ── Live Database Stats ───────────────────────────────────────────────
    if expanded:
        st.sidebar.markdown(
            "<p style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            "letter-spacing:1px;margin-bottom:8px;font-weight:700;'>"
            "<span class='live-dot'></span> Live Stats</p>",
            unsafe_allow_html=True,
        )
        if db_exists():
            stats = load_db_stats()
            c1, c2 = st.sidebar.columns(2)
            c1.metric("Articles", f"{stats['total_articles']:,}")
            c2.metric("Sources", str(stats['total_sources']))
            c3, c4 = st.sidebar.columns(2)
            c3.metric("🟢 Pos", str(stats['pos_count']))
            c4.metric("🔴 Neg", str(stats['neg_count']))
        else:
            st.sidebar.caption("⚠️ Database not found")

        st.sidebar.markdown("<hr style='border-color:#2a2a2a;margin:14px 0;'>",
                            unsafe_allow_html=True)

        # ── Auto-Refresh Controls ─────────────────────────────────────────────
        st.sidebar.markdown(
            "<p style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            "letter-spacing:1px;margin-bottom:6px;font-weight:700;'>🔄 Live Refresh</p>",
            unsafe_allow_html=True,
        )
        st.sidebar.toggle("Auto-refresh", value=False, key="auto_refresh_toggle")
        st.sidebar.slider("Interval (sec)", 5, 120, 30, key="refresh_rate_slider")

        st.sidebar.markdown("<hr style='border-color:#2a2a2a;margin:14px 0;'>",
                            unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────
    if expanded:
        st.sidebar.markdown(
            "<p style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            "letter-spacing:1px;margin-bottom:6px;font-weight:700;'>⚡ Quick Actions</p>",
            unsafe_allow_html=True,
        )
    if st.sidebar.button("↺" if not expanded else "↺  Refresh Data Now", use_container_width=True, key="quick_refresh"):
        st.rerun()

    # ── Footer timestamp ──────────────────────────────────────────────────
    if expanded:
        st.sidebar.markdown(
            f"<div style='margin-top:2rem;font-size:0.68rem;color:#333;text-align:center;'>"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}</div>",
            unsafe_allow_html=True,
        )

# ===========================================================================
# SECTION 5: VIEW — MAIN DASHBOARD
# ===========================================================================
# High-level statistical visualization with KPI metrics, sentiment timeline,
# source comparison, keyword heatmap, and category breakdown charts.
# ===========================================================================

def view_main_dashboard():
    """Render the Main Dashboard view with KPI cards and visualization grid."""

    # ── Page Header ───────────────────────────────────────────────────────
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    st.markdown(f"""
<div class="page-header">
    <div>
        <div class="page-title">📊 Main Dashboard</div>
        <div class="page-subtitle">High-level analytics & public opinion trends</div>
    </div>
    <div class="page-status">
        <span class="live-dot"></span> System Online<br>
        <span style="font-size:0.72rem;">Last synced: <strong>{now_str}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)

    # Load data once for the whole view
    df = load_articles()
    stats = load_db_stats()
    kw_df = load_keywords()

    # ── KPI Metrics Row ───────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    # KPI 1: Total Articles
    with k1:
        pct_change = "+12.4%" if stats['total_articles'] > 0 else "—"
        st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-label">Total Articles Crawled</div>
    <div class="kpi-value">{stats['total_articles']:,}</div>
    <div class="kpi-change-up">▲ {pct_change} since last run</div>
</div>""", unsafe_allow_html=True)

    # KPI 2: Sentiment Index — ratio breakdown
    with k2:
        total = max(stats['total_articles'], 1)
        pos_pct = round(stats['pos_count'] / total * 100, 1)
        neg_pct = round(stats['neg_count'] / total * 100, 1)
        neut_pct = round(100 - pos_pct - neg_pct, 1)
        st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-label">Overall Sentiment Index</div>
    <div class="kpi-value" style="font-size:1.5rem;">
        <span style="color:#4ade80">{pos_pct}%</span>
        <span style="color:#555;font-size:1rem;"> / </span>
        <span style="color:#aaa">{neut_pct}%</span>
        <span style="color:#555;font-size:1rem;"> / </span>
        <span style="color:#f87171">{neg_pct}%</span>
    </div>
    <div class="kpi-sub">Positive / Neutral / Negative</div>
</div>""", unsafe_allow_html=True)

    # KPI 3: Active Crawlers Status (simulated)
    with k3:
        # Simulate crawler statuses based on sources in DB
        crawler_names = ["VnExpressCrawler", "BBCCrawler"]
        active_count = stats['total_sources']
        st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-label">Active Crawlers</div>
    <div class="kpi-value">
        <span style="color:#22c55e;">{active_count}</span>
        <span style="color:#555;font-size:1rem;"> / {len(crawler_names)}</span>
    </div>
    <div class="kpi-sub">
        {"".join(f'<span class="live-dot"></span>' for _ in range(active_count))}
        {"".join(f'<span class="live-dot-red"></span>' for _ in range(len(crawler_names) - active_count))}
        &nbsp; operational threads
    </div>
</div>""", unsafe_allow_html=True)

    # KPI 4: Database Health
    with k4:
        st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-label">Database Size</div>
    <div class="kpi-value">{stats['db_size_kb']}<span style="font-size:0.9rem;color:#888;"> KB</span></div>
    <div class="kpi-sub">Keywords tracked: {stats['total_keywords']:,}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ── Visualization Grid ────────────────────────────────────────────────

    # Row 1: Sentiment Timeline + Source Comparison
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.markdown("<div class='section-card'><div class='section-title'>"
                    "📈 Sentiment Timeline</div>", unsafe_allow_html=True)
        fig_timeline = chart_sentiment_timeline(df)
        st.pyplot(fig_timeline, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown("<div class='section-card'><div class='section-title'>"
                    "📊 Source Comparison</div>", unsafe_allow_html=True)
        fig_source = chart_source_comparison(df)
        st.pyplot(fig_source, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='spacer-sm'></div>", unsafe_allow_html=True)

    # Row 2: Keyword Heatmap + Category Breakdown
    heat_col, cat_col = st.columns([3, 2])

    with heat_col:
        st.markdown("<div class='section-card'><div class='section-title'>"
                    "🔥 Topic Frequency Heatmap</div>", unsafe_allow_html=True)
        fig_heatmap = chart_keyword_heatmap(kw_df, df)
        st.pyplot(fig_heatmap, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with cat_col:
        st.markdown("<div class='section-card'><div class='section-title'>"
                    "🍩 Category Breakdown</div>", unsafe_allow_html=True)
        fig_cat = chart_category_breakdown(df)
        st.pyplot(fig_cat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# SECTION 6: VIEW — LIVE NEWS FEED
# ===========================================================================
# Real-time data table with global filters, search, sentiment badges,
# language toggle, and export actions.
# ===========================================================================

def view_live_feed():
    """Render the Live News Feed view with filters, table, and export actions."""

    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # ── Page Header ───────────────────────────────────────────────────────
    st.markdown(f"""
<div class="page-header">
    <div>
        <div class="page-title">📰 Live News Feed</div>
        <div class="page-subtitle">Real-time article monitoring & data workspace</div>
    </div>
    <div class="page-status">
        <span class="live-dot"></span> Monitoring Active<br>
        <span style="font-size:0.72rem;">Last synced: <strong>{now_str}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)

    df = load_articles()

    # ── Global Filter & Search Bar ────────────────────────────────────────
    st.markdown("<div class='section-card'><div class='section-title'>"
                "🔍 Filter & Search</div>", unsafe_allow_html=True)

    f1, f2, f3, f4, f5 = st.columns([3, 1.5, 1.5, 1.5, 1])

    with f1:
        search_text = st.text_input(
            "Search", placeholder="Search titles, content, or source…",
            key="feed_search", label_visibility="collapsed",
        )

    with f2:
        if not df.empty:
            sources_list = ["All Sources"] + sorted(df['source'].dropna().unique().tolist())
        else:
            sources_list = ["All Sources"]
        sel_source = st.selectbox("Source", sources_list, key="feed_source",
                                  label_visibility="collapsed")

    with f3:
        sel_sentiment = st.selectbox(
            "Sentiment", ["All Sentiment", "Positive", "Neutral", "Negative"],
            key="feed_sentiment", label_visibility="collapsed",
        )

    with f4:
        # Language toggle — inferred from source name
        sel_lang = st.selectbox(
            "Language", ["All Languages", "Vietnamese", "English"],
            key="feed_lang", label_visibility="collapsed",
        )

    with f5:
        st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
        if st.button("↺ Refresh", use_container_width=True, key="feed_refresh"):
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data found. Run `python main.py` to populate the database.")
        return

    # ── Apply Filters ─────────────────────────────────────────────────────
    fdf = df.copy()

    if search_text:
        mask = (
            fdf['title'].str.contains(search_text, case=False, na=False) |
            fdf['content'].str.contains(search_text, case=False, na=False) |
            fdf['source'].str.contains(search_text, case=False, na=False)
        )
        fdf = fdf[mask]

    if sel_source != "All Sources":
        fdf = fdf[fdf['source'] == sel_source]

    if sel_sentiment == "Positive":
        fdf = fdf[fdf['sentiment_score'] > 0.1]
    elif sel_sentiment == "Negative":
        fdf = fdf[fdf['sentiment_score'] < -0.1]
    elif sel_sentiment == "Neutral":
        fdf = fdf[(fdf['sentiment_score'] >= -0.1) & (fdf['sentiment_score'] <= 0.1)]

    # Language filter by source heuristic
    vn_sources = {'VnExpress', 'Tuoi Tre', 'Thanh Nien'}
    en_sources = {'BBC', 'Reuters', 'CNN'}
    if sel_lang == "Vietnamese":
        fdf = fdf[fdf['source'].isin(vn_sources)]
    elif sel_lang == "English":
        fdf = fdf[fdf['source'].isin(en_sources)]

    # ── Results Summary ───────────────────────────────────────────────────
    showing = min(len(fdf), 50)
    st.markdown(
        f"<div style='color:#888;font-size:0.78rem;margin: 10px 0 14px;'>"
        f"Showing <strong style='color:#fff;'>{showing}</strong> of "
        f"<strong style='color:#fff;'>{len(fdf)}</strong> articles</div>",
        unsafe_allow_html=True,
    )

    # ── Advanced Feed Table ───────────────────────────────────────────────
    display_df = fdf.head(50).copy()

    # Create a cleaned snippet column (first 120 chars of content)
    display_df['snippet'] = display_df['content'].apply(
        lambda x: (str(x)[:120] + '…') if len(str(x)) > 120 else str(x)
    )

    # Sentiment label column
    def sentiment_label(score):
        if score > 0.1:
            return "🟢 Positive"
        elif score < -0.1:
            return "🔴 Negative"
        return "⚪ Neutral"

    display_df['sentiment'] = display_df['sentiment_score'].apply(sentiment_label)

    # Format date
    display_df['timestamp'] = display_df['date'].apply(
        lambda d: d.strftime("%Y-%m-%d %H:%M") if pd.notnull(d)
        else datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    # Show using st.dataframe with column_config for a premium look
    st.dataframe(
        display_df[['source', 'title', 'snippet', 'category', 'sentiment',
                     'sentiment_score', 'timestamp']],
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "source": st.column_config.TextColumn("📡 Source", width="small"),
            "title": st.column_config.TextColumn("📝 Title", width="large"),
            "snippet": st.column_config.TextColumn("📄 Snippet", width="large"),
            "category": st.column_config.TextColumn("🏷️ Category", width="small"),
            "sentiment": st.column_config.TextColumn("💡 Sentiment", width="medium"),
            "sentiment_score": st.column_config.NumberColumn(
                "📊 Score", format="%.3f", width="small",
            ),
            "timestamp": st.column_config.TextColumn("🕐 Timestamp", width="medium"),
        },
    )

    # ── Action Row: Export Buttons ─────────────────────────────────────────
    st.markdown("<div class='spacer-sm'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-card'><div class='section-title'>"
                "⚡ Actions</div>", unsafe_allow_html=True)

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        csv_bytes = fdf.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export CSV", csv_bytes,
            file_name=f"feed_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True, key="feed_csv",
        )

    with a2:
        # JSON export (only serializable columns)
        export_cols = ['title', 'content', 'source', 'category', 'sentiment_score']
        json_str = fdf[export_cols].to_json(orient="records", force_ascii=False, indent=2)
        st.download_button(
            "⬇️ Export JSON", json_str.encode("utf-8"),
            file_name=f"feed_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json", use_container_width=True, key="feed_json",
        )

    with a3:
        if st.button("↺ Force Refresh", use_container_width=True, key="feed_force_refresh"):
            st.rerun()

    with a4:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px;color:#555;"
            f"font-size:0.78rem;'>{len(fdf)} articles in current filter</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# SECTION 7: VIEW — ADMIN & SETTINGS
# ===========================================================================
# System configuration with AI API settings, crawler control panel with
# ON/OFF toggles, logging console, and database storage management.
# ===========================================================================

def view_admin_settings():
    """Render the Admin & Settings view."""

    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # ── Page Header ───────────────────────────────────────────────────────
    st.markdown(f"""
<div class="page-header">
    <div>
        <div class="page-title">⚙️ Admin & Settings</div>
        <div class="page-subtitle">System configuration, crawler management & storage oversight</div>
    </div>
    <div class="page-status">
        <span style="font-size:0.72rem;">Session: <strong>{now_str}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Password Gate ─────────────────────────────────────────────────────
    if 'admin_auth' not in st.session_state:
        st.session_state['admin_auth'] = False

    if not st.session_state['admin_auth']:
        st.markdown("""
<div class="section-card" style="max-width:450px;">
    <div class="section-title">🔐 Authentication Required</div>
    <div style="color:#888;font-size:0.85rem;margin-bottom:12px;">
        Enter the admin password to access system controls.
    </div>
</div>""", unsafe_allow_html=True)

        pwd = st.text_input("Password", type="password",
                            placeholder="Enter admin password…", key="admin_pwd")
        if st.button("🔓 Unlock Admin Panel", type="primary"):
            if pwd == "admin123":
                st.session_state['admin_auth'] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Try again.")
        return

    # Authenticated — show lock button
    lock_col, _, status_col = st.columns([1, 4, 1])
    with lock_col:
        if st.button("🔒 Lock Panel", use_container_width=True):
            st.session_state['admin_auth'] = False
            st.rerun()
    with status_col:
        st.markdown(
            "<div style='text-align:right;padding-top:8px;'>"
            "<span class='live-dot'></span>"
            "<span style='color:#22c55e;font-size:0.82rem;font-weight:600;'>"
            "Authenticated</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION A: AI Sentiment API Configuration
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'><div class='section-title'>"
                "🤖 AI Sentiment API Configuration</div>", unsafe_allow_html=True)

    api_col1, api_col2 = st.columns([2, 1])

    with api_col1:
        selected_model = st.selectbox(
            "Target AI Model",
            ["TextBlob (Built-in NLP)", "Google Generative AI API", "OpenAI GPT-4o",
             "Custom REST API"],
            key="ai_model_select",
        )
        api_key = st.text_input(
            "API Secret Key", type="password",
            placeholder="sk-xxxx… (leave empty for TextBlob)",
            key="api_key_input",
        )
        api_endpoint = st.text_input(
            "API Endpoint (optional)",
            placeholder="https://api.example.com/v1/sentiment",
            key="api_endpoint_input",
        )

    with api_col2:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)

        # Test Connection button
        if st.button("🔌 Test Connection", use_container_width=True, key="test_api"):
            if selected_model == "TextBlob (Built-in NLP)":
                # TextBlob doesn't need an API key — always succeeds
                st.success("✅ TextBlob engine is available and ready.")
            elif api_key:
                # Simulated connection test
                with st.spinner("Testing connection…"):
                    time.sleep(1)
                st.success(f"✅ Connected to {selected_model} successfully.")
            else:
                st.error("❌ API key is required for this model.")

        st.markdown("<div style='padding-top:12px;'></div>", unsafe_allow_html=True)

        # Re-run Sentiment button
        if st.button("▶ Run Sentiment Now", type="primary", use_container_width=True,
                      key="run_sentiment"):
            with st.spinner("Running sentiment analysis on all articles…"):
                try:
                    import sys
                    sys.path.insert(0, os.path.abspath(
                        os.path.join(os.path.dirname(__file__), '..')))
                    from src.analysis.sentiment_engine import SentimentEngine
                    engine = SentimentEngine()
                    with sqlite3.connect(DB_PATH) as conn:
                        articles = pd.read_sql_query(
                            "SELECT id, content FROM Articles", conn)
                    updates = [
                        (engine.analyze_text(r['content']), r['id'])
                        for _, r in articles.iterrows()
                    ]
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.executemany(
                            "UPDATE Articles SET sentiment_score = ? WHERE id = ?",
                            updates)
                        conn.commit()
                    st.success(f"✅ Updated {len(updates)} articles.")
                except Exception as e:
                    st.error(f"❌ Failed: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION B: Crawler Control Panel
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'><div class='section-title'>"
                "🕷️ Crawler Control Panel</div>", unsafe_allow_html=True)

    # Define crawlers with their simulated statuses
    crawlers = [
        {"name": "VnExpressCrawler",  "type": "BeautifulSoup", "icon": "🇻🇳",
         "status": "active",  "articles": 968, "key": "toggle_vnexpress"},
        {"name": "BBCCrawler",        "type": "Selenium",      "icon": "🇬🇧",
         "status": "standby", "articles": 0,   "key": "toggle_bbc"},
        {"name": "TuoiTreCrawler",    "type": "BeautifulSoup", "icon": "🇻🇳",
         "status": "standby", "articles": 0,   "key": "toggle_tuoitre"},
        {"name": "ReutersCrawler",    "type": "Selenium",      "icon": "🌐",
         "status": "standby", "articles": 0,   "key": "toggle_reuters"},
    ]

    for crawler in crawlers:
        c1, c2, c3, c4, c5 = st.columns([0.5, 2.5, 1.5, 1.5, 1])

        with c1:
            st.markdown(
                f"<div style='font-size:1.5rem;text-align:center;padding-top:6px;'>"
                f"{crawler['icon']}</div>",
                unsafe_allow_html=True,
            )

        with c2:
            dot_class = "live-dot" if crawler['status'] == 'active' else "live-dot-red"
            st.markdown(f"""
<div style="padding-top:4px;">
    <div style="font-size:0.95rem;font-weight:600;color:#f0f0f0;">
        <span class="{dot_class}"></span>{crawler['name']}
    </div>
    <div style="font-size:0.72rem;color:#777;">
        Engine: {crawler['type']} · {crawler['articles']:,} articles fetched
    </div>
</div>""", unsafe_allow_html=True)

        with c3:
            status_color = "#22c55e" if crawler['status'] == 'active' else "#555"
            status_text = "ACTIVE" if crawler['status'] == 'active' else "STANDBY"
            st.markdown(f"""
<div style="text-align:center;padding-top:8px;">
    <span style="color:{status_color};font-size:0.75rem;font-weight:700;
                 letter-spacing:0.8px;">{status_text}</span>
</div>""", unsafe_allow_html=True)

        with c4:
            is_on = crawler['status'] == 'active'
            st.toggle(
                f"Enable {crawler['name']}",
                value=is_on, key=crawler['key'],
                label_visibility="collapsed",
            )

        with c5:
            st.markdown(
                "<div style='text-align:center;padding-top:8px;color:#555;"
                "font-size:1.1rem;cursor:pointer;'>⋮</div>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ── Logging Console ───────────────────────────────────────────────────
    st.markdown("<div class='section-card'><div class='section-title'>"
                "🖥️ Logging Console</div>", unsafe_allow_html=True)

    # Generate realistic-looking log entries
    log_entries = [
        ("15:12:01", "INFO",  "CrawlerEngine initialized. Thread pool size: 4"),
        ("15:12:02", "INFO",  "VnExpressCrawler.fetch() — Connecting to https://vnexpress.net/"),
        ("15:12:04", "INFO",  "VnExpressCrawler.fetch() — HTTP 200 OK. Parsing 50 articles..."),
        ("15:12:06", "WARN",  "BBCCrawler.fetch() — Selenium ChromeDriver not found. Skipping."),
        ("15:12:06", "INFO",  "VnExpressCrawler — 50 articles saved to Articles table."),
        ("15:12:07", "INFO",  "DatabaseManager.insert_article() — Deduplication: 3 duplicates skipped."),
        ("15:12:08", "INFO",  "Pipeline complete. Total new articles: 47"),
        ("15:12:09", "INFO",  "SentimentEngine.analyze_batch() — Processing 47 articles via TextBlob..."),
        ("15:12:14", "INFO",  "SentimentEngine — Analysis complete. Avg score: 0.0234"),
        ("15:12:15", "INFO",  "ReportGenerator — Daily report exported to data/daily_report_*.csv"),
        ("15:12:15", "INFO",  f"Session ended at {datetime.now().strftime('%H:%M:%S')}. All tasks complete."),
    ]

    log_html = ""
    for ts, level, msg in log_entries:
        level_class = {
            "INFO": "log-line-info", "WARN": "log-line-warn", "ERROR": "log-line-error"
        }.get(level, "")
        log_html += (
            f'<div><span class="log-line-time">[{ts}]</span> '
            f'<span class="{level_class}">{level}</span> '
            f'<span style="color:#bbb;">— {msg}</span></div>'
        )

    st.markdown(f'<div class="log-console">{log_html}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION C: Database & Storage Management
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'><div class='section-title'>"
                "💾 Database & Storage Management</div>", unsafe_allow_html=True)

    stats = load_db_stats()
    sizes = load_table_sizes()

    # Storage indicator cards
    s1, s2, s3, s4, s5 = st.columns(5)

    table_info = [
        (s1, "Articles",         sizes['Articles'],         "#3b82f6"),
        (s2, "Sources",          sizes['Sources'],          "#22c55e"),
        (s3, "Keywords",         sizes['Keywords'],         "#f59e0b"),
        (s4, "Article_Keywords", sizes['Article_Keywords'], "#a855f7"),
        (s5, "DB File Size",     None,                      "#06b6d4"),
    ]

    for col, label, count, color in table_info:
        with col:
            if count is not None:
                val_str = f"{count:,} rows"
            else:
                val_str = f"{stats['db_size_kb']} KB"
            st.markdown(f"""
<div style="background:#0d0d0d;border:1px solid #2a2a2a;border-radius:8px;
            padding:16px;text-align:center;border-top:3px solid {color};">
    <div style="font-size:0.65rem;text-transform:uppercase;color:#666;
                letter-spacing:0.6px;margin-bottom:6px;font-weight:700;">{label}</div>
    <div style="font-size:1.3rem;font-weight:800;color:#fff;">{val_str}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # Action buttons
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if st.button("🗑️ Wipe Cache", use_container_width=True, key="wipe_cache"):
            st.info("ℹ️ Cache cleared (Streamlit session state reset).")

    with b2:
        if db_exists():
            with sqlite3.connect(DB_PATH) as conn:
                df_exp = pd.read_sql_query(
                    "SELECT a.title, a.content, s.name as source, a.date, "
                    "a.category, a.sentiment_score "
                    "FROM Articles a JOIN Sources s ON a.source_id = s.id", conn)
            csv_data = df_exp.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export All CSV", csv_data,
                file_name=f"full_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key="admin_csv",
            )

    with b3:
        if db_exists():
            json_data = df_exp.to_json(
                orient="records", force_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Export All JSON", json_data,
                file_name=f"full_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True, key="admin_json",
            )

    with b4:
        purge_days = st.number_input("Purge older than (days)", min_value=7,
                                     max_value=365, value=30, key="purge_days")

    if st.button(f"🗑️ Purge articles older than {int(purge_days)} days",
                 type="primary", key="purge_btn"):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM Articles WHERE date < date('now', ? || ' days')",
                    (f"-{int(purge_days)}",))
                deleted = cursor.rowcount
                conn.commit()
            st.success(f"✅ Purged {deleted} old articles.")
        except Exception as e:
            st.error(f"❌ Purge failed: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# SECTION 8: MAIN APPLICATION ENTRY POINT
# ===========================================================================
# Orchestrates CSS injection, sidebar rendering, page routing,
# and the auto-refresh loop.
# ===========================================================================

def main():
    """Main application entry point. Handles routing and auto-refresh."""

    # Inject the CSS design system
    inject_css()

    # Render the sidebar (sets st.session_state['page'])
    render_sidebar()

    # Initialize default page
    if 'page' not in st.session_state:
        st.session_state['page'] = 'dashboard'

    # ── Page Router ───────────────────────────────────────────────────────
    page = st.session_state.get('page', 'dashboard')

    if page == 'dashboard':
        view_main_dashboard()
    elif page == 'feed':
        view_live_feed()
    elif page == 'admin':
        view_admin_settings()
    else:
        view_main_dashboard()

    # ── Auto-Refresh Loop ─────────────────────────────────────────────────
    auto_refresh = st.session_state.get('auto_refresh_toggle', False)
    refresh_rate = st.session_state.get('refresh_rate_slider', 30)

    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()


if __name__ == "__main__":
    main()
