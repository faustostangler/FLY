import sqlite3
import os
import shutil
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from cachetools import cached, TTLCache

from utils import system
from utils import settings
from utils import selenium_driver

class CompanyScraper:
    # Configuração de cache
    cache = TTLCache(maxsize=3000, ttl=60*5)

    def __init__(self):
        # Instancia o WebDriver e WebDriverWait usando a função `initialize_driver` existente
        self.driver, self.driver_wait = selenium_driver.initialize_driver()

    @cached(cache)
    def get_raw_code(self, url=settings.companies_url):
        try:
            select_page_xpath = '//*[@id="selectPage"]'
            pagination_xpath = '//*[@id="listing_pagination"]/pagination-template/ul'
            nav_bloc_xpath = '//*[@id="nav-bloco"]/div'
            next_page_xpath = '//*[@id="listing_pagination"]/pagination-template/ul/li[10]/a'

            self.driver.get(url)
            system.choose(select_page_xpath, self.driver, self.driver_wait)

            text = system.text(pagination_xpath, self.driver_wait)
            pages = list(map(int, re.findall(r'\d+', text)))
            total_pages = max(pages) - 1

            raw_code = []
            start_time = time.time()

            for i, page in enumerate(range(0, total_pages + 1)):
                system.wait_forever(self.driver_wait, nav_bloc_xpath)
                inner_html = system.raw_text(nav_bloc_xpath, self.driver_wait)
                raw_code.append(inner_html)

                if i != total_pages:
                    system.click(next_page_xpath, self.driver_wait)

                extra_info = [f'page {page + 1}']
                system.print_info(i, extra_info, start_time, total_pages + 1)

        except Exception as e:
            system.log_error(e)
            raw_code = []

        return raw_code

    @cached(cache)
    def get_company_ticker(self):
        field_mapping = {
            'ticker': {'tag': 'h5', 'class': 'card-title2'},
            'company_name': {'tag': 'p', 'class': 'card-title'},
            'trading_name': {'tag': 'p', 'class': 'card-text'},
            'listing': {'tag': 'p', 'class': 'card-nome'}
        }

        raw_code = self.get_raw_code(settings.companies_url)
        company_tickers = {}

        for inner_html in raw_code:
            soup = BeautifulSoup(inner_html, 'html.parser')
            cards = soup.find_all('div', class_='card-body')

            for card in cards:
                try:
                    extracted_info = {
                        key: system.clean_text(card.find(details['tag'], class_=details['class']).text)
                        for key, details in field_mapping.items()
                    }

                    listing = extracted_info['listing']
                    if listing:
                        for abbr, full_name in settings.governance_levels.items():
                            new_listing = system.clean_text(listing.replace(abbr, full_name))
                            if new_listing != listing:
                                extracted_info['listing'] = new_listing
                                break

                    company_tickers[extracted_info['company_name']] = {
                        'ticker': extracted_info['ticker'],
                        'trading_name': extracted_info['trading_name'],
                        'listing': extracted_info['listing']
                    }
                except Exception as e:
                    system.log_error(e)

        return company_tickers

    def extract_company_data(self, detail_soup):
        ticker_table_id = 'accordionBody2'
        company_info = detail_soup.find('div', class_='card-body')

        ticker_codes = []
        isin_codes = []

        accordion_body = detail_soup.find('div', {'id': ticker_table_id})
        if accordion_body:
            rows = accordion_body.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) > 1:
                    ticker_codes.append(system.clean_text(cols[0].text))
                    isin_codes.append(system.clean_text(cols[1].text))

        cnpj_element = company_info.find(text='CNPJ')
        cnpj = re.sub(r'\D', '', cnpj_element.find_next('p', class_='card-linha').text) if cnpj_element else ''
        activity_element = company_info.find(text='Atividade Principal')
        activity = activity_element.find_next('p', class_='card-linha').text if activity_element else ''
        sector_element = company_info.find(text='Classificação Setorial')
        sector_classification = sector_element.find_next('p', class_='card-linha').text if sector_element else ''
        website_element = company_info.find(text='Site')
        website = website_element.find_next('a').text if website_element else ''
        registrar_element = detail_soup.find(text='Escriturador')
        registrar = registrar_element.find_next('span').text.strip() if registrar_element else ''

        sectors = sector_classification.split('/')
        sector = system.clean_text(sectors[0].strip()) if len(sectors) > 0 else ''
        subsector = system.clean_text(sectors[1].strip()) if len(sectors) > 1 else ''
        segment = system.clean_text(sectors[2].strip()) if len(sectors) > 2 else ''

        return {
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

    def get_company_info(self, company_tickers):
        all_company_info = {}
        total_companies = len(company_tickers)
        existing_companies = self.load_existing_data(settings.db_name)

        companies_to_process = {name: info for name, info in company_tickers.items() if name not in existing_companies}
        total_companies_to_process = len(companies_to_process)

        start_time = time.time()
        all_data = []

        for i, (company_name, info) in enumerate(companies_to_process.items()):
            try:
                self.driver.get(settings.company_url)
                search_field_xpath = '//*[@id="keyword"]'
                nav_tab_content_xpath = '//*[@id="nav-tabContent"]'
                overview_xpath = '//*[@id="divContainerIframeB3"]/app-companies-overview/div/div[1]/div/div'

                search_field = system.wait_forever(self.driver_wait, search_field_xpath)
                search_field.clear()
                search_field.send_keys(company_name)
                search_field.send_keys(Keys.RETURN)

                system.wait_forever(self.driver_wait, nav_tab_content_xpath)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                cards = soup.find_all('div', class_='card-body')

                company_found = False
                for card in cards:
                    card_ticker = system.clean_text(card.find('h5', class_='card-title2').text)
                    if card_ticker == info['ticker']:
                        card_xpath = f'//h5[text()="{card_ticker}"]'
                        system.click(card_xpath, self.driver_wait)
                        system.wait_forever(self.driver_wait, overview_xpath)

                        match = re.search(r'/main/(\d+)/', self.driver.current_url)
                        cvm_code = match.group(1) if match else ''
                        info['cvm_code'] = cvm_code

                        detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        company_data = self.extract_company_data(detail_soup)

                        info.update(company_data)
                        company_found = True
                        break

            except Exception as e:
                system.log_error(f"Error processing company {company_name}: {e}")

            all_company_info[company_name] = info
            extra_info = [info['ticker'], info['cvm_code'], company_name]
            system.print_info(i, extra_info, start_time, total_companies_to_process)

            all_data.append({'company_name': company_name, **info})

            if (total_companies_to_process - i - 1) % (settings.batch_size // 5) == 0 or i == total_companies - 1:
                all_data = self.save_to_db(all_data, settings.db_name)
                all_data.clear()

        return all_company_info

    def load_existing_data(self, db_name=settings.db_name):
        existing_data = {}
        try:
            db_path = os.path.join(settings.db_folder, db_name)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM company_info")
            columns = [column[0] for column in cursor.description]

            for row in cursor.fetchall():
                company_name = row[columns.index('company_name')]
                existing_data[company_name] = dict(zip(columns, row))

            conn.close()
        except Exception as e:
            system.log_error(e)

        return existing_data

    def save_to_db(self, data, db_name=settings.db_name):
        try:
            if not data:
                return

            db_path = os.path.join(settings.db_folder, db_name)
            os.makedirs(settings.db_folder, exist_ok=True)

            backup_name = f"{os.path.splitext(db_name)[0]} backup.db"
            backup_path = os.path.join(settings.db_folder, backup_name)
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

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

            conn.commit()
            conn.close()

            print('Partial save completed...')
            return data

        except Exception as e:
            system.log_error(e)

    def update_and_save_batch(self, existing_data, new_data_batch):
        batch_to_save = []

        for info in new_data_batch:
            company_name = info['company_name']
            if company_name in existing_data:
                existing_info = existing_data[company_name]
                changes = {key: info[key] for key in info if info[key] != existing_info.get(key)}
                if changes:
                    batch_to_save.append(info)
            else:
                batch_to_save.append(info)

        self.save_to_db(batch_to_save)

    def run(self):
        existing_data = self.load_existing_data()
        new_company_tickers = self.get_company_ticker()
        new_company_info = self.get_company_info(new_company_tickers)

        total_companies = len(new_company_info)
        batch_size = settings.batch_size
        all_company_info = []

        for i in range(0, total_companies, batch_size):
            batch = list(new_company_info.items())[i:i + batch_size]
            self.update_and_save_batch(existing_data, [info for _, info in batch])
            all_company_info.extend(batch)

        return all_company_info

    def close(self):
        """Fecha o WebDriver"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    try:
        scraper = CompanyScraper()
        scraper.run()
    except Exception as e:
        system.log_error(e)
    finally:
        scraper.close()
