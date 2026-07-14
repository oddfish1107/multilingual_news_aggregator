# Project Status Report: Multilingual News Aggregator & Sentiment Analysis Dashboard

This report summarizes the entire development process, architecture, and completed deliverables for the "Multilingual News Aggregator" project. The system has been successfully implemented across two major phases, culminating in a fully automated data pipeline from web scraping to AI analysis and visualization.

## Architecture Overview

The system is built as a highly modular Python application, separated into logical components spanning data extraction, storage, user interface, and AI-driven analysis.

> [!TIP]
> **Modularity Strategy**
> Each component is encapsulated in its own file (e.g., `crawler_engine.py`, `sentiment_engine.py`), allowing for independent testing and easy future extensions without risking system-wide failures.

## Phase 1: Web Crawling & Storage

**Goal:** Automatically extract news data from various multilingual sources and safely store it in a structured format.

- **Object-Oriented Crawler Engine**: We implemented an abstract base class (`BaseCrawler`) to define the scraping interface. We created specialized subclasses:
  - `VnExpressCrawler`: Uses `BeautifulSoup` and `requests` for fast, static page scraping.
  - `BBCCrawler`: Uses `Selenium WebDriver` to render and scrape dynamic, JavaScript-heavy sites safely.
- **Multithreading**: `concurrent.futures.ThreadPoolExecutor` was utilized to launch multiple crawlers simultaneously, drastically reducing data collection time.
- **Relational Database**: Developed `database_manager.py` to establish a normalized SQLite schema featuring `Sources`, `Articles`, and `Keywords` tables interconnected by foreign keys. 
- **Functional Programming**: Extensive use of `lambda` functions and `map()` for streamlined text cleaning and batch processing.
- **Data Export**: Built-in support to dump the SQLite tables directly into JSON and CSV files for portability.

## Phase 1.5: Live User Interface

**Goal:** Provide a stunning, real-time dashboard for end-users to view incoming news.

- **Frontend Technology**: Built using pure HTML, CSS, and Vanilla Javascript.
- **Aesthetic**: Implemented a modern, brutalist aesthetic heavily inspired by user-provided references. It features giant `Syncopate` typography, smooth CSS micro-animations (slide-ups, pulsing indicators), and sleek glassmorphism UI elements over an urban photo background.
- **Real-Time Data Sync**: The JS engine implements a continuous polling loop that fetches the output JSON file every 3 seconds. When the Python backend completes a scrape, the website instantly detects the changes, automatically rendering and animating the new articles into view without a browser refresh.

## Phase 2: Analysis & AI Integration

**Goal:** Clean the scraped data, determine article sentiment using Artificial Intelligence, and generate insights.

- **Pandas Data Pipeline**: Built `data_pipeline.py` to connect directly to the SQLite database. It performs critical ETL tasks: dropping nulls, handling duplicates (`drop_duplicates`), and configuring datetime objects for time-series operations.
- **AI Sentiment Engine**: Developed `sentiment_engine.py` integrating the `TextBlob` NLP library. It parses article content and computes a continuous sentiment polarity score from -1.0 to 1.0. 
  > [!IMPORTANT]
  > **API Resilience**
  > To ensure the system handles external API constraints robustly, the sentiment engine includes custom tracking logic for rate limit checking and triggers exponential backoff/sleeping when limits are exceeded.
- **Automated Visualizations**: Created `visualizations.py` leveraging `Matplotlib` and `Seaborn`. The system automatically outputs three critical analytical charts:
  1. Average Daily Sentiment Timeline.
  2. Sentiment Distribution by News Source (Boxplot).
  3. Average Sentiment Topic Heatmap.
- **Daily Automated Reporting**: Built `report_generator.py` to aggregate summary statistics (e.g., total articles, average sentiment breakdown) and automatically export a daily JSON overview alongside a detailed CSV file.

## Execution Flow

The full pipeline is completely functional and is operated via two primary orchestrators:
1. `python main.py` triggers the crawler fleet, populates the SQLite database, and feeds the live frontend.
2. `python main_phase2.py` triggers the Pandas pipeline, runs the AI sentiment analysis over the newly scraped data, plots the data science charts into the `plots/` directory, and outputs the daily automated summaries.

> [!NOTE]
> The project successfully meets all technical requirements for a robust, concurrent web scraping engine and a complete AI-driven data science pipeline.
