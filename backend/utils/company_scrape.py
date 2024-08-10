import sqlite3
import os
import shutil
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from cachetools import cached, TTLCache
from utils import system
from utils import settings

# Cache configuration with cachetools: maxsize=3000, ttl=5 minutes
cache = TTLCache(maxsize=3000, ttl=60*5)

@cached(cache)
def get_raw_code(driver, driver_wait, url=settings.companies_url):
    """
    Retrieves the raw HTML code from the B3 companies page.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - driver_wait: The WebDriverWait instance.
    - url (str): URL of the B3 companies page.

    Returns:
    list: A list of raw HTML strings.
    """
    try:
        # XPaths and other variables
        select_page_xpath = '//*[@id="selectPage"]'
        pagination_xpath = '//*[@id="listing_pagination"]/pagination-template/ul'
        nav_bloc_xpath = '//*[@id="nav-bloco"]/div'
        next_page_xpath = '//*[@id="listing_pagination"]/pagination-template/ul/li[10]/a'

        # Navigate to the specified URL
        driver.get(url)

        # Select the maximum number of records per page
        batch = system.choose(select_page_xpath, driver, driver_wait)

        # Extract the total number of pages
        text = system.text(pagination_xpath, driver_wait)
        pages = list(map(int, re.findall(r'\d+', text)))
        total_pages = max(pages) - 1

        raw_code = []
        start_time = time.time()

        for i, page in enumerate(range(0, total_pages + 1)):
            # Wait for the navigation block to load
            system.wait_forever(driver_wait, nav_bloc_xpath)

            # Extract the HTML of the current page
            inner_html = system.raw_text(nav_bloc_xpath, driver_wait)
            raw_code.append(inner_html)

            if i != total_pages:
                # Click to advance to the next page
                system.click(next_page_xpath, driver_wait)

            # Print progress information
            extra_info = [f'page {page + 1}']
            system.print_info(i, extra_info, start_time, total_pages + 1)

    except Exception as e:
        # Log the error and return an empty list if something goes wrong
        system.log_error(e)
        raw_code = []

    return raw_code

@cached(cache)
def get_company_ticker(driver, driver_wait):
    """
    Extracts company tickers and names from raw HTML code.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - driver_wait: The WebDriverWait instance.

    Returns:
    dict: A dictionary with company names as keys and a nested dictionary with ticker, trading name, and listing as values.
    """
    # Define the mapping for extracting company details
    field_mapping = {
        'ticker': {'tag': 'h5', 'class': 'card-title2'},
        'company_name': {'tag': 'p', 'class': 'card-title'},
        'trading_name': {'tag': 'p', 'class': 'card-text'},
        'listing': {'tag': 'p', 'class': 'card-nome'}
    }

    # Retrieve the raw HTML code from the companies page
    raw_code = get_raw_code(driver, driver_wait, settings.companies_url)

    company_tickers = {}

    for inner_html in raw_code:
        soup = BeautifulSoup(inner_html, 'html.parser')
        # Locate all company cards in the HTML
        cards = soup.find_all('div', class_='card-body')

        for card in cards:
            try:
                # Extract information from the card using the field mapping
                extracted_info = {
                    key: system.clean_text(card.find(details['tag'], class_=details['class']).text)
                    for key, details in field_mapping.items()
                }

                # Expand the abbreviation of governance levels
                listing = extracted_info['listing']
                if listing:
                    for abbr, full_name in settings.governance_levels.items():
                        new_listing = system.clean_text(listing.replace(abbr, full_name))
                        if new_listing != listing:
                            extracted_info['listing'] = new_listing
                            break

                # Store the information in the company_tickers dictionary
                company_tickers[extracted_info['company_name']] = {
                    'ticker': extracted_info['ticker'],
                    'trading_name': extracted_info['trading_name'],
                    'listing': extracted_info['listing']
                }
            except Exception as e:
                # Log errors without interrupting the loop
                system.log_error(e)

    return company_tickers

def extract_company_data(detail_soup):
    """
    Extracts detailed company information from the provided BeautifulSoup object.

    Parameters:
    - detail_soup (BeautifulSoup): The BeautifulSoup object containing the company detail page HTML.

    Returns:
    dict: A dictionary containing the extracted company information.
    """
    # ID of the element containing ticker information
    ticker_table_id = 'accordionBody2'

    company_info = detail_soup.find('div', class_='card-body')

    ticker_codes = []
    isin_codes = []

    # Extract ticker and ISIN codes
    accordion_body = detail_soup.find('div', {'id': ticker_table_id})
    if accordion_body:
        rows = accordion_body.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) > 1:
                ticker_codes.append(system.clean_text(cols[0].text))
                isin_codes.append(system.clean_text(cols[1].text))

    # Extract the company's CNPJ
    cnpj_element = company_info.find(text='CNPJ')
    cnpj = re.sub(r'\D', '', cnpj_element.find_next('p', class_='card-linha').text) if cnpj_element else ''
    
    # Extract the company's main activity
    activity_element = company_info.find(text='Atividade Principal')
    activity = activity_element.find_next('p', class_='card-linha').text if activity_element else ''
    
    # Extract the company's sector classification
    sector_element = company_info.find(text='Classificação Setorial')
    sector_classification = sector_element.find_next('p', class_='card-linha').text if sector_element else ''
    
    # Extract the company's website
    website_element = company_info.find(text='Site')
    website = website_element.find_next('a').text if website_element else ''
    
    # Extract the name of the registrar
    registrar_element = detail_soup.find(text='Escriturador')
    registrar = registrar_element.find_next('span').text.strip() if registrar_element else ''

    # Split the sector classification into sector, subsector, and segment
    sectors = sector_classification.split('/')
    sector = system.clean_text(sectors[0].strip()) if len(sectors) > 0 else ''
    subsector = system.clean_text(sectors[1].strip()) if len(sectors) > 1 else ''
    segment = system.clean_text(sectors[2].strip()) if len(sectors) > 2 else ''

    # Return a dictionary with the company's information
    company_data = {
        "activity": activity,
        "sector": sector,
        "subsector": subsector,
        "segment": segment, 
        "cnpj": cnpj,
        "website": website,
        "sector_classification": sector_classification,
        "ticker_codes": ticker_codes,
        "isin_codes": isin_codes,
        "registrar": registrar,
    }

    return company_data

def get_company_info(driver, driver_wait, company_tickers):
    """
    Retrieves detailed information for each company in the company_tickers list.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - driver_wait: The WebDriverWait instance.
    - company_tickers (dict): A dictionary with company names as keys and ticker information as values.

    Returns:
    dict: A dictionary with company names as keys and detailed company information as values.
    """
    all_company_info = {}
    total_companies = len(company_tickers)
    existing_companies = load_existing_data(settings.db_name)

    # Filter companies that need to be processed (not in the database)
    companies_to_process = {name: info for name, info in company_tickers.items() if name not in existing_companies}
    total_companies_to_process = len(companies_to_process)
    
    start_time = time.time()
    all_data = []

    for i, (company_name, info) in enumerate(companies_to_process.items()):
        try:
            # Navigate to the company URL
            driver.get(settings.company_url)

            # Search for the company name
            search_field_xpath = '//*[@id="keyword"]'
            nav_tab_content_xpath = '//*[@id="nav-tabContent"]'
            overview_xpath = '//*[@id="divContainerIframeB3"]/app-companies-overview/div/div[1]/div/div'

            search_field = system.wait_forever(driver_wait, search_field_xpath)
            search_field.clear()
            search_field.send_keys(company_name)
            search_field.send_keys(Keys.RETURN)

            # Wait for the results to load
            system.wait_forever(driver_wait, nav_tab_content_xpath)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.find_all('div', class_='card-body')

            company_found = False
            for card in cards:
                # Check if the company's ticker matches the expected one
                card_ticker = system.clean_text(card.find('h5', class_='card-title2').text)
                if card_ticker == info['ticker']:
                    # Click on the corresponding company card
                    card_xpath = f'//h5[text()="{card_ticker}"]'
                    system.click(card_xpath, driver_wait)
                    
                    # Wait for the company's overview to load
                    system.wait_forever(driver_wait, overview_xpath)

                    # Extract the CVM code from the current URL
                    match = re.search(r'/main/(\d+)/', driver.current_url)
                    cvm_code = match.group(1) if match else ''
                    info['cvm_code'] = cvm_code

                    # Extract the company's detailed data
                    detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    company_data = extract_company_data(detail_soup)

                    # Update the company's information with the detailed data
                    info.update(company_data)
                    company_found = True
                    break

        except Exception as e:
            # Log errors when processing a specific company
            system.log_error(f"Error processing company {company_name}: {e}")
            pass

        all_company_info[company_name] = info
        extra_info = [info['ticker'], info['cvm_code'], company_name]
        system.print_info(i, extra_info, start_time, total_companies_to_process)

        all_data.append({'company_name': company_name, **info})

        # Save the data periodically in batches
        if (total_companies_to_process - i - 1) % (settings.batch_size // 5) == 0 or i == total_companies - 1:
            all_data = save_to_db(all_data, settings.db_name)
            all_data.clear()

    return all_company_info

def load_existing_data(db_name=settings.db_name):
    """
    Loads existing company data from the database into a dictionary.

    Parameters:
    - db_name (str): Name of the database file.

    Returns:
    dict: A dictionary containing existing company data with the company name as the key.
    """
    existing_data = {}
    try:
        # Establish connection to the database
        db_path = os.path.join(settings.db_folder, db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute SQL query to retrieve all company data
        cursor.execute("SELECT * FROM company_info")
        columns = [column[0] for column in cursor.description]

        # Populate the dictionary with the fetched data
        for row in cursor.fetchall():
            company_name = row[columns.index('company_name')]
            existing_data[company_name] = dict(zip(columns, row))

        conn.close()
    except Exception as e:
        # Log any errors encountered
        system.log_error(e)
    
    return existing_data

def save_to_db(data, db_name=settings.db_name):
    """
    Saves the company data to the database.

    Parameters:
    - data (list): A list of dictionaries containing company information.
    - db_name (str): Name of the database file.
    """
    try:
        if not data:
            return

        # Ensure the database folder exists
        db_path = os.path.join(settings.db_folder, db_name)
        os.makedirs(settings.db_folder, exist_ok=True)

        # Backup existing database before making changes
        backup_name = f"{os.path.splitext(db_name)[0]} backup.db"
        backup_path = os.path.join(settings.db_folder, backup_name)
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)

        # Establish connection to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the company_info table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS company_info (
                            cvm_code TEXT,
                            company_name TEXT PRIMARY KEY,
                            ticker TEXT,
                            ticker_codes TEXT,
                            isin_codes TEXT,
                            trading_name TEXT,
                            sector TEXT,
                            subsector TEXT,
                            segment TEXT,
                            listing TEXT,
                            activity TEXT,
                            registrar TEXT,
                            cnpj TEXT,
                            website TEXT)''')

        # Insert new data or update existing records
        for info in data:
            cursor.execute('''INSERT INTO company_info (cvm_code, company_name, ticker, ticker_codes, isin_codes, trading_name, sector, subsector, segment, listing, activity, registrar, cnpj, website)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(company_name) DO UPDATE SET
                            cvm_code=excluded.cvm_code,
                            ticker=excluded.ticker,
                            ticker_codes=excluded.ticker_codes,
                            isin_codes=excluded.isin_codes,
                            trading_name=excluded.trading_name,
                            sector=excluded.sector,
                            subsector=excluded.subsector,
                            segment=excluded.segment,
                            listing=excluded.listing,
                            activity=excluded.activity,
                            registrar=excluded.registrar,
                            cnpj=excluded.cnpj,
                            website=excluded.website''',
                            (info['cvm_code'], info['company_name'], info['ticker'], ','.join(info.get('ticker_codes', [])),
                             ','.join(info.get('isin_codes', [])), info.get('trading_name', ''), info.get('sector', ''),
                             info.get('subsector', ''), info.get('segment', ''), info.get('listing', ''),
                             info.get('activity', ''), info.get('registrar', ''), info.get('cnpj', ''), info.get('website', '')))

        # Commit changes and close the connection
        conn.commit()
        conn.close()

        print('Partial save completed...')
        return data
    
    except Exception as e:
        # Log any errors during the saving process
        system.log_error(e)

def update_and_save_batch(existing_data, new_data_batch):
    """
    Compares and updates company data in batches, then saves periodically to the database.

    Parameters:
    - existing_data (dict): Dictionary containing existing company data from the database.
    - new_data_batch (list): List of dictionaries containing new company data to be compared and possibly updated.
    """
    batch_to_save = []
    
    for info in new_data_batch:
        company_name = info['company_name']
        if company_name in existing_data:
            # Compare new data with existing data
            existing_info = existing_data[company_name]
            changes = {key: info[key] for key in info if info[key] != existing_info.get(key)}
            if changes:
                # If changes are found, add to the batch for saving
                batch_to_save.append(info)
        else:
            # If the company does not exist in the database, add it as new
            batch_to_save.append(info)
    
    # Save the batch of updates or new entries to the database
    save_to_db(batch_to_save)

def main(driver, driver_wait):
    """
    Main function to initiate the extraction and updating of company information.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - driver_wait: The WebDriverWait instance.

    Returns:
    dict: A dictionary with updated company information.
    """
    try:
        # Step 1: Load existing company data from the database
        existing_data = load_existing_data()

        # Step 2: Extract the new company tickers and names from the HTML
        new_company_tickers = get_company_ticker(driver, driver_wait)

        # Step 3: Retrieve detailed information for each company
        new_company_info = get_company_info(driver, driver_wait, new_company_tickers)

        # Step 4: Process and save the data in batches
        total_companies = len(new_company_info)
        batch_size = settings.batch_size
        all_company_info = []

        for i in range(0, total_companies, batch_size):
            batch = list(new_company_info.items())[i:i + batch_size]
            update_and_save_batch(existing_data, [info for _, info in batch])
            all_company_info.extend(batch)

        return dict(all_company_info)
    except Exception as e:
        # Log any errors during the main process
        system.log_error(e)
        return {}

if __name__ == "__main__":
    try:
        print(settings.module_alert)
    except Exception as e:
        system.log_error(e)
