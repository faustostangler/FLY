# ASW (AssetWise)

## Overview

The ASW Financial Data App is designed to automate the extraction and processing of financial data from various online sources. It retrieves detailed company information, financial documents, and standardized financial statements, storing this data in a local SQLite database for easy access and analysis.

## Features

- **Company Information Scraping**: Extracts details such as ticker symbols, trading information, governance levels, CNPJ, sector classification, website, and more from the B3 (Brasil, Bolsa, Balcão) website.
- **NSD (Document Number) Scraping**: Generates and scrapes NSD values to fetch detailed financial documents and metadata, including auditor information and document dates.
- **Financial Sheets Scraping**: Retrieves standardized financial statements and quarterly information, processes the data, and stores it in a structured format.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Required Python packages listed in `requirements.txt`
- Google Chrome browser installed

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-username/financial-data-scraping-app.git
   cd financial-data-scraping-app

2. **Install the required packages:**
    pip install -r requirements.txt

3. Set up the database:
    Ensure the SQLite database file b3.db is in the specified folder (backend/data).

### Configuration
Configure system-wide settings in settings.py:

batch_size: Batch size for data processing
db_name: Database name (default is b3.db)
db_folder: Folder where the database is stored
wait_time: Wait time for Selenium operations
companies_url: URL for the B3 companies search page
company_url: URL for the B3 company detail page

### Usage
1. Run the main script:
    python b3.py

This will start the process of scraping company information, NSD values, and financial sheets.

### Modules
b3.py: The main script that orchestrates the scraping and data processing tasks.
settings.py: Contains configuration settings for the app.
selenium_driver.py: Manages the setup and operation of the Selenium WebDriver.
nsd_scrap.py: Handles the generation and scraping of NSD values.
finsheet.py: Scrapes and processes standardized financial statements and quarterly information.
company_scrap.py: Extracts company details from the B3 website.
system.py: Provides utility functions for logging, web interactions, and database operations.

## Contributing
Fork the repository
Create a new branch (git checkout -b feature-branch)
Commit your changes (git commit -am 'Add new feature')
Push to the branch (git push origin feature-branch)
Create a new Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements
Selenium for web automation
BeautifulSoup for parsing HTML
SQLite for the database

"Inspired by the Pampas and crafted with yerba mate in South America: an authentic gaucho product."
