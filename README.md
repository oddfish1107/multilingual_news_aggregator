# Multilingual News Aggregator & Sentiment Analysis Dashboard
**Project Antigravity**

A complete end-to-end Python ecosystem that scrapes multilingual news sites, stores the data in a relational database, applies AI Sentiment NLP, and presents live trends in an interactive data science dashboard.

---

## 🛠️ System Architecture

1. **Phase 1: Web Crawling & Storage**
   - Object-Oriented crawler engine supporting `BeautifulSoup` (static sites) and `Selenium` (dynamic sites).
   - Thread-pool multi-processing for fast, concurrent fetching.
   - Normalized SQLite database architecture.
2. **Phase 2: AI Data Pipeline**
   - Advanced Pandas ETL pipeline.
   - `TextBlob` integrated as our NLP Sentiment Engine, featuring rate limit simulation and robust error handling.
   - Automated Matplotlib analytical chart generation and daily report exports (JSON/CSV).
3. **Phase 3: Interactive Dashboard & Trends**
   - Streamlit frontend providing interactive filters (source, sentiment, date).
   - Data fetching layer optimized with `@st.cache_data` for instant rendering.
   - TF-IDF Trend Detection module identifying surging anomalous topics dynamically.

---

## 🚀 System Requirements & Installation

**Prerequisites:**
- Python 3.9+
- Google Chrome & ChromeDriver (for Selenium functionality)

**Installation:**
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd news_aggregator
   ```
2. Set up a Python Virtual Environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📊 Live Demo Launch Guide

Follow these sequential steps to present the entire ecosystem during the final presentation:

**Step 1: Run the Web Scraper**
Execute the Phase 1 script to spin up the crawlers and populate the SQLite database.
```bash
python main.py
```

**Step 2: Run the AI Data Pipeline**
Execute the Phase 2 script to process the data, calculate sentiment polarity scores, and log static reports.
```bash
python main_phase2.py
```

**Step 3: Launch the Interactive Dashboard**
Run the Phase 3 Streamlit application to visualize the results live!
```bash
streamlit run dashboard.py
```
*The dashboard will automatically open in your default web browser.*

---

## 🧪 System Testing

The ecosystem is backed by a robust `pytest` suite ensuring text processing, parsing logic, and sentiment assignments work flawlessly without network dependencies.
To run the test suite:
```bash
pytest tests/test_system.py -v
```

---
*Built by an Expert Python Full-Stack Developer & Lead System Architect.*
