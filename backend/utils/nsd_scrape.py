import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from cachetools import cached, TTLCache
import time
import os
import shutil

from utils import system, settings

class NSDScraper:
    """
    A class to scrape and store NSD (Número Sequencial do Documento) data from a specific source.
    """

    # Cache configuration: stores up to 100,000 items for 10 minutes
    cache = TTLCache(maxsize=100000, ttl=600)

    def __init__(self):
        """
        Initialize the NSDScraper with database settings.
        """
        self.db_name = settings.db_name
        self.db_folder = settings.db_folder
        self.db_full_path = os.path.join(self.db_folder, self.db_name)

    def get_max_nsd(self):
        """
        Retrieve the maximum NSD value from the database.

        Returns:
        int: The maximum NSD value found in the database, or 0 if none exists.
        """
        try:
            with sqlite3.connect(self.db_full_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(nsd) FROM nsd")
                max_nsd = cursor.fetchone()[0]
                return max_nsd if max_nsd is not None else 0
        except Exception as e:
            # system.log_error(f"Error retrieving max NSD from database: {e}")
            return 0

    def get_missing_nsds(self):
        """
        Identify missing NSD values in the database.

        Returns:
        list: A list of missing NSD values.
        """
        try:
            with sqlite3.connect(self.db_full_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT nsd + 1 AS missing_nsd
                    FROM nsd t1
                    WHERE NOT EXISTS (SELECT 1 FROM nsd t2 WHERE t2.nsd = t1.nsd + 1)
                    ORDER BY t1.nsd
                """)
                missing_nsds = [row[0] for row in cursor.fetchall()]
                return missing_nsds
        except Exception as e:
            # system.log_error(f"Error retrieving missing NSDs from database: {e}")
            return []

    def generate_nsd_range(self):
        """
        Generate the range of NSD values to scrape, including missing and new NSDs.

        Returns:
        list: A list of NSD values to scrape.
        """
        try:
            # Step 1: Get the maximum NSD and the sent date of the last NSD
            max_nsd, last_sent_date = self.get_last_nsd_and_date()

            # Step 2: Calculate the daily submission estimate from the database
            daily_submission_estimate = self.calculate_daily_submission_estimate()

            # Step 3: Calculate the date difference from today
            days_elapsed = (datetime.now() - last_sent_date).days + 1 if last_sent_date else 1

            # Step 4: Calculate the number of new NSDs with a safety factor
            estimated_new_nsds = int(daily_submission_estimate * days_elapsed * settings.safety_factor)

            # Step 5: Generate the full range of NSDs to scrape
            new_nsds = list(range(max_nsd + 1, max_nsd + estimated_new_nsds + 1))
            missing_nsds = self.get_missing_nsds()
            nsd_range = new_nsds + missing_nsds
            nsd_range = new_nsds + missing_nsds

            return nsd_range
        except Exception as e:
            system.log_error(f"Error generating NSD range: {e}")
            return []

    def calculate_daily_submission_estimate(self):
        """
        Calculate the daily submission estimate based on historical data in the database.

        Returns:
        float: The estimated number of NSDs submitted per day.
        """
        try:
            with sqlite3.connect(self.db_full_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MIN(sent_date), MAX(sent_date), COUNT(*) FROM nsd")
                result = cursor.fetchone()
                
                if result:
                    min_date, max_date, total_nsds = result
                    if min_date and max_date and total_nsds > 0:
                        try:
                            min_date = datetime.strptime(min_date, "%Y-%m-%dT%H:%M:%S")
                        except:
                            min_date = datetime.strptime(min_date, "%Y-%m-%d %H:%M:%S")
                        try:
                            max_date = datetime.strptime(max_date, "%Y-%m-%dT%H:%M:%S")
                        except:
                            max_date = datetime.strptime(max_date, "%Y-%m-%d %H:%M:%S")
                        days_span = (max_date - min_date).days
                        if days_span > 0:
                            return total_nsds / days_span  # Average submissions per day
                return settings.default_daily_submission_estimate  # Fallback to a default estimate if data is insufficient
        except Exception as e:
            # system.log_error(f"Error calculating daily submission estimate: {e}")
            return settings.default_daily_submission_estimate

    def get_last_nsd_and_date(self):
        """
        Retrieve the maximum NSD and its corresponding sent date from the database.

        Returns:
        tuple: The maximum NSD and its sent date.
        """
        try:
            with sqlite3.connect(self.db_full_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nsd, sent_date FROM nsd ORDER BY nsd DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    last_nsd, last_sent_date = result
                    try:
                        last_sent_date = datetime.strptime(last_sent_date, "%Y-%m-%dT%H:%M:%S")
                    except:
                        last_sent_date = datetime.strptime(last_sent_date, "%Y-%m-%d %H:%M:%S")
                    return last_nsd, last_sent_date
                return 0, None  # If no NSD is found, return 0 and None
        except Exception as e:
            # system.log_error(f"Error retrieving last NSD and date from database: {e}")
            return 0, None

    @cached(cache)
    def fetch_page(self, nsd):
        """
        Fetch the HTML content of an NSD page

        Parameters:
        nsd (int): The NSD value to fetch.

        Returns:
        str: The HTML content of the NSD page.
        """
        try:
            url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"
            headers = system.header_random()  # Use the random headers from the system module
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            return html
        except Exception as e:
            system.log_error(f"Error fetching NSD page {nsd}: {e}")
            return None

    def parse_nsd_data(self, html, nsd):
        """
        Parse the HTML content to extract NSD data.

        Parameters:
        html (str): The HTML content of the NSD page.
        nsd (int): The NSD value being parsed.

        Returns:
        dict: A dictionary of the parsed NSD data.
        """
        try:
            # Hard-coded XPaths or CSS selectors
            company_name_selector = '#lblNomeCompanhia'
            dri_selector = '#lblNomeDRI'
            nsd_type_version_selector = '#lblDescricaoCategoria'
            auditor_selector = '#lblAuditor'
            responsible_auditor_selector = '#lblResponsavelTecnico'
            protocolo_selector = '#lblProtocolo'
            quarter_selector = '#lblDataDocumento'
            sent_date_selector = '#lblDataEnvio'
            reason_selector = '#lblMotivoCancelamentoReapresentacao'

            # Parse the HTML content
            soup = BeautifulSoup(html, 'html.parser')
            data = {'nsd': nsd}

            # Extracting data using the defined selectors
            data['company_name'] = system.clean_text(soup.select_one(company_name_selector).text)
            data['dri'] = system.clean_text(soup.select_one(dri_selector).text.split('-')[0].strip())
            nsd_type_version = soup.select_one(nsd_type_version_selector).text
            data['nsd_type'] = system.clean_text(nsd_type_version.split('-')[0].strip())
            data['version'] = int(nsd_type_version.split('V')[-1])
            data['auditor'] = system.clean_text(soup.select_one(auditor_selector).text.split('-')[0].strip())
            data['responsible_auditor'] = system.clean_text(soup.select_one(responsible_auditor_selector).text)
            data['protocol'] = soup.select_one(protocolo_selector).text.replace('-', '').strip()

            # Handle quarter parsing
            raw_date = soup.select_one(quarter_selector).text
            try:
                if len(raw_date) == 4:  # Only a year is provided
                    # Assuming the last day of the year
                    data['quarter'] = datetime.strptime(f"31/12/{raw_date}", "%d/%m/%Y")
                else:
                    data['quarter'] = datetime.strptime(raw_date, "%d/%m/%Y")
            except ValueError as e:
                # system.log_error(f"Error parsing date for NSD {nsd}: {e}")
                return None

            # Parse the sent date
            try:
                data['sent_date'] = datetime.strptime(soup.select_one(sent_date_selector).text, "%d/%m/%Y %H:%M:%S")
            except ValueError as e:
                system.log_error(f"Error parsing sent date for NSD {nsd}: {e}")
                data['sent_date'] = None  # Set to None if parsing fails

            data['reason'] = system.clean_text(soup.select_one(reason_selector).text)

            return data if data['sent_date'] else None

        except Exception as e:
            # system.log_error(f"Error parsing NSD {nsd}: {e}")
            return None

    def save_to_db(self, nsd_data):
        """
        Save a list of NSD data to the SQLite database, with backup.

        Parameters:
        nsd_data (list): A list of dictionaries containing NSD data.
        """
        try:
            # Ensure the database directory exists
            os.makedirs(self.db_folder, exist_ok=True)

            # Backup the existing database before saving new data
            backup_name = f"{os.path.splitext(self.db_name)[0]} {settings.backup_name}.db"
            backup_path = os.path.join(self.db_folder, backup_name)
            if os.path.exists(self.db_full_path):
                shutil.copy2(self.db_full_path, backup_path)

            with sqlite3.connect(self.db_full_path) as conn:
                cursor = conn.cursor()

                # Ensure the table exists with the correct schema and field order
                cursor.execute('''CREATE TABLE IF NOT EXISTS nsd
                                (nsd INTEGER PRIMARY KEY, 
                                company_name TEXT, 
                                quarter TEXT, 
                                nsd_type TEXT, 
                                version INTEGER, 
                                dri TEXT,
                                auditor TEXT,
                                responsible_auditor TEXT, 
                                protocol TEXT, 
                                sent_date TEXT, 
                                reason TEXT)''')

                # Iterate over the data list and insert or update records
                for data in nsd_data:
                    # Handle None values and quarter formatting
                    sent_date_str = data['sent_date'].strftime("%Y-%m-%d %H:%M:%S") if data['sent_date'] else None

                    # Perform the insert or update with the correct field order
                    cursor.execute('''INSERT INTO nsd 
                                    (nsd, company_name, quarter, nsd_type, version, dri, auditor, responsible_auditor, protocol, sent_date, reason) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ON CONFLICT(nsd) DO UPDATE SET
                                    company_name=excluded.company_name,
                                    quarter=excluded.quarter,
                                    nsd_type=excluded.nsd_type,
                                    version=excluded.version,
                                    dri=excluded.dri,
                                    auditor=excluded.auditor,
                                    responsible_auditor=excluded.responsible_auditor,
                                    protocol=excluded.protocol,
                                    sent_date=excluded.sent_date,
                                    reason=excluded.reason''',
                                (data['nsd'], data['company_name'], data['quarter'], data['nsd_type'], data['version'], 
                                data['dri'], data['auditor'], data['responsible_auditor'], 
                                data['protocol'], sent_date_str, data['reason']))

                # Commit the transaction
                conn.commit()
                print('Partial save completed...')
            return nsd_data

        except Exception as e:
            system.log_error(f"Error saving data to database: {e}")

    def scrape_nsd(self):
        """
        The main method to scrape NSD data, parse it, and save it to the database.
        """
        try:
            nsd_range = self.generate_nsd_range()
            nsd_data = []
            total_nsds = len(nsd_range)
            start_time = time.time()
            limit_counter = 0

            for i, nsd in enumerate(nsd_range):
                try:
                    html = self.fetch_page(nsd)
                    if html:
                        data = self.parse_nsd_data(html, nsd)
                        if not data:
                            extra_info = [nsd]
                        else:
                        # Prepare extra information for progress reporting
                            extra_info = [nsd, data['sent_date'], data['quarter'].strftime("%Y-%m-%d"), data['nsd_type'], data['company_name']]

                            nsd_data.append(data)

                    # Print progress information
                    system.print_info(i, total_nsds, start_time, extra_info)

                    # Regressive periodic save
                    if (total_nsds - i - 1) % (settings.batch_size // 1) == 0:
                        if nsd_data:
                            nsd_data = self.save_to_db(nsd_data)
                            nsd_data.clear()
                            limit_counter = 0
                        else:
                            limit_counter += 1
                            # Check if the counter has reached 5
                            if limit_counter >= 2:
                                nsd_data = self.save_to_db(nsd_data)
                                return nsd_range # Interrupts the function so it does not go to infinity

                except Exception as e:
                    system.log_error(f"Error processing NSD {nsd}: {e}")
            system.db_optimize(self.db_name)
            return nsd_range
        
        except Exception as e:
            system.log_error(f"Error in scrape_nsd: {e}")

if __name__ == "__main__":
    try:
        scraper = NSDScraper()
        scraper.scrape_nsd()
    except Exception as e:
        system.log_error(e)
