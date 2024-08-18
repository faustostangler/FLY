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

    def load_nsd_data(self):
        """
        Load NSD data from the nsd table in b3.db, filtered by settings.finsheet_types.

        Returns:
        DataFrame: A DataFrame containing the filtered NSD data.
        """
        try:
            db_path = os.path.join(self.db_folder, settings.db_name)  # Full path to b3.db
            query = """
                SELECT *
                FROM nsd
                WHERE nsd_type IN ({})
            """.format(','.join('?' for _ in settings.finsheet_types))

            with sqlite3.connect(db_path) as conn:
                nsd_data = pd.read_sql_query(query, conn, params=settings.finsheet_types)

            return nsd_data.drop_duplicates()
        except Exception as e:
            system.log_error(f"Error loading NSD data: {e}")
            return pd.DataFrame()

    def load_existing_data(self):
        """
        Load existing NSD data from all .db files in the db_folder.

        Returns:
        DataFrame: A DataFrame containing the NSD data from all files.
        """
        try:
            all_dfs = []
            excluded_patterns = ['backup', 'math', ' ']  # List of patterns to exclude from filenames
            db_files = [
                db_file for db_file in glob.glob(f"{self.db_folder}/* .db")
                if not any(pattern in os.path.basename(db_file) for pattern in excluded_patterns)
            ]

            for db_file in db_files:
                with sqlite3.connect(db_file) as conn:
                    df = pd.read_sql_query("SELECT * FROM nsd", conn)
                    all_dfs.append(df)

            if all_dfs:
                return pd.concat(all_dfs, ignore_index=True).drop_duplicates()
            else:
                return pd.DataFrame(columns=settings.nsd_columns)
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

    def scrape_finantial_data(self, cmbGrupo, cmbQuadro):
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

            columns = ['conta', 'descricao', 'valor']
            df1 = df1.iloc[:,0:3]
            df2 = df2.iloc[:,0:3]
            df1.columns = columns
            df2.columns = columns
            df = pd.concat([df1.iloc[:, :2], df2.iloc[:, 2:3]], axis=1)

            col = df.iloc[:, 2].astype(str)
            col = col.str.replace('.', '', regex=False)
            col = col.str.replace(',', '.', regex=False)
            col = pd.to_numeric(col, errors='coerce')
            col = col * thousand
            df.iloc[:, 2] = col

            df = df[~df['conta'].str.startswith(drop_items)]

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

            # Descriptions and accounts
            descriptions = {
                'acoes_on': 'Ações ON Ordinárias',
                'acoes_pn': 'Ações PN Preferenciais',
                'acoes_on_tesouraria': 'Em Tesouraria Ações ON Ordinárias',
                'acoes_pn_tesouraria': 'Em Tesouraria Ações PN Preferenciais'
            }

            accounts = {
                'acoes_on': '00.01.01',
                'acoes_pn': '00.01.02',
                'acoes_on_tesouraria': '00.02.01',
                'acoes_pn_tesouraria': '00.02.02'
            }

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
                'conta': [],
                'descricao': [],
                'valor': []
            }

            acoes_on = self.driver.find_element(By.XPATH, acoes_on_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_pn = self.driver.find_element(By.XPATH, acoes_pn_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_on_tesouraria = self.driver.find_element(By.XPATH, acoes_on_tesouraria_xpath).text.strip().replace('.', '').replace(',', '.')
            acoes_pn_tesouraria = self.driver.find_element(By.XPATH, acoes_pn_tesouraria_xpath).text.strip().replace('.', '').replace(',', '.')

            data['conta'] = [accounts['acoes_on'], accounts['acoes_pn'], accounts['acoes_on_tesouraria'], accounts['acoes_pn_tesouraria']]
            data['descricao'] = [descriptions['acoes_on'], descriptions['acoes_pn'], descriptions['acoes_on_tesouraria'], descriptions['acoes_pn_tesouraria']]
            data['valor'] = [float(acoes_on) * thousand, float(acoes_pn) * thousand, float(acoes_on_tesouraria) * thousand, float(acoes_pn_tesouraria) * thousand]

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
        table_name = 'statements'

        try:
            # Hard-coded configurations
            db_name_base = self.db_name.split('.')[0]  # Extract the base name (e.g., 'b3')
            db_name = f"{db_name_base} {table_name} {setor}"  # Create a database file name specific to the sector
            db_path = os.path.join(self.db_folder, db_name + '.db')
            backup_path = os.path.join(self.db_folder, f"{db_name_base} {table_name} {setor} backup.db")
            
            # SQL command to create the table with a composite primary key
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                nsd INTEGER,
                tipo TEXT,
                setor TEXT,
                subsetor TEXT,
                segmento TEXT,
                company_name TEXT,
                quadro TEXT,
                quarter TEXT,
                conta TEXT,
                descricao TEXT,
                valor REAL,
                version TEXT,
                PRIMARY KEY (company_name, quarter, version, tipo, quadro, conta, descricao)
            )
            """

            # SQL command for INSERT OR REPLACE
            insert_sql = f"""
            INSERT OR REPLACE INTO {table_name} 
            (nsd, tipo, setor, subsetor, segmento, company_name, quadro, quarter, conta, descricao, valor, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Create a backup if the database already exists
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)

            # Connect to the sector-specific database
            with sqlite3.connect(db_path) as conn:
                # Create the table with the composite primary key if it doesn't exist
                conn.execute(create_table_sql)
                conn.commit()

                # Ensure DataFrame columns match the table structure
                df = df[settings.statements_columns]
                
                # Insert data using INSERT OR REPLACE
                for _, row in df.iterrows():
                    conn.execute(insert_sql, tuple(row))

                conn.commit()

            return df

        except Exception as e:
            system.log_error(f"Error saving data for setor {setor}: {e}")

    def filter_new_nsds(self, df_nsd):
        """
        Filter out NSD entries that have already been processed.

        Parameters:
        - df_nsd (DataFrame): The DataFrame of NSD entries to filter.

        Returns:
        DataFrame: A DataFrame containing only new NSD entries.
        """
        try:
            existing_data = self.load_nsd_data()
            return df_nsd[~df_nsd['nsd'].isin(existing_data['nsd'])]
        except Exception as e:
            system.log_error(f"Error filtering new NSD entries: {e}")
            return df_nsd

    def run_scraper(self):
        """
        Run the entire scraping process for the provided NSD entries, iterating over all financial data statements.
        """
        last_order = 'ZZZZZZZZZZ'
        statements_order = ['conta', 'descricao']

        try:
            # Load data
            actual_data = self.load_nsd_data()
            existing_data = self.load_existing_data()
            company_info = self.load_company_info()

            # Filter the data to exclude nsd entries that are already in existing_data
            new_data = actual_data[~actual_data['company'].isin(existing_data['company'])]

            # Merge filtered_nsd_data with company_info on matching company names
            scrape_targets = pd.merge(new_data, company_info, left_on='company', right_on='company_name', how='inner')

            # Custom sorting to place empty fields last
            scrape_targets['setor'] = scrape_targets['setor'].replace('', last_order)  # Replace empty strings with a placeholder
            scrape_targets['subsetor'] = scrape_targets['subsetor'].replace('', last_order)
            scrape_targets['segmento'] = scrape_targets['segmento'].replace('', last_order)

            # Order the list by setor, subsetor, segmento, company, quarter, and version
            scrape_targets = scrape_targets.sort_values(by=['setor', 'subsetor', 'segmento', 'company', 'quarter', 'version'], ascending=True)

            # Restore empty fields
            scrape_targets['setor'] = scrape_targets['setor'].replace(last_order, '')  # Restore empty fields
            scrape_targets['subsetor'] = scrape_targets['subsetor'].replace(last_order, '')
            scrape_targets['segmento'] = scrape_targets['segmento'].replace(last_order, '')

            # Initialize the overall counter
            counter = 0
            total_items = len(scrape_targets)  # Total number of items across all sectors

            # Process data sector by sector, with sectors having empty strings processed last
            for setor, sector_data in scrape_targets.groupby('setor', sort=False):
                all_data = []  # List to store all the processed data
                start_time = time.time()  # Record the start time for the entire process
                sector_size = len(sector_data)  # Total number of rows in the current sector

                for i, row in sector_data.iterrows():
                    company_quarter_data = []  # Clear company_quarter_data for each company

                    nsd = row.iloc[sector_data.columns.get_loc('nsd')]
                    company_name = row.iloc[sector_data.columns.get_loc('company')]
                    quarter = pd.to_datetime(row.iloc[sector_data.columns.get_loc('quarter')], dayfirst=False, errors='coerce').strftime('%Y-%m-%d')
                    setor = row.iloc[sector_data.columns.get_loc('setor')]
                    subsetor = row.iloc[sector_data.columns.get_loc('subsetor')]
                    segmento = row.iloc[sector_data.columns.get_loc('segmento')]
                    version = row.iloc[sector_data.columns.get_loc('version')]

                    url = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"
                    self.driver.get(url)

                    extra_info = [nsd, setor, subsetor, segmento, company_name, quarter]
                    system.print_info(counter, extra_info, start_time, total_items)

                    # Combine financial and capital statements into a single list
                    statements = settings.financial_data_statements + settings.capital_data_statements

                    for cmbGrupo, cmbQuadro in statements:
                        # Decide which scraping function to use based on cmbGrupo and cmbQuadro
                        if [cmbGrupo, cmbQuadro] in settings.financial_data_statements:
                            df = self.scrape_finantial_data(cmbGrupo, cmbQuadro)
                        else:
                            df = self.scrape_capital_data(cmbGrupo, cmbQuadro)

                        if df is not None:
                            # Add metadata columns using assign
                            df = df.assign(
                                nsd=nsd,
                                company_name=company_name,
                                quarter=quarter,
                                version=version,
                                segmento=segmento,
                                subsetor=subsetor,
                                setor=setor,
                                tipo=cmbGrupo,
                                quadro=cmbQuadro
                            )
                            
                            # Reorder the columns if necessary
                            cols = ['nsd', 'company_name', 'quarter', 'version', 'segmento', 'subsetor', 'setor', 'tipo', 'quadro'] + list(df.columns[:-9])
                            df = df[cols]

                            # Append the DataFrame directly to company_quarter_data
                            company_quarter_data.append(df)

                    all_data.extend(company_quarter_data)  # Add all processed DataFrames to all_data

                    # Increment the overall counter
                    counter += 1

                    # Save to DB every settings.batch_size iterations or at the end
                    if (counter) % int(settings.batch_size / 1) == 0 or counter == total_items:
                        if all_data:
                            batch_df = pd.concat(all_data, ignore_index=True)
                            # Reorder columns and sort
                            batch_df = batch_df[settings.statements_columns].sort_values(by=statements_order)
                            batch_df = self.save_to_db(batch_df, setor)
                            all_data.clear()  # Clear the list after saving

            return scrape_targets
        except Exception as e:
            system.log_error(f"Error in run_scraper: {e}")

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
