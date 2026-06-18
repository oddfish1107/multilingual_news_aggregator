# Multilingual News Aggregator & Sentiment Analysis Dashboard (Phase 1)

This project is a Python-based web crawling and data storage engine for aggregating news from multiple sources, designed with modularity, concurrency, and object-oriented principles. Phase 1 focuses on fetching news (using `requests`, `BeautifulSoup`, and `Selenium`), processing it, and storing it into a normalized SQLite database.

## Features
- **Object-Oriented Architecture**: Modular crawler engine with an abstract base class.
- **Static & Dynamic Scraping**: Supports both static pages (e.g., VnExpress via BeautifulSoup) and dynamic, JavaScript-rendered pages (e.g., BBC via Selenium).
- **Concurrency**: Multi-threaded scraping for faster data extraction.
- **SQLite Database**: Normalized schema tracking Sources, Articles, and Keywords.
- **Data Export**: Built-in support to export scraped articles to JSON and CSV formats.
- **Advanced Python Concepts**: Extensive use of decorators for timing/logging, and lambda/map functions for batch text processing.

## Project Structure
```text
news_aggregator/
├── crawler_engine.py      # Abstract Base Crawler & Specific Implementations
├── database_manager.py    # SQLite initialization, inserts, and export functions
├── main.py                # Multi-threaded orchestrator script
├── utils.py               # Utility decorators and filtering functions
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
└── tests/
    ├── __init__.py
    └── test_crawlers.py   # Unit tests for crawlers and utility functions
```

## Setup & Installation

1. Clone the repository and navigate into the folder:
   ```bash
   git clone <your-repo-url>
   cd news_aggregator
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   *Note: For the BBC crawler, ensure you have Google Chrome installed, as well as the compatible `chromedriver` in your system PATH (Selenium Manager typically handles this automatically in newer versions of Selenium).*

## Usage

Run the main orchestrator script:
```bash
python main.py
```
This will:
1. Initialize the SQLite database `news_aggregator.db`.
2. Spawn multiple threads to crawl target URLs concurrently.
3. Save the results to the database.
4. Export the scraped data to `articles_export.json` and `articles_export.csv`.

## Running Tests

To run the unit tests provided in the `tests` directory:
```bash
python -m unittest discover -s tests
```
