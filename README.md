# FLY
Finance Ledger Yearly (FLY) gathers financial documents from companies listed on a stock exchange. It scrapes company data and stores them in a local database.

## How It Works, Behind the Wheels
The FLY list below outlines the core steps in fetching company data and financial documents.

1. **CompanyData Information Scraping**  
   - Finds company names, tickers, sectors, and registration data.
   - Saves the latest updates to avoid redundant data.

2. **Financial Reports Processing**  
   - Extracts and standardizes company financial statements.
   - Ensures that data follows a structured, readable format.
   - Only updates reports if new information is available.

3. **NSD (Document Number) Tracking**  
   - Keeps track of financial disclosure documents.
   - Fills in missing document sequences intelligently.

4. **Stock Market & Corporate Events Analysis**  
   - Fetches stock prices, stock splits, and dividend information.
   - Matches stock performance with financial statements.

5. **Performance & Optimization**
   - Supports concurrent processing with a configurable number of workers for improved performance.
   - Tracks memory and execution time to keep things running smoothly.


## Technologies

- **Python 3.11**
- **SQLite** with **SQLAlchemy**
- Hexagonal Architecture (Ports and Adapters)

## Installation

1. Create a virtual environment and install the dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the CLI application:
   ```bash
   python run.py
   ```

The CLI invokes the application services to synchronize companies and NSD records. Logs are written to a `.log` in the project root.

## Services

- Example services can be triggered individually:

- `sync_companies` – Fetch company listings and details from the exchange.
- `sync_nsd` – Download sequential document information.
- `fetch_statements` – Retrieve raw statement pages. The rows are stored in
  `SqlAlchemyRepositoryStatementFetchedPort` before parsing. Fetched statements are persisted separately using `SqlAlchemyStatementRawRepository`.
- `parse_statements` – Convert stored pages into structured records.

Services are started from `presentation/cli.py` when you execute `run.py`.

## Project Layout

```
domain/         # DTOs and ports
application/    # services and use cases
infrastructure/ # scrapers, repositories, helpers
presentation/   # CLI entry point
```

Development and production runs use the same entry point. Adjust configuration files in `infrastructure/config` if you need to change paths or logging levels.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---
"Inspired by the Pampas and crafted with yerba mate in South America: an authentic gaucho product."
