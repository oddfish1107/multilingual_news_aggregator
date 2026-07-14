"""
test_dashboard.py
=================
Automated tests for dashboard.py (v2 — redesigned 3-view dashboard)

Run with:
    python -m pytest tests/test_dashboard.py -v

Tests cover 5 critical behaviours:
  1. Module imports without errors
  2. load_articles() always returns a DataFrame
  3. load_db_stats() returns correct structure
  4. Sidebar search / date-range / sentiment filter logic
  5. No duplicate Streamlit widget keys in the source file
"""

import ast
import os
import sys
import sqlite3
import types
from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Stub streamlit BEFORE importing dashboard so set_page_config does not crash
# ---------------------------------------------------------------------------
def _make_st_stub():
    st = types.ModuleType("streamlit")
    st.sidebar = MagicMock()
    st.session_state = {}
    st.column_config = MagicMock()
    st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    for name in [
        "markdown","write","title","header","subheader","caption","info",
        "success","warning","error","dataframe","metric","button",
        "download_button","text_input","selectbox","radio","slider","toggle",
        "date_input","rerun","set_page_config","stop","pyplot",
        "spinner","number_input","code",
    ]:
        setattr(st, name, MagicMock(return_value=None))
    return st

sys.modules.setdefault("streamlit", _make_st_stub())

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard")
sys.path.insert(0, DASHBOARD_DIR)
# Also need to add root directory so src can be found
sys.path.insert(0, os.path.join(DASHBOARD_DIR, ".."))
import dashboard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_db(tmp_path):
    db = tmp_path / "news_data_v2.db"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE Sources (id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL);
        CREATE TABLE Articles (
            id INTEGER PRIMARY KEY, title TEXT, url TEXT, content TEXT, content_hash TEXT,
            source_id INTEGER, alt_sources TEXT, date TEXT, category TEXT, sentiment_score REAL
        );
        CREATE TABLE Keywords (id INTEGER PRIMARY KEY, keyword TEXT UNIQUE NOT NULL);
        CREATE TABLE Article_Keywords (
            article_id INTEGER, keyword_id INTEGER,
            PRIMARY KEY (article_id, keyword_id)
        );
        INSERT INTO Sources VALUES (1,'BBC','https://bbc.co.uk'),(2,'VnExpress','https://vnexpress.net');
        INSERT INTO Articles (id, title, content, source_id, date, category, sentiment_score) VALUES
            (1,'AI Breakthrough','Content A',1,'2025-06-01 10:00:00','tech',0.5),
            (2,'Market Crash','Content B',2,'2025-06-02 11:00:00','finance',-0.6),
            (3,'Neutral News','Content C',1,'2025-06-03 09:00:00','world',0.0);
    """)
    conn.close()
    return str(db)


@pytest.fixture()
def sample_df():
    return pd.DataFrame({
        "id":              [1, 2, 3],
        "title":           ["AI Breakthrough", "Market Crash", "Neutral News"],
        "content":         ["A", "B", "C"],
        "source":          ["BBC", "VnExpress", "BBC"],
        "date":            pd.to_datetime(["2025-06-01","2025-06-02","2025-06-03"]),
        "category":        ["tech", "finance", "world"],
        "sentiment_score": [0.5, -0.6, 0.0],
    })


# ===========================================================================
# TEST 1 — Module imports cleanly
# ===========================================================================
class TestImport:
    def test_module_loads(self):
        assert dashboard is not None

    def test_required_functions_exist(self):
        """Verify the new dashboard API functions exist."""
        for fn in ("load_articles", "load_db_stats", "load_keywords",
                    "inject_css", "render_sidebar",
                    "view_main_dashboard", "view_live_feed", "view_admin_settings",
                    "main"):
            assert hasattr(dashboard, fn), f"Missing: {fn}"


# ===========================================================================
# TEST 2 — load_articles() always returns a DataFrame
# ===========================================================================
class TestLoadArticles:
    def test_missing_db_returns_empty_df(self):
        df = dashboard.load_articles(db_path="/nonexistent.db")
        assert isinstance(df, pd.DataFrame) and df.empty

    def test_valid_db_returns_rows(self, sample_db):
        df = dashboard.load_articles(db_path=sample_db)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "sentiment_score" in df.columns

    def test_date_column_is_datetime(self, sample_db):
        df = dashboard.load_articles(db_path=sample_db)
        assert pd.api.types.is_datetime64_any_dtype(df["date"])


# ===========================================================================
# TEST 3 — load_db_stats() returns correct structure
# ===========================================================================
class TestLoadDbStats:
    def test_missing_db_returns_defaults(self):
        stats = dashboard.load_db_stats(db_path="/nonexistent.db")
        assert isinstance(stats, dict)
        assert stats['total_articles'] == 0
        assert stats['pos_count'] == 0

    def test_valid_db_returns_correct_counts(self, sample_db):
        stats = dashboard.load_db_stats(db_path=sample_db)
        assert stats['total_articles'] == 3
        assert stats['total_sources'] == 2
        assert stats['pos_count'] == 1   # score > 0.1
        assert stats['neg_count'] == 1   # score < -0.1
        assert stats['neut_count'] == 1  # the remaining

    def test_avg_sentiment_is_float(self, sample_db):
        stats = dashboard.load_db_stats(db_path=sample_db)
        assert isinstance(stats['avg_sentiment'], float)


# ===========================================================================
# TEST 4 — Filter logic (same as before — tests the pandas operations)
# ===========================================================================
class TestFilterLogic:
    def test_search_by_title(self, sample_df):
        s = "ai"
        mask = (sample_df["title"].str.lower().str.contains(s,na=False) |
                sample_df["source"].str.lower().str.contains(s,na=False))
        assert len(sample_df[mask]) == 1

    def test_search_by_source(self, sample_df):
        s = "vnexpress"
        mask = (sample_df["title"].str.lower().str.contains(s,na=False) |
                sample_df["source"].str.lower().str.contains(s,na=False))
        assert sample_df[mask].iloc[0]["source"] == "VnExpress"

    def test_date_range(self, sample_df):
        result = sample_df[
            (sample_df["date"].dt.date >= date(2025,6,1)) &
            (sample_df["date"].dt.date <= date(2025,6,2))
        ]
        assert len(result) == 2

    def test_positive_sentiment(self, sample_df):
        assert len(sample_df[sample_df["sentiment_score"] > 0.1]) == 1

    def test_negative_sentiment(self, sample_df):
        assert len(sample_df[sample_df["sentiment_score"] < -0.1]) == 1

    def test_empty_search_returns_all(self, sample_df):
        s = ""
        result = sample_df if not s else sample_df[
            sample_df["title"].str.lower().str.contains(s,na=False)]
        assert len(result) == 3

    def test_sorting_mixed_types(self):
        mixed_series = pd.Series(["BBC", None, 123, "VnExpress", 45.6])
        clean_list = sorted([str(x) for x in mixed_series.dropna().unique()])
        assert clean_list == ["123", "45.6", "BBC", "VnExpress"]

    def test_language_filter_by_source(self, sample_df):
        """Test the language filter heuristic (filter by source name)."""
        vn_sources = {'VnExpress', 'Tuoi Tre'}
        en_sources = {'BBC', 'Reuters'}
        vn_df = sample_df[sample_df['source'].isin(vn_sources)]
        en_df = sample_df[sample_df['source'].isin(en_sources)]
        assert len(vn_df) == 1  # VnExpress
        assert len(en_df) == 2  # BBC x2


# ===========================================================================
# TEST 5 — No duplicate Streamlit widget keys
# ===========================================================================
class TestNoDuplicateKeys:
    def test_no_duplicate_widget_keys(self):
        src = os.path.join(DASHBOARD_DIR, "dashboard.py")
        with open(src, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        keys, seen, dupes = [], set(), set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "key" and isinstance(kw.value, ast.Constant):
                    k = kw.value.value
                    (dupes if k in seen else seen).add(k)
        assert not dupes, f"Duplicate widget keys: {dupes}"
