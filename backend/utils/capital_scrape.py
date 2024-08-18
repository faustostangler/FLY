import os
import glob
import sqlite3
import pandas as pd
import time
import shutil
from io import StringIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import itertools

from utils import system
from utils import settings
from utils import selenium_driver

class CapitalDataScraper:
    """
    A class to scrape and store capital data from NSD pages.
    """

    def __init__(self):
        """Initialize the scraper with settings and WebDriver."""
        self.driver, self.driver_wait = selenium_driver.initialize_driver()
        self.db_folder = settings.db_folder
        self.db_name = settings.db_name

    def load_nsd_list(self):
        """
        Load NSD data from the nsd table in b3.db, filtered by settings.statements_types.

        Returns:
        DataFrame: A DataFrame containing the filtered NSD data.
        """
        try:
            db_path = os.path.join(self.db_folder, settings.db_name)  # Full path to b3.db
            query = """
                SELECT *
                FROM nsd
                WHERE nsd_type IN ({})
            """.format(','.join('?' for _ in settings.statements_types))

            with sqlite3.connect(db_path) as conn:
                nsd_data = pd.read_sql_query(query, conn, params=settings.statements_types)

            return nsd_data.drop_duplicates()
        except Exception as e:
            system.log_error(f"Error loading NSD data: {e}")
            return pd.DataFrame()

    def load_financial_statements(self):
        """
        Load existing financial statements from all .db files in the db_folder.

        Returns:
        DataFrame: A DataFrame containing the NSD data from all files.
        """
        included_patterns = [settings.table_name]
        excluded_patterns = [settings.backup_name, 'math']  # List of patterns to exclude from filenames

        try:
            all_dfs = []

            # Get all .db files in the db_folder that include any of the included_patterns and exclude the excluded_patterns
            database_files = [
                db_file for db_file in glob.glob(f"{self.db_folder}/*.db")
                if any(inc in os.path.basename(db_file) for inc in included_patterns)
                and not any(exc in os.path.basename(db_file) for exc in excluded_patterns)
            ]

            for db_file in database_files:
                with sqlite3.connect(db_file) as conn:
                    df = pd.read_sql_query(f"SELECT * FROM {settings.table_name}", conn)
                    all_dfs.append(df)

            if all_dfs:
                return pd.concat(all_dfs, ignore_index=True).drop_duplicates()
            else:
                return pd.DataFrame(columns=settings.statements_columns)
        except Exception as e:
            system.log_error(f"Error loading existing NSD data: {e}")
            return pd.DataFrame()

    def load_company_info(self):
        try:
            db_path = os.path.join(self.db_folder, settings.db_name)  # Full path to b3.db
            with sqlite3.connect(db_path) as conn:
                query = "SELECT * FROM company_info"
                company_info_df = pd.read_sql_query(query, conn)
            return company_info_df
        except Exception as e:
            system.log_error(f"Error loading company_info data: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    def scrape_financial_data(self, cmbGrupo, cmbQuadro):
        """
        Scrapes capital data from the specified page.

        Parameters:
        - group_value: The group combo box value.
        - quadro_value: The frame combo box value.

        Returns:
        - DataFrame: A DataFrame containing the scraped data.
        """
        try:
            drop_items = '3.99'
            xpath_grupo = '//*[@id="cmbGrupo"]'
            xpath_quadro = '//*[@id="cmbQuadro"]'
            xpath_frame = '//*[@id="iFrameFormulariosFilho"]'

            # Select the correct options for cmbGrupo and cmbQuadro
            grupo = system.select(xpath_grupo, cmbGrupo, self.driver, self.driver_wait)
            quadro = system.select(xpath_quadro, cmbQuadro, self.driver, self.driver_wait)

            # selenium enter frame
            frame = system.wait_forever(self.driver_wait, xpath_frame)
            frame = self.driver.find_elements(By.XPATH, xpath_frame)
            self.driver.switch_to.frame(frame[0])

            # read and clean quadro
            xpath = '//*[@id="ctl00_cphPopUp_tbDados"]'
            thousand = system.wait_forever(self.driver_wait, xpath)

            xpath = '//*[@id="TituloTabelaSemBorda"]'
            thousand = self.driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text
            thousand = 1000 if "Mil" in thousand else 1

            html_content = self.driver.page_source
            df1 = pd.read_html(StringIO(html_content), header=0)[0]
            df2 = pd.read_html(StringIO(html_content), header=0, thousands='.')[0].fillna(0)

            df1 = df1.iloc[:,0:3]
            df2 = df2.iloc[:,0:3]
            df1.columns = settings.financial_capital_columns
            df2.columns = settings.financial_capital_columns
            df = pd.concat([df1.iloc[:, :2], df2.iloc[:, 2:3]], axis=1)

            col = df.iloc[:, 2].astype(str)
            col = col.str.replace('.', '', regex=False)
            col = col.str.replace(',', '.', regex=False)
            col = pd.to_numeric(col, errors='coerce')
            col = col * thousand
            df.iloc[:, 2] = col

            df = df[~df[settings.financial_capital_columns[0]].str.startswith(drop_items)]

            # selenium exit frame
            self.driver.switch_to.parent_frame()

            return df
        
        except Exception as e:
            # system.log_error(e)
            return None

    def scrape_capital_data(self, cmbGrupo, cmbQuadro):
        """
        Process the scraped capital data into a DataFrame.

        Parameters:
        - cmbGrupo: The group combo box value.
        - cmbQuadro: The frame combo box value.

        Returns:
        DataFrame: A Pandas DataFrame containing the processed data.
        """
        try:
            # Define the XPaths
            xpath_grupo = '//*[@id="cmbGrupo"]'
            xpath_quadro = '//*[@id="cmbQuadro"]'
            xpath_frame = '//*[@id="iFrameFormulariosFilho"]'
            xpath_thousand = '//*[@id="UltimaTabela"]/table/tbody[1]/tr[1]/td[1]/b'
            thousand_word = 'Mil'
            
            # XPaths for the different data points
            acoes_on_xpath = '//*[@id="QtdAordCapiItgz_1"]'
            acoes_pn_xpath = '//*[@id="QtdAprfCapiItgz_1"]'
            acoes_on_tesouraria_xpath = '//*[@id="QtdAordTeso_1"]'
            acoes_pn_tesouraria_xpath = '//*[@id="QtdAprfTeso_1"]'

            # Select the correct options for cmbGrupo and cmbQuadro
            grupo = system.select(xpath_grupo, cmbGrupo, self.driver, self.driver_wait)
            quadro = system.select(xpath_quadro, cmbQuadro, self.driver, self.driver_wait)

            # Selenium enter frame
            frame = system.wait_forever(self.driver_wait, xpath_frame)
            self.driver.switch_to.frame(frame)

            # Check if the values are in thousands
            thousand_text = system.wait_forever(self.driver_wait, xpath_thousand).text
            thousand = 1000 if thousand_word in thousand_text else 1

            # Extract the required values
            data = {
                settings.financial_capital_columns[0]: [],  # 'account'
                settings.financial_capital_columns[1]: [],  # 'description'
                settings.financial_capital_columns[2]: []   # 'value'
            }

            # Extract values using the XPaths
            acoes_on = self.driver.find_element(By.XPATH, acoes_on_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_pn = self.driver.find_element(By.XPATH, acoes_pn_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_on_tesouraria = self.driver.find_element(By.XPATH, acoes_on_tesouraria_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_pn_tesouraria = self.driver.find_element(By.XPATH, acoes_pn_tesouraria_xpath).text.strip().replace('.', '').replace(',', '.')

            # Populate the data dictionary using settings values
            data[settings.financial_capital_columns[0]] = [
                settings.accounts['acoes_on'], 
                settings.accounts['acoes_pn'], 
                settings.accounts['acoes_on_tesouraria'], 
                settings.accounts['acoes_pn_tesouraria']
            ]
            data[settings.financial_capital_columns[1]] = [
                settings.descriptions['acoes_on'], 
                settings.descriptions['acoes_pn'], 
                settings.descriptions['acoes_on_tesouraria'], 
                settings.descriptions['acoes_pn_tesouraria']
            ]
            data[settings.financial_capital_columns[2]] = [
                float(acoes_on) * thousand, 
                float(acoes_pn) * thousand, 
                float(acoes_on_tesouraria) * thousand, 
                float(acoes_pn_tesouraria) * thousand
            ]

            df = pd.DataFrame(data)

            # Selenium exit frame
            self.driver.switch_to.parent_frame()
            
            return df
            
        except Exception as e:
            system.log_error(f"Error processing capital data: {e}")
            return None

    def save_to_db(self, df, setor):
        """
        Save the processed capital data to a sector-specific database.

        Parameters:
        - df (DataFrame): The processed capital data as a DataFrame.
        - setor (str): The sector associated with the data.
        """

        try:
            # Hard-coded configurations
            db_name_base = self.db_name.split('.')[0]  # Extract the base name (e.g., 'b3')
            db_name = f"{db_name_base} {settings.table_name} {setor}"  # Create a database file name specific to the sector
            db_path = os.path.join(self.db_folder, db_name + '.db')
            backup_path = os.path.join(self.db_folder, f"{db_name_base} {settings.table_name} {setor} {settings.backup_name}.db")
            
            # SQL command to create the table with a composite primary key
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {settings.table_name} (
                nsd INTEGER,
                sector TEXT,
                subsector TEXT,
                segment TEXT,
                company_name TEXT,
                quarter TEXT,
                version TEXT,
                type TEXT,
                frame TEXT,
                account TEXT,
                description TEXT,
                value REAL,
                PRIMARY KEY (company_name, quarter, version, type, frame, account, description)
            )
            """

            # SQL command for INSERT OR REPLACE
            insert_sql = f"""
            INSERT INTO {settings.table_name} 
            (nsd, sector, subsector, segment, company_name, quarter, version, type, frame, account, description, value) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_name, quarter, version, type, frame, account, description) DO UPDATE SET
            nsd=excluded.nsd,
            sector=excluded.sector,
            subsector=excluded.subsector,
            segment=excluded.segment,
            type=excluded.type,
            frame=excluded.frame,
            account=excluded.account,
            description=excluded.description,
            value=excluded.value
            """

            # Create a backup if the database already exists
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)

            # Connect to the sector-specific database
            with sqlite3.connect(db_path) as conn:
                # Create the table with the composite primary key if it doesn't exist
                conn.execute(create_table_sql)
                conn.commit()

                # Insert data using INSERT OR REPLACE
                for _, row in df.iterrows():
                    conn.execute(insert_sql, tuple(row))

                conn.commit()

            print('partial save...')
            return db_path

        except Exception as e:
            system.log_error(f"Error saving data for setor {setor}: {e}")

    def identify_scrape_targets(self):
        """
        Identifies and returns companies that need new financial data scraping.

        This function loads the NSD list, financial statements, and company information,
        filters out NSD entries already present in financial statements, and merges 
        the remaining NSD entries with company information to identify the scrape targets.

        Returns:
            pd.DataFrame: A DataFrame containing the companies that need new financial data scraping.
        """
        try:
            last_order = 'ZZZZZZZZZZ'
            scrape_order = ['sector', 'subsector', 'segment', 'company_name', 'quarter', 'version']

            # Load the necessary datasets
            nsd_list = self.load_nsd_list()
            financial_statements = self.load_financial_statements()
            company_info = self.load_company_info()

            # Sort datasets according to the predefined order in settings
            nsd_list = nsd_list.sort_values(by=settings.nsd_order, ascending=True)
            financial_statements = financial_statements.sort_values(by=settings.statements_order, ascending=True)

            # Identify NSD entries that are not in financial statements
            new_nsd = nsd_list[~nsd_list['nsd'].isin(financial_statements['nsd'])]
            new_nsd = new_nsd.sort_values(by=settings.nsd_order, ascending=True)

            # Merge filtered NSD data with company information on matching company names
            scrape_targets = pd.merge(new_nsd, company_info, on='company_name', how='inner')

            # Custom sorting to place empty fields last
            scrape_targets['sector'] = scrape_targets['sector'].replace('', last_order)  # Replace empty strings with a placeholder
            scrape_targets['subsector'] = scrape_targets['subsector'].replace('', last_order)
            scrape_targets['segment'] = scrape_targets['segment'].replace('', last_order)

            # Order the list by sector, subsector, segment, company_name, quarter, and version
            scrape_targets = scrape_targets.sort_values(by=scrape_order, ascending=True)

            # Restore empty fields
            scrape_targets['sector'] = scrape_targets['sector'].replace(last_order, '')  # Restore empty fields
            scrape_targets['subsector'] = scrape_targets['subsector'].replace(last_order, '')
            scrape_targets['segment'] = scrape_targets['segment'].replace(last_order, '')


            return scrape_targets

        except Exception as e:
            # Log any errors encountered during the process
            system.log_error(f"Error identifying scrape targets: {e}")

    def process_company_quarter_data(self, row):
        """
        Process financial and capital data for a specific company and quarter.

        Args:
            row (pd.Series): A row of data containing NSD, company name, quarter, sector, and other metadata.

        Returns:
            list: A list of DataFrames with the processed financial and capital data for the company.
        """
        try:
            company_quarter_data = []  # List to store data for the company in the current quarter

            # Extract data from the row
            nsd = row['nsd']
            company_name = row['company_name']
            quarter = pd.to_datetime(row['quarter'], dayfirst=False, errors='coerce').strftime('%Y-%m-%d')
            sector = row['sector']
            subsector = row['subsector']
            segment = row['segment']
            version = row['version']

            # Construct the URL for the NSD entry
            url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"
            self.driver.get(url)

            # Define all statements to be scraped
            statements = settings.financial_data_statements + settings.capital_data_statements

            for cmbGrupo, cmbQuadro in statements:
                # Determine which scraping method to use
                if [cmbGrupo, cmbQuadro] in settings.financial_data_statements:
                    df = self.scrape_financial_data(cmbGrupo, cmbQuadro)
                else:
                    df = self.scrape_capital_data(cmbGrupo, cmbQuadro)

                if df is not None:
                    # Add necessary metadata columns to the DataFrame
                    df = df.assign(
                        nsd=nsd,
                        company_name=company_name,
                        quarter=quarter,
                        version=version,
                        segment=segment,
                        subsector=subsector,
                        sector=sector,
                        type=cmbGrupo,
                        frame=cmbQuadro
                    )
                    # Append the processed DataFrame to the list
                    company_quarter_data.append(df[settings.statements_columns])

            return company_quarter_data

        except Exception as e:
            # Log any errors encountered during processing
            system.log_error(f"Error processing company quarter data: {e}")
            return []  # Return an empty list to prevent the process from stopping

    def run_scraper(self, scrape_targets, batch_number=None):
        """
        Run the entire scraping process for the identified NSD entries, iterating over all financial data statements.
        """
        try:
            # Initialize the overall counter
            counter = 0
            total_items = len(scrape_targets)  # Total number of items across all sectors

            # Process data sector by sector, processing sectors with empty strings last
            for sector, sector_data in scrape_targets.groupby('sector', sort=False):
                all_data = []  # List to store all the processed data
                start_time = time.time()  # Record the start time for the entire process
                sector_size = len(sector_data)  # Total number of rows in the current sector

                for i, row in sector_data.iterrows():
                    try:
                        # Print progress information
                        extra_info = [batch_number, row['nsd'], row['company_name'], pd.to_datetime(row['quarter'], dayfirst=False, errors='coerce').strftime('%Y-%m-%d')]
                        system.print_info(counter, extra_info, start_time, total_items)

                        # Process each company-quarter data using the refactored function
                        company_quarter_data = self.process_company_quarter_data(row)
                        all_data.extend(company_quarter_data)  # Add all processed DataFrames to all_data

                        # Increment the overall counter
                        counter += 1

                        # Save to DB every settings.batch_size iterations or at the end
                        if (total_items - counter - 1) % int(settings.batch_size // settings.max_workers) == 0:
                            if all_data:
                                batch_df = pd.concat(all_data, ignore_index=True)
                                # Reorder columns and sort
                                batch_df = batch_df[settings.statements_columns].sort_values(by=settings.statements_order)
                                db_path = self.save_to_db(batch_df, sector)
                                all_data.clear()  # Clear the list after saving

                    except Exception as e:
                        # Log any errors encountered during processing of individual rows
                        system.log_error(f"Error processing row {i} in sector {sector}: {e}")

                system.db_optimize(db_path)

            system.db_optimize(db_path)

            return scrape_targets

        except Exception as e:
            # Log any errors encountered during the main scraping process
            system.log_error(f"Error in run_scraper: {e}")
            return None  # Return None to indicate that the scraping process did not complete

    def close_scraper(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    try:
        scraper = CapitalDataScraper()
        scraper.run_scraper(group_value='Capital', quadro_value='Quadro Demonstrativo')
    except Exception as e:
        system.log_error(e)
    finally:
        scraper.close_scraper()
