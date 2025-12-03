import os
import certifi
# Garanta que o REQUESTS use o mesmo bundle de CA do certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE']      = certifi.where()

import base64
import concurrent.futures
import cloudscraper
import inspect
import json
import logging
import platform
import random
import re
import requests
import sqlite3
import string
import subprocess
import threading
import time
import traceback
import warnings
import zipfile
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from urllib.parse import urlparse
import sqlparse
from sqlparse.sql import Identifier, IdentifierList
from sqlparse.tokens import Keyword, DML, Name


import pandas as pd
import psutil
import pyautogui
import requests
import unidecode
import urllib3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from tqdm import tqdm

from utils.config import Config
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import cProfile
import pstats
import functools
from contextlib import contextmanager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

class BaseProcessor:
    def __init__(self):
        self.inspect = inspect
        self.config = Config()  # Assume Config is already defined
        self.db_lock = Lock()  # Initialize a threading Lock

    # APP FLOW LOGIC
    def run(self, data, payload=None, verbose=True, thread=True, module_name=""):
        """Split data into batches and process them sequentially or with
        threads."""
        num_workers = self.config.scraping['max_workers']
        results = []
        try:
            batch_splitters = {
                True: self._split_batches_by_company,
                False: lambda d, n: (self._split_batches(d, n), n),
            }

            splitter = "utils.intel_processor" in module_name
            batches, num_workers = batch_splitters[splitter](data, num_workers)
            items_per_batch = len(batches[0]) if batches else 0

            processors = {
                True: self._process_with_threads,
                False: self._process_sequentially,
            }

            batch_count = len(batches) if thread else num_workers

            if verbose:
                print(
                    f"From {module_name.split('.')[-1]}: processing {data.shape[0]} items in {batch_count} batches of up to {items_per_batch} items each"
                )

            results = processors[thread](batches, payload=payload, verbose=verbose)

        except Exception as e:
            self.log_error(e)

        try:
            processed_batch = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
        except Exception:
            # self.log_error(e)
            try:
                # try to flatten
                flat_results = [df for sublist in results for df in sublist]
                processed_batch = pd.concat(flat_results, ignore_index=True)
            except Exception:
                processed_batch = results

        return processed_batch

    def _split_batches(self, data, batch_size):
        """Split data into batches."""
        batches = []
        try:
            # # split with limit as batch_size
            # batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

            # split with limit as batch count
            batch_size = min(batch_size, len(data))  # Ensure batch_size doesn't exceed data length
            chunk_size = (len(data) + batch_size - 1) // batch_size  # Equivalent to ceil(len(data) / batch_size)
            batches = [data[i * chunk_size : (i + 1) * chunk_size] for i in range(batch_size)]

        except Exception as e:
            self.log_error(e)

        return batches

    def _split_batches_by_company(self, data, num_workers):
        """docstring."""
        batches = []
        try:
            # Get unique company names
            unique_companies = data["company_name"].unique()
            num_companies = len(unique_companies)

            # Handle case where there are fewer companies than workers
            if num_companies < num_workers:
                num_workers = num_companies  # Set number of workers to the number of companies

            # Calculate batch size and remainder
            batch_size = int(num_companies // num_workers)  # Integer division for batch size
            remainder = num_companies % num_workers  # Calculate the remainder

            batches = []
            start = 0

            # Distribute companies across workers
            for i in range(num_workers):
                end = start + batch_size + (1 if i < remainder else 0)  # Add one extra if there's a remainder
                batch_companies = unique_companies[start:end]
                # Filter the original DataFrame for each batch
                batch_data = data[data["company_name"].isin(batch_companies)]
                batches.append(batch_data)
                start = end

        except Exception as e:
            self.log_error(e)

        return batches, num_workers

    def _process_with_threads(self, batches, payload, verbose):
        """Process batches with threading."""
        results = []
        try:
            total_batches = len(batches)
            start_time = time.monotonic()
            total_scrape_size = sum(len(b) for b in batches)
            cumulative = 0  # will keep track of the global start index for each batch
            items_per_batch = len(batches[0])

            with ThreadPoolExecutor(max_workers=self.config.scraping["max_workers"]) as worker_pool_executor:
                futures = []
                for batch_index, batch in enumerate(batches):
                    time.sleep(self.dynamic_sleep() * 5)
                    progress = {
                        "items_per_batch": items_per_batch,
                        "batch_index": batch_index,
                        "total_batches": total_batches,
                        "batch_start": cumulative,  # actual starting index in the overall data,
                        "scrape_size": total_scrape_size,
                        "start_time": start_time,
                        "thread_id": batch_index
                        % self.config.scraping["max_workers"],  # Map batch index to thread pool ID
                    }
                    cumulative += len(batch)  # add the length of this batch for the next iteration

                    # Submit task with progress
                    futures.append(worker_pool_executor.submit(self.process_instance, batch, payload, verbose, progress))

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.log_error(f"Error in thread: {e}")
        except Exception as e:
            self.log_error(e)

        return results

    def _process_sequentially(self, batches, payload, verbose):
        """"""
        results = []
        start_time = time.monotonic()
        total_batches = len(batches)
        total_scrape_size = sum(len(b) for b in batches)
        items_per_batch = len(batches[0])

        for batch_index, batch in enumerate(batches):
            # Prepare progress dictionary
            progress = {
                "items_per_batch": items_per_batch,
                "batch_index": batch_index,
                "total_batches": total_batches,
                "batch_start": batch_index * items_per_batch,  # self.config.scraping["batch_size"],
                "scrape_size": total_scrape_size,
                "start_time": start_time,
                "thread_id": batch_index % self.config.scraping["max_workers"],  # Map batch index to thread pool ID
            }

            try:
                result = self.process_instance(batch, payload, verbose, progress)
                results.append(result)

            except Exception as e:
                self.log_error(f"Error in batch: {e}")

        return results

    @abstractmethod
    def process_instance(self, batch, payload, verbose, progress):
        """To be implemented by child classes."""
        pass

    # WEB & REQUESTS
    def header_random(self):
        """Generate random HTTP headers for requests."""
        try:
            user_agent = random.choice(self.config.requests["user_agents"])
            referer = random.choice(self.config.requests["referers"])
            language = random.choice(self.config.requests["languages"])

            headers = {"User-Agent": user_agent, "Referer": referer, "Accept-Language": language}

            # headers = {
            #     "User-Agent": user_agent,
            #     "Referer": referer,
            #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            #     "Accept-Encoding": "gzip, deflate, br",
            #     "Accept-Language": language,
            #     "Connection": "keep-alive",
            #     "Upgrade-Insecure-Requests": "1",
            #     "DNT": "1",
            #     "Sec-Fetch-Mode": "navigate",
            #     "Sec-Fetch-Site": "none",
            #     "Sec-Fetch-User": "?1",
            #     "Sec-Fetch-Dest": "document",
            # }

        except Exception as e:
            self.log_error(e)

        return headers

    def test_internet(self, wait_time=None, url="https://www.google.com/favicon.ico"):
        """Test internet connection by sending an HTTP GET request to a
        specified URL. Retries if no connection is detected.

        Parameters:
            url (str): The URL to request (default: Google's favicon URL).
        """
        wait_time = wait_time = self.dynamic_sleep() * 10

        while True:
            try:
                # set random headers
                headers = self.header_random()
                session = requests.Session()
                session.headers.update(headers)

                # Make a lightweight GET request
                response = session.get(url, timeout=wait_time)
                if response.status_code == 200:
                    return True  # Connection is successful
            except Exception:
                # Log the error or suppress if preferred
                # print(f"No Internet connection: {e}. Retrying in {wait_time} seconds...")
                pass
            time.sleep(wait_time)  # Wait before retrying

    def detect_dns_block(self, title, driver=False, driver_wait=False, content=False, debug=False, block=False):
        """
        Detecta se uma resposta HTML foi bloqueada pela Cloudflare.
        Funciona com Selenium (driver.page_source) e requests (response.text).
        
        Args:
            title (str): Título para o arquivo de debug.
            driver (WebDriver): Instância do Selenium WebDriver.
            debug (bool): Indica se deve salvar o HTML para debug.

        Returns:
            str or bool: Conteúdo da página ou False se bloqueado.
        """
        try:
            self._simulate_human_interaction(driver)
            if not content:
                content = driver.page_source.lower().strip()

                # Verifica bloqueio tentando encontrar elemento exclusivo do erro 1015
                cloudflare_xpath = "//div[@id='cf-error-details']"
                is_blocked = self.wait_forever(driver_wait, cloudflare_xpath, max_retries=1) is not False
            else:
                block_indicators = [
                    "error 1015",
                    "rate limited",
                    "access denied",
                    "cloudflare",
                    "ray id", 
                ]

                is_blocked = any(term in content for term in block_indicators) or (
                    "<app-root></app-root>" in content and len(content) < 10000
                )

            is_blocked = block if block else is_blocked

            filename = f"{'dns_block_' if is_blocked else ''}{title}.html"

            if debug:
                temp_path = os.path.join(self.config.paths["temp_folder"], filename)
                try:
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    self.log_error(f"Failed to save blocked HTML content: {e}")

            if is_blocked:
                time.sleep(self.config.selenium['wait_time'] * self.dynamic_sleep())
                content = False
        except Exception as e:
            self.log_error(e)

        return content
    class _SSLAdapter(HTTPAdapter):
        def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.poolmanager = PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_context=context,
                **pool_kwargs
            )

    def _create_insecure_scraper(self, headers):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        class InsecureAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                kwargs['ssl_context'] = context
                self.poolmanager = PoolManager(*args, **kwargs)

        session = requests.Session()
        session.mount('https://', InsecureAdapter())
        session.headers.update(headers)

        # Cria o cloudscraper usando a sessão adaptada com o contexto SSL inseguro
        insecure_scraper = cloudscraper.create_scraper(sess=session)
        return insecure_scraper

    def _init_scraper(self, url, wait_time=None):
        """Create a cloudscraper instance with randomized headers and prime it on the homepage."""
        wait_time = wait_time or self.config.selenium['wait_time']
        r = None
        while True:
            try:
                self.test_internet()
                headers = self.header_random()

                # backup
                scraper = requests.Session()
                scraper.headers.update(headers)

                # real one
                scraper = cloudscraper.create_scraper()
                scraper.headers.update(headers)

                # define o caminho do certificado
                scraper.verify = certifi.where()

                # scraper scrape
                r = scraper.get(url, verify=certifi.where())

                if r.status_code == 200:
                    break  # Success! Exit the loop

            except Exception as e:
                self.log_error(e)

            # small sleep to avoid hammering
            wait_time += 1
            time.sleep(self.dynamic_sleep() + wait_time)

        return scraper

    def _fetch_with_retry(self, scraper, url, wait=1):
        """
        Keep calling scraper.get(url) until we get status_code 200,
        tracking block times and using dynamic_sleep() between tries.
        Returns the successful Response.
        """
        domain = urlparse(url).hostname or ""
        insecure_domains = ['bvmf.bmfbovespa.com.br', ]
        block_start = None

        while True:
            try:
                # get url
                if domain in insecure_domains:
                    try:
                        insecure_scraper = self._create_insecure_scraper(scraper.headers)
                        r = insecure_scraper.get(url, headers=scraper.headers, verify=False)
                    except Exception as e:
                        r = requests.get(url, headers=scraper.headers, verify=False)
                else:
                    r = scraper.get(url, verify=certifi.where())  # normal para os demais
                r.raise_for_status()

                # total bytes transferred
                bytes_transferred = len(r.content)
                if self.shared_total_bytes is not None and self.shared_lock is not None:
                    with self.shared_lock:
                        self.shared_total_bytes["total"] += bytes_transferred
                        if self.thread_id is not None:
                            if self.thread_id not in self.shared_total_bytes["threads"]:
                                self.shared_total_bytes["threads"][self.thread_id] = 0
                            self.shared_total_bytes["threads"][self.thread_id] += bytes_transferred
                else:
                    # fallback caso esteja rodando isolado
                    self.total_bytes_transferred += bytes_transferred

                if block_start:
                    self.total_block_time += time.monotonic() - block_start
                    print(f'Dodging server block: {self.total_block_time:.2f}s')
                return r
            except Exception as e:
                if block_start is None:
                    block_start = time.monotonic()
                wait += 1
                time.sleep(self.dynamic_sleep() + wait)
                scraper = self._init_scraper()

    # SELENIUM DRIVER METHODS
    def _get_chrome_version(self):
        """Retrieve the version of Chrome installed on the system.

        Returns:
            str: The Chrome version, or None if not found.
        """
        chrome_error_msg = "Failed to retrieve Chrome version: {e}"

        try:
            for reg_query in self.config.selenium["registry_paths"]:
                try:
                    output = subprocess.check_output(reg_query, shell=True)
                    version = re.search(r"\d+\.\d+\.\d+\.\d+", output.decode("utf-8")).group(0)
                    return version
                except subprocess.CalledProcessError:
                    continue

            try:
                chrome_path = (
                    self.config.selenium["chrome_path_64"]
                    if os.path.exists(self.config.selenium["chrome_path_64"])
                    else self.config.selenium["chrome_path_32"]
                )
                output = subprocess.check_output([chrome_path, "--version"], shell=True)
                version = re.search(r"\d+\.\d+\.\d+\.\d+", output.decode("utf-8")).group(0)
                return version

            except Exception as e:
                self.system.log_error(chrome_error_msg.format(e=e))
                return None
        except Exception as e:
            self.log_error(e)

    def _get_chromedriver_url(self, version):
        """Generate the download URL for ChromeDriver based on the Chrome
        version.

        Args:
            version (str): The Chrome version.

        Returns:
            str: The URL for downloading the corresponding ChromeDriver.
        """
        chromedriver_url_template = (
            f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
        )
        url_error_msg = f"Error obtaining ChromeDriver for version {version}"

        try:
            self.test_internet()
            response = requests.get(chromedriver_url_template)
            if response.status_code == 200:
                return chromedriver_url_template
            else:
                print(url_error_msg)
                return None

        except Exception as e:
            self.log_error(str(e))
            return None

    def _download_and_extract_chromedriver(self, url):
        """Download and extract ChromeDriver from the given URL.

        Args:
            url (str): The URL for downloading ChromeDriver.
            dest_folder (Path): The destination folder for extraction.

        Returns:
            str: The path to the extracted ChromeDriver executable.
        """
        zip_filename = "chromedriver.zip"
        dest_folder = self.config.paths["bin_folder"]
        chromedriver_folder = "chromedriver-win64"
        chromedriver_executable = "chromedriver.exe"
        download_error_msg = "Failed to download or extract ChromeDriver: {e}"

        try:
            self.test_internet()
            response = requests.get(url)
            zip_path = os.path.join(dest_folder, zip_filename)

            with open(zip_path, "wb") as file:
                file.write(response.content)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(dest_folder)

            os.remove(zip_path)
            chromedriver_path = os.path.join(dest_folder, chromedriver_folder, chromedriver_executable)

            return str(chromedriver_path)

        except Exception as e:
            self.log_error(download_error_msg.format(e=e))
            return None

    def _get_chromedriver_path(self):
        """Download and extract the ChromeDriver based on the Chrome version
        installed on the system.

        Returns:
            str: The path to the ChromeDriver executable.
        """
        chrome_version_error_msg = "Unable to determine Chrome version."
        chromedriver_url_error_msg = "Unable to determine the correct ChromeDriver URL."
        path_error_msg = "Failed to obtain ChromeDriver path dynamically."

        try:
            chrome_version = self._get_chrome_version()
            if not chrome_version:
                raise Exception(chrome_version_error_msg)

            chromedriver_url = self._get_chromedriver_url(chrome_version)
            if not chromedriver_url:
                raise Exception(chromedriver_url_error_msg)

            chromedriver_path = self._download_and_extract_chromedriver(chromedriver_url)
            if not chromedriver_path:
                raise Exception(path_error_msg)

            return chromedriver_path

        except Exception as e:
            self.log_error(str(e))
            return None

    def _load_driver(self, chromedriver_path=None):
        """Initialize and return the Selenium WebDriver and WebDriverWait
        instances.

        Args:
            chromedriver_path (str): The path to the ChromeDriver executable.

        Returns:
            tuple: A tuple containing the WebDriver and WebDriverWait instances.
        """
        load_driver_error_msg = "Failed to load driver: {e}"

        chromedriver_path = chromedriver_path or self.config.selenium["chromedriver_path"]

        try:
            # Get random headers using the custom function
            headers = self.header_random()
            width = random.randint(800, 1600)
            height = random.randint(600, 1000)

            chrome_service = Service(executable_path=chromedriver_path)

            chrome_options = Options()

            chrome_options.add_argument(f"--window-size={width},{height}")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--disable-infobars")

            # anti cloudflare
            chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
            chrome_options.add_argument(f"--lang={headers['Accept-Language']}")
            chrome_options.add_argument(f"--referer={headers['Referer']}")

            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            if self.config.selenium.get("proxy_socks5"):
                chrome_options.add_argument(f"--proxy-server=socks5://{self.config.selenium['proxy_socks5']}")

            # chrome_options.add_argument('--headless')

            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            exceptions_ignore = (NoSuchElementException, StaleElementReferenceException)
            driver_wait = WebDriverWait(driver, self.config.selenium["wait_time"], ignored_exceptions=exceptions_ignore)

            return driver, driver_wait

        except Exception as e:
            self.log_error(load_driver_error_msg.format(e=e))
            return None, None

    def _initialize_driver(self):
        """Obtain the Selenium WebDriver and WebDriverWait instances.

        This function either uses a predefined path to ChromeDriver or fetches and loads it dynamically.

        Returns:
            tuple: A tuple containing the WebDriver and WebDriverWait instances.
        """
        # https://googlechromelabs.github.io/chrome-for-testing/#stable
        initialize_driver_error_msg = "Failed to load driver from hardcoded path."
        dynamic_driver_error_msg = "Failed to obtain ChromeDriver path dynamically."

        try:
            driver, driver_wait = self._load_driver()
            if driver is not None:
                return driver, driver_wait
            else:
                raise Exception(initialize_driver_error_msg)

        except Exception:
            try:
                chromedriver_path = self._get_chromedriver_path()
                if not chromedriver_path:
                    raise Exception(dynamic_driver_error_msg)

                driver, driver_wait = self._load_driver(chromedriver_path)
                return driver, driver_wait

            except Exception as dynamic_error:
                self.log_error(str(dynamic_error))
                return None, None

    def _simulate_human_interaction(self, driver):
        """
        Simula interações humanas leves que não exigem foco da janela.
        - Faz scrolls aleatórios.
        - Adiciona pequenas pausas para simular tempo de leitura.
        """
        try:
            # Scroll aleatório para simular navegação
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            max_scroll = max(50, scroll_height // 2)  # Garante valor mínimo razoável

            for _ in range(random.randint(2, 5)):
                scroll = random.randint(10, max_scroll)
                driver.execute_script(f"window.scrollBy(0, {scroll});")
                time.sleep(self.dynamic_sleep())

            # Volta para o topo
            driver.execute_script("window.scrollTo(0, 0);")

            return True

        except Exception as e:
            self.log_error(f"Erro simulando interação humana: {e}")
            return False

    def close_driver(self, driver=None, driver_wait=None):
        """Safely quits the Selenium WebDriver instance."""
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            if driver:
                driver.quit()
        except Exception:
            pass

    # TEXT & SELENIUM OBJECT METHODS
    def clean_text(self, text):
        """Cleans and normalizes the input text by removing punctuation,
        converting to uppercase, removing extra whitespace, and eliminating
        specific words.

        Parameters:
        - text (str): The input text to be cleaned.

        Returns:
        str: The cleaned and normalized text.
        """
        try:
            # Remove punctuation, accents, and normalize case
            translation_table = str.maketrans("", "", string.punctuation)
            if text:
                text = unidecode.unidecode(text)
                text = text.translate(translation_table)
                text = text.upper()
                text = text.strip()
                text = re.sub(r"\s+", " ", text)

                # Regular expression pattern to remove specific words from text
                words_to_remove = "|".join(map(re.escape, self.config.domain["words_to_remove"]))
                pattern = r"\b(?:" + words_to_remove + r")\b"
                text = re.sub(pattern, "", text)

                # Remove extra spaces after word removal
                text = re.sub(r"\s+", " ", text)
                text = text.strip()

        except Exception as e:
            self.log_error(e)

        return text

    def text(self, xpath, driver=None, driver_wait=None):
        """Encontra e recupera o texto de um elemento da web usando o xpath e o
        objeto de espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para recuperar o texto.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        str: O texto do elemento ou uma string vazia se ocorrer uma exceção.
        """
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath)
            return element.text
        except Exception as e:
            self.log_error(e)
            return ""

    def click(self, xpath, driver_wait=None):
        """Encontra e clica em um elemento da web usando o xpath e o objeto de
        espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para clicar.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        bool: True se o elemento foi encontrado e clicado, False caso contrário.
        """
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath)
            if not element:
                return False  # retorna False se o elemento não for encontrado

            # time.sleep(self.dynamic_sleep())
            element.click()
            # time.sleep(self.dynamic_sleep())

            return True
        except Exception as e:
            self.log_error(e)
            return False

    def choose(self, xpath, driver=None, driver_wait=None):
        """Encontra e seleciona um elemento da web usando o xpath e o objeto de
        espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para selecionar.
        - driver (webdriver.Chrome): O objeto driver Chrome a ser usado.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        int: O valor da opção selecionada ou uma string vazia se ocorrer uma exceção.
        """
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath)
            element.click()
            select = Select(driver.find_element(By.XPATH, xpath))
            options = [int(option.text) for option in select.options]
            highest_option = str(max(options))
            select.select_by_value(highest_option)
            return int(highest_option)
        except Exception as e:
            self.log_error(e)
            return ""

    def choose_by_value(self, xpath, value, driver=None, driver_wait=None):
        """Encontra e seleciona um elemento da web usando o xpath e o objeto de
        espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para selecionar.
        - driver (webdriver.Chrome): O objeto driver Chrome a ser usado.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        int: O valor da opção selecionada ou uma string vazia se ocorrer uma exceção.
        """
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath)
            element.click()
            select = Select(driver.find_element(By.XPATH, xpath))
            # options = [option.text for option in select.options]
            select.select_by_value(value)
            self.click("/html/body")
            return value
        except Exception as e:
            self.log_error(e)
            return ""

    def get_options(self, xpath, driver=None, driver_wait=None):
        """Encontra e retorna os elementos da web usando o xpath e o objeto de
        espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para selecionar.
        - driver (webdriver.Chrome): O objeto driver Chrome a ser usado.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        int: O valor da opção selecionada ou uma string vazia se ocorrer uma exceção.
        """
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath, max_retries=1)
            element.click()
            select = Select(driver.find_element(By.XPATH, xpath))
            options = [int(option.text) for option in select.options]
            return options
        except Exception:
            # self.log_error(e)
            return ""

    def select(self, xpath, text, driver=None, driver_wait=None):
        """"""
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait
        select = ""

        try:
            element = self.wait_forever(driver_wait, xpath, max_retries=1)
            select = Select(driver.find_element(By.XPATH, xpath))
            select.select_by_visible_text(text)
        except Exception:
            pass
            # self.log_error(e)
        return select

    def raw_text(self, xpath, driver=None, driver_wait=None):
        """Encontra e recupera o HTML bruto de um elemento da web usando o
        xpath e o objeto de espera fornecido.

        Parameters:
        - xpath (str): O xpath do elemento para recuperar o HTML bruto.
        - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

        Returns:
        str: O HTML bruto do elemento ou uma string vazia se ocorrer uma exceção.
        """
        driver = driver or self.driver
        driver_wait = driver_wait or self.driver_wait

        try:
            element = self.wait_forever(driver_wait, xpath)
            return element.get_attribute("innerHTML")
        except Exception as e:
            self.log_error(e)
            return ""

    def wait_forever(self, driver_wait, xpath, max_retries=None):
        """Espera indefinidamente até que o elemento da web localizado pelo
        xpath seja encontrado.

        Parameters:
        - driver_wait (WebDriverWait): O objeto de espera para usar.
        - xpath (str): O xpath do elemento para esperar.

        Returns:
        WebElement: O elemento da web encontrado.
        """
        attempt = 0
        max_retries = max_retries or self.config.selenium.get("max_retries", 5)
        while True:
            try:
                element = driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return element
            except Exception:
                attempt += 1
                if max_retries and attempt >= max_retries:
                    return False
                self.driver.refresh()
                time.sleep(self.config.selenium["wait_time"])
                # return False

    def subtract_lists(self, list1, list2):
        """
        Subtract elements of list2 from list1.
        Example: ['a', 'b'] - ['b', 'c'] = ['a']

        Parameters
        ----------
        list1 : list
            The list from which elements will be removed.
        list2 : list
            The list of elements to remove from list1.

        Returns
        -------
        list
            A list containing elements from list1 that are not in list2.
        """
        return [item for item in list1 if item not in list2]

    def escape_keywords(self, keywords):
        """Escape special characters in a list of keywords for regex
        operations.

        Parameters
        ----------
        keywords : list
            A list of keywords that may contain special characters.

        Returns
        -------
        list
            A list of escaped keywords ready for regex operations.
        """
        return [re.escape(keyword) for keyword in keywords]

    def map_dataframe_columns(self, df, mapping):
        """
        Map columns of a dataframe to a target schema, adjusting for missing columns.

        Args:
            df (pd.DataFrame): The input dataframe with raw scraped data.
            mapping (dict): A dictionary where keys are source columns and values are target columns.

        Returns:
            pd.DataFrame: DataFrame with columns renamed and completed according to the target schema.
        """
        try:
            # Defensive copy
            df = df.copy()

            # Check if mapping needs to be inverted
            first_col = df.columns[0]
            if first_col not in mapping.keys() and first_col in mapping.values():
                mapping = {v: k for k, v in mapping.items()}

            # Rename the dataframe
            df = df.rename(columns=mapping)

            # Add missing columns as None
            for target_col in mapping.values():
                if target_col not in df.columns:
                    df[target_col] = None

            # Reorder dataframe according to final column order
            df = df[list(mapping.values())]

        except Exception as e:
            self.log_error(e)
            return pd.DataFrame()

        return df

    def _format_bytes(self, bytes_amount):
        if bytes_amount < 1024:
            return f"{bytes_amount:.4f} B"
        elif bytes_amount < 1024 * 1024:
            return f"{bytes_amount / 1024:.2f} KB"
        else:
            return f"{bytes_amount / (1024 * 1024):.2f} MB"

    def get_float_from_text(self, value):
        """
        Automatically detect and parse a number from mixed decimal systems.

        Args:
            value (str or int or float): Input value.

        Returns:
            float: Parsed float value.
        """
        if isinstance(value, (int, float)):
            return float(value)

        value = value.strip().replace('\xa0', '')

        if ',' in value and '.' in value:
            # Both ',' and '.' exist
            if value.rfind(',') > value.rfind('.'):
                # Comma comes after dot => dot = thousand separator
                value = value.replace('.', '').replace(',', '.')
            else:
                # Dot comes after comma => comma = thousand separator
                value = value.replace(',', '')
        elif ',' in value:
            # Only comma present => comma is decimal separator
            value = value.replace('.', '').replace(',', '.')
        elif '.' in value:
            # Only dot present
            parts = value.split('.')
            if len(parts[-1]) <= 2:
                # Last part has 2 or fewer digits: treat as decimal separator
                pass  # Do nothing
            else:
                # Last part has more than 2 digits: treat dot as thousand separator
                value = value.replace('.', '')
        else:
            # No separator
            pass

        return float(value)

    def _clean_number(self, text):
        if text is None:
            return 0
        
        value = text.strip()
        if not value or set(value.replace('\xa0', '').replace('.', '').replace(',', '')) == {'0'}:
            return float(0)
        
        result = self.get_float_from_text(value)
        return result

    def safe_parse_date(self, val):
        if pd.isna(val) or val is None:
            return pd.NaT
        val = str(val).strip()
        if "-" in val and "T" in val:
            # ISO format detected
            return pd.to_datetime(val, errors='coerce', dayfirst=False)
        else:
            # Assume Brazilian format
            return pd.to_datetime(val, errors='coerce', dayfirst=True)

    # APP METHODS
    def prefill_input(self, text, delay=None):
        """Simulate typing the default text into the input field.

        Parameters:
        - text (str): The text to pre-fill in the input.
        - delay (int): The delay before typing starts.
        """
        try:
            if delay == None:
                delay = self.config.selenium["wait_time"]

            time.sleep(self.dynamic_sleep())
            pyautogui.typewrite(text)

        except Exception as e:
            self.log_error(e)

    def timed_input(self, prompt, timeout=None, default="YES"):
        """
        Exibe um prompt e aguarda input do usuário por um tempo limitado.

        Args:
            prompt (str): A mensagem que será exibida ao usuário.
            timeout (int): Tempo máximo em segundos para aguardar a resposta.
            default (str): Valor padrão caso o tempo se esgote.

        Returns:
            str: Resposta do usuário ou valor padrão.
        """
        try:
            timeout = timeout or self.config.selenium["wait_time"]

            result = []

            def ask_input():
                try:
                    result.append(input(prompt))
                except Exception:
                    result.append(default)

            thread = threading.Thread(target=ask_input)
            thread.daemon = True
            thread.start()
            thread.join(timeout)

        except Exception as e:
            self.log_error(e)

        return result[0] if result else default

    def dynamic_sleep(self):
        """
        Dynamically adjusts the sleep time based on the system's CPU usage.

        The function monitors the CPU usage and adjusts the sleep duration as follows:
        - If CPU usage is greater than 80%, the function returns a longer sleep time (suggested 0.5 seconds).
        - If CPU usage is between 50% and 80%, the function returns a moderate sleep time (suggested 0.3 seconds).
        - If CPU usage is below 50%, the function returns a short sleep time (suggested 0.1 seconds).

        Returns:
            float: The sleep duration in seconds, based on current CPU usage.
        """

        wait = self.config.selenium["wait_time"]

        # Get the current CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)  # Get CPU usage over 0.1 second

        # Adjust sleep time based on CPU usage
        if cpu_usage > 80:
            return wait * random.uniform(0.3, 1.5)  # Increase delay if CPU usage is high
        elif cpu_usage > 50:
            return wait * random.uniform(0.2, 1.0)  # delay if CPU usage is medium load
        else:
            return wait * random.uniform(0.1, 0.5)  # delay if CPU usage is medium low

    def detect_and_correct_outliers_old(self, df):
        """
        definitions
        """
        try:
            # Define primary key columns
            statements_sheet_columns = self.config.domain["statements_sheet_columns"]

            # Initiate variables
            group_cols = ["company_name", "type", "account"]
            value_col = "value"
            date_col = "quarter"
            neighbor_count = 5  # Quantidade de vizinhos a considerar para média

            df_sorted = df.sort_values(by=group_cols + [date_col]).reset_index(drop=True)
            df_sorted["original_value"] = df_sorted[value_col]  # Preserva o valor original

            def process_group(group):
                group = group.copy()  # Evita modificar os dados originais

                # Remove duplicates by keeping the row with the highest value (ignoring 0)
                group = group.loc[group.groupby(statements_sheet_columns)["value"].idxmax()].reset_index(drop=True)

                for idx in range(len(group)):
                    try:
                        # Get Value
                        value = group.iloc[idx][value_col]

                        # Seleciona vizinhos
                        prev_values = group.iloc[max(0, idx - neighbor_count) : idx][value_col].tolist()
                        next_values = group.iloc[idx + 1 : idx + 1 + neighbor_count][value_col].tolist()

                        if not prev_values or not next_values:
                            continue  # Se não há vizinhos suficientes, pula a verificação

                        # Loop regressivo de neighbor_count até 1
                        for n in range(neighbor_count, 0, -1):
                            prev_values_n = prev_values[-n:]  # Considera últimos n valores anteriores
                            next_values_n = next_values[:n]  # Considera primeiros n valores posteriores

                            if prev_values_n and next_values_n:
                                mean_prev = sum(prev_values_n) / len(prev_values_n)
                                mean_next = sum(next_values_n) / len(next_values_n)

                                # Se a média for 1000x maior ou menor e for diferente de 0, aplica a correção
                                if (mean_prev == value * 1000 or mean_prev == value / 1000) and mean_prev != 0:
                                    group.iloc[idx, group.columns.get_loc(value_col)] = mean_prev
                                    break  # Sai do loop ao encontrar um valor válido

                                elif (mean_next == value * 1000 or mean_next == value / 1000) and mean_next != 0:
                                    group.iloc[idx, group.columns.get_loc(value_col)] = mean_next
                                    break  # Sai do loop ao encontrar um valor válido

                    except Exception as e:
                        self.log_error(e)

                return group

            corrected_df = df_sorted.groupby(group_cols, group_keys=False).apply(process_group).reset_index(drop=True)

        except Exception as e:
            self.log_error(e)

        return corrected_df

    def detect_and_correct_outliers(self, df):
        """
        Detect and correct outliers for a specific company.
        Retrieves raw statements for the company, applies outlier detection and correction, and saves the cleaned data.
        """
        try:
            # Determine the company to process
            company_name = df['company_name'].iloc[0]

            # Run raw statements for this company from the database
            raw_df = self.load_data(
                query=f"SELECT * FROM {self.tbl_statements_raw} WHERE company_name = ?",
                params=(company_name,),
                db_filepath=self.db_filepath,
                alert=False
            )
            if raw_df.empty:
                return df

            # Define outlier detection parameters
            group_cols = ["company_name", "type", "account"]
            value_col = "value"
            date_col = "quarter"
            neighbor_count = 5  # Number of neighboring periods to consider

            # Sort and preserve original values
            raw_df_sorted = raw_df.sort_values(by=group_cols + [date_col]).reset_index(drop=True)
            raw_df_sorted["original_value"] = raw_df_sorted[value_col]

            # Function to verify and correct outliers in a group
            def process_group(group):
                group = group.copy()
                # Remove duplicates: keep highest non-zero
                group = group.loc[group.groupby(self.primary_key_columns)[value_col].idxmax()].reset_index(drop=True)

                for idx in range(len(group)):
                    val = group.at[idx, value_col]
                    # Gather previous and next neighbor values
                    prev_vals = group.iloc[max(0, idx - neighbor_count):idx][value_col].tolist()
                    next_vals = group.iloc[idx + 1: idx + 1 + neighbor_count][value_col].tolist()
                    if not prev_vals or not next_vals:
                        continue
                    # Check progressively smaller windows
                    for n in range(neighbor_count, 0, -1):
                        pv = prev_vals[-n:]
                        nv = next_vals[:n]
                        if pv and nv:
                            mean_prev = sum(pv) / len(pv)
                            mean_next = sum(nv) / len(nv)
                            # If the value is off by a factor of 1000
                            if mean_prev != 0 and (mean_prev == val * 1000 or mean_prev == val / 1000):
                                group.at[idx, value_col] = mean_prev
                                break
                            if mean_next != 0 and (mean_next == val * 1000 or mean_next == val / 1000):
                                group.at[idx, value_col] = mean_next
                                break
                return group

            # Apply outlier processing per group
            corrected_df = (
                raw_df_sorted
                .groupby(group_cols, group_keys=False)
                .apply(process_group)
                .reset_index(drop=True)
            )

            # Persist corrected data to the normalized statements table
            self.save_to_db(
                dataframe=corrected_df,
                table_name=self.tbl_statements_normalized,
                db_filepath=self.db_filepath,
                alert=False,
                update=False
            )

            return corrected_df

        except Exception as e:
            self.log_error(e)
            return pd.DataFrame()

    def base64_payload(self, payload: dict) -> str:
        """
        Gera um token Base64 com os parâmetros corretos para o endpoint da B3.

        Args:
            payload (dict): Dicionário com parâmetros como language, pageNumber, etc.

        Returns:
            str: String Base64 pronta para ser usada na URL.
        """
        try:
            json_str = json.dumps(payload, separators=(',', ':'))
            base64_encoded = base64.b64encode(json_str.encode()).decode()

        except Exception as e:
            self.log_error(e)

        return base64_encoded

    def base64_decode(self, token_base64: str) -> dict:
        """
        Decodifica um payload Base64 da B3 e retorna como dicionário JSON.

        Args:
            token_base64 (str): Token codificado (ex: 'eyJsYW5ndWFnZSI6InB0LWJyIn0=')

        Returns:
            dict: Dicionário com os dados decodificados
        """
        if token_base64.startswith("https"):
            token_base64 = token_base64.rstrip("/").split("/")[-1]

        try:
            decoded_bytes = base64.b64decode(token_base64)
            decoded_str = decoded_bytes.decode()
            json_str = json.loads(decoded_str)
            return json_str

        except Exception as e:
            self.log_error(e)
            return {}

    # BENCHMARK, LOG & DEBUG METHODS
    def benchmark_function(self, function, *args, benchmark_mode=False, workers_list=None, **kwargs):
        """Generic benchmarking method to evaluate resource usage with
        different worker counts.

        Parameters:
        - function: The function to benchmark (e.g., process_batch).
        - *args: Positional arguments for the function.
        - benchmark_mode (bool): If True, runs the benchmark; otherwise, just calls the function normally.
        - workers_list (list, optional): List of worker counts to test. Defaults to [1, half CPU, full CPU, double CPU].
        - **kwargs: Keyword arguments for the function.

        Returns:
        - original_result: The actual result from the function being benchmarked.
        - benchmark_results: A list of tuples containing (workers, time_taken, memory_used, cpu_usage).
        """
        try:
            if not benchmark_mode:
                # Just run the function normally without benchmarking

                result = function(*args, **kwargs), []

                return result

            if workers_list is None:
                workers_list = [1, max(2, os.cpu_count() // 2), os.cpu_count(), os.cpu_count() * 2]

            print(f"\nRunning benchmark for {inspect.getmodule(function).__name__}.{function.__name__}")

            benchmark_results = []
            original_result = None  # Store the result of the first execution

            for i, workers in enumerate(workers_list):
                print(f"{self.config.domain['indent']}starting benchmark {i + 1} of {len(workers_list)}")
                start_time = time.monotonic()
                process = psutil.Process()
                initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as worker_pool_executor:
                    future = worker_pool_executor.submit(function, *args, **kwargs)
                    result = future.result()

                end_time = time.monotonic()
                elapsed_time = end_time - start_time
                final_memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_used = final_memory - initial_memory
                cpu_usage = process.cpu_percent(interval=0.5)

                # Store the benchmark data
                benchmark_results.append((workers, elapsed_time, memory_used, cpu_usage))

                print(f"\n🔹 Workers: {workers}")
                print(f"⏳ Time Taken: {elapsed_time:.2f} sec")
                print(f"📈 Memory Used: {memory_used:.2f} MB")
                print(f"⚡ CPU Usage: {cpu_usage:.2f}%\n")

                # Store the original function's result (only from the first execution)
                if original_result is None:
                    original_result = result
        except Exception as e:
            self.log_error(e)
            original_result, benchmark_results = [], []

        return (original_result, benchmark_results)  # Return both the function result and benchmark data

    def log_error(self, error):
        """Logs an error to a file with detailed context, including caller
        info, module, function, line number, timestamp, and system
        information."""
        try:
            # Get the current frame and the caller frame
            current_frame = inspect.currentframe()
            caller_frame = current_frame.f_back

            # Gather detailed context information
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            function_name = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno
            module_name = caller_frame.f_globals["__name__"]
            system_info = platform.platform()
            caller_name = caller_frame.f_globals["__name__"]

            # Get traceback as string
            full_traceback = traceback.format_exc()

            # Configure logging settings
            logging.basicConfig(
                filename="app_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
            )

            # Detailed log message without stack trace
            log_message = (
                f"Timestamp: {timestamp}\n"
                f"Error in module '{module_name}', function '{function_name}', line {line_number}\n"
                f"Caller: {caller_name}\n"
                f"Error: {error}\n"
                f"System Info: {system_info}\n"
                f"Traceback:\n{full_traceback}"
            )

            # Log the error message to the file
            logging.error(log_message)

            # Print a simplified error message to the console
            print(f"Error in {function_name} (line {line_number}): {error}")

        except Exception as e:
            print(e)

        return error

    def print_info(self, index=0, size=1, start_time=time.monotonic(), extra_info=[], indent_level=0):
        """Prints the provided information along with the progress, elapsed
        time, estimated remaining time, and total estimated time."""
        try:
            completed_items = index + 1
            remaining_items = size - completed_items
            percentage_completed = completed_items / size

            elapsed_time = time.monotonic() - start_time
            avg_time_per_item = elapsed_time / completed_items
            remaining_time = remaining_items * avg_time_per_item
            total_estimated_time = elapsed_time + remaining_time

            # Format elapsed time
            elapsed_hours, elapsed_remainder = divmod(int(elapsed_time), 3600)
            elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
            elapsed_time_formatted = f"{int(elapsed_hours)}h {int(elapsed_minutes):02}m {int(elapsed_seconds):02}s"

            # Format remaining time
            remaining_hours, remaining_remainder = divmod(int(remaining_time), 3600)
            remaining_minutes, remaining_seconds = divmod(remaining_remainder, 60)
            remaining_time_formatted = (
                f"{int(remaining_hours)}h {int(remaining_minutes):02}m {int(remaining_seconds):02}s"
            )

            # Format total estimated time
            total_hours, total_remainder = divmod(int(total_estimated_time), 3600)
            total_minutes, total_seconds = divmod(total_remainder, 60)
            total_time_formatted = f"{int(total_hours)}h {int(total_minutes):02}m {int(total_seconds):02}s"

            # Prepare progress string
            progress = (
                f"{percentage_completed:.2%} ({completed_items}+{remaining_items}), "
                f"{avg_time_per_item:.4f}s per item, "
                f"{total_time_formatted} = {elapsed_time_formatted} + {remaining_time_formatted}"
            )

            # Add indentation
            indent = self.config.domain["indent"] * (indent_level + 1)
            extra_info_str = " ".join(map(str, extra_info))
            print(f"{indent}{progress} {extra_info_str}")

        except Exception as e:
            self.log_error(e)
            pass

    def winbeep(frequency=5000, duration=50):
        """Generates a system beep sound with the specified frequency and
        duration.

        Parameters:
        - frequency (int): The frequency of the beep sound in Hertz (default is 5000 Hz).
        - duration (int): The duration of the beep sound in milliseconds (default is 50 ms).

        Returns:
        bool: True if the beep was successful, False otherwise.
        """
        # winsound.Beep(frequency, duration)
        return True

    def profile_generator(self):
        """
        Decorator para perfilar métodos da instância.
        Salva um snapshot .prof após a execução do método.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                profiler = cProfile.Profile()
                profiler.enable()

                result = func(*args, **kwargs)

                profiler.disable()
                filename_prefix = "profile"
                module_name = os.path.basename(func.__module__.replace(".", "/"))
                timestamp = datetime.now().strftime("%Y-%m-%d %H%M %S")
                filename = os.path.join(
                    self.config.paths["profiles_folder"], 
                    f"{filename_prefix} {module_name}_{func.__name__} {timestamp}.prof"
                )
                try:
                    profiler.create_stats()
                    with open(filename, "w") as f:
                        stats = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
                        stats.dump_stats(filename)
                except Exception as e:
                    self.log_error(e)
                return result
            return wrapper
        return decorator

    @contextmanager
    def profiling(self, label="manual"):
        """
        Context manager para perfilar um trecho de código e salvar snapshot automaticamente.
        """
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            yield
        finally:
            profiler.disable()
            self.dump_profiler_snapshot(profiler)

    def dump_profiler_snapshot(self, profiler):
        """
        Salva um snapshot parcial do profiler no formato .prof.
        Pode ser chamada de dentro de qualquer método.
        """
        try:
            profiler.create_stats()
            filename_prefix = "profile_manual"

            # Procurar o primeiro frame fora de BaseProcessor e libs internas
            for frame_info in inspect.stack():
                module_name = frame_info.frame.f_globals.get("__name__", "")
                if (
                    not module_name.startswith("contextlib")
                    and not module_name.endswith("base_processor")
                    and "site-packages" not in frame_info.filename
                ):
                    func_name = frame_info.function
                    module_name_clean = module_name.split(".")[-1]
                    break
            else:
                func_name = "unknown"
                module_name_clean = "unknown"

            timestamp = datetime.now().strftime("%Y-%m-%d %H%M %S")
            filename = os.path.join(
                self.config.paths["profiles_folder"], 
                f"{filename_prefix} {module_name_clean}_{func_name} {timestamp}.prof"
            )

            with open(filename, "w") as f:
                stats = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
                stats.dump_stats(filename)
        except Exception as e:
            self.log_error(e)

    # DATABASE METHODS
    def _initialize_database(self, db_filepath, database_name, table_name=None):
        """Ensure the database and table exist, creating them if necessary."""
        try:
            if not os.path.exists(db_filepath):
                # print(f"Database '{database_name}' does not exist. Creating...")
                with self._get_db_connection(db_filepath, read_only=False) as conn:
                    # Create the database file if it doesn't exist
                    conn.execute("PRAGMA temp_store=MEMORY;")
                    conn.execute("PRAGMA locking_mode=NORMAL;")
                    conn.execute("PRAGMA journal_mode=WAL;")
                    conn.execute("PRAGMA synchronous=NORMAL;")
                    conn.execute("PRAGMA cache_size = -20000;")

                if table_name:
                    self._initialize_table(db_filepath, database_name, table_name)
        except Exception as e:
            self.log_error(e)

        return True

    def _initialize_table(self, db_filepath, database_name, table_name):
        """Ensure the specified table exists, creating it if necessary."""
        try:
            schema_definitions = self.config.schemas[database_name]
            for schema_table_name, schema_sql in schema_definitions.items():
                # Handle dynamic table names for sectors
                if schema_table_name in table_name or schema_table_name == table_name:
                    with self._get_db_connection(db_filepath, read_only=False) as conn:
                        cursor = conn.cursor()
                        try:
                            [cursor.execute(statement.strip()) for statement in schema_sql.split(";") if statement.strip()]
                        except:
                            cursor.executescript(schema_sql)
                        conn.commit()
                        # print(f"Table '{table_name}' initialized in '{database_name}'.")
                    return
            # print(f"Warning: No schema defined for table '{table_name}' in database '{database_name}'.")
        except Exception as e:
            self.log_error(e)

        return True

    def _configure_db(self, db_filepath):
        """Set persistent PRAGMA settings for the database."""
        try:
            with sqlite3.connect(db_filepath) as conn:
                conn.execute("PRAGMA temp_store=MEMORY;")
                conn.execute("PRAGMA locking_mode=NORMAL;")
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA cache_size = -20000;")
            # print("Database configured successfully.")
        except Exception as e:
            self.log_error(e)

        return conn

    def _get_db_connection(self, db_filepath, read_only=True):
        """Return a new database connection with session-specific PRAGMA settings.

        Parameters:
        - db_filepath (str): Path to the database file.
        - read_only (bool): Whether to open the database in read-only mode (default is False).

        Returns:
        - conn (sqlite3.Connection): A SQLite connection object if successful, else None.
        """
        try:
            # Determine the connection mode based on the read_only flag
            if read_only:
                # Open in read-only mode using URI format
                uri = f"file:{db_filepath}?mode=ro"
            else:
                # Normal read-write mode
                uri = f"file:{db_filepath}"

            # Attempt to establish a connection with the database
            conn = sqlite3.connect(uri, uri=True, check_same_thread=False)

            # Return the connection if successful
            return conn

        except sqlite3.Error as e:
            # Log the error if the connection fails
            self.log_error(f"SQLite connection error: {e}")
            return None

    def prepare_db_conn(self, db):
        """description."""
        try:
            conn = ""
        except Exception as e:
            self.log_error(e)

        return conn

    def auto_map_columns(self, df, column_map):
        """
        Converte os nomes das colunas de um DataFrame de local → web ou web → local,
        baseado nas colunas detectadas no DataFrame.

        Parâmetros:
        - df: pd.DataFrame
        - column_map: dict — mapeamento local → web

        Retorno:
        - DataFrame com colunas renomeadas (ou original, se irrelevante)
        """
        df_cols = set(column_map.keys())
        df_reverse = set(column_map.values())
        current_cols = set(df.columns)

        if df_cols & current_cols:
            # Se contém colunas
            rename_map = column_map
        elif df_reverse & current_cols:
            # Se o mapa está invertido
            rename_map = {v: k for k, v in column_map.items()}
        else:
            # Nenhuma coluna relevante encontrada
            return df

        return df.rename(columns=rename_map)

    def _add_columns_if_not_exist(self, db_filepath, table_name, column_names):
        """Adds multiple columns to the table if they do not already exist.

        Args:
            db_path (str): Path to the SQLite database.
            table_name (str): Name of the table to modify.
            column_names (list): List of column names to add.
        """
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        # Retrieve existing column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}  # Use a set for faster lookups

        # Prepare ALTER TABLE statements only for missing columns
        alter_statements = [
            f"ALTER TABLE {table_name} ADD COLUMN '{column}' REAL"
            for column in column_names
            if column not in existing_columns
        ]

        # Execute all ALTER TABLE commands in a single transaction
        if alter_statements:
            for statement in alter_statements:
                cursor.execute(statement)
            conn.commit()

        conn.close()

    def _count_records(self, db_filepath, table_name, query, params):
        """Counts total records in the specified table or query."""
        try:
            with sqlite3.connect(db_filepath) as conn:
                cursor = conn.cursor()
                try:
                    if query:
                        sql_query = query if not params else f"SELECT COUNT(*) FROM ({query})"
                        (cursor.execute(sql_query, params) if params else cursor.execute(sql_query))
                    elif table_name:
                        if params:
                            sql_query = f"SELECT COUNT(*) FROM {table_name} WHERE ticker_code = ?"
                            cursor.execute(sql_query, params)
                        else:
                            sql_query = f"SELECT COUNT(*) FROM {table_name}"
                            cursor.execute(sql_query)
                    total_rows = cursor.fetchone()[0]

                except Exception:
                    total_rows = 0

                return total_rows

        except Exception as e:
            self.log_error(e)

    def _load_data_batches(self, db_filepath, table_name, query, params, total_rows, normalize_columns, alert):
        """Loads data in batches using multi-threading."""
        try:
            batch_size = self.config.scraping["chunk_size"]
            batch_number = (total_rows // batch_size) + 1
            batch_threads = min(self.config.scraping["max_workers"], batch_number)
            offsets = range(0, total_rows, batch_size)

            start_time = time.monotonic()
            with ThreadPoolExecutor(max_workers=batch_threads) as worker_pool_executor:
                tasks = [
                    worker_pool_executor.submit(
                        self._read_batch,
                        db_filepath,
                        table_name,
                        query,
                        params,
                        offset,
                        batch_size,
                        batch_num,
                        total_rows,
                        start_time,
                        alert,
                    )
                    for batch_num, offset in enumerate(offsets)
                ]
                dataframes = [task.result() for task in tasks]

            final_df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

            if normalize_columns:
                final_df = self._normalize_columns(final_df, normalize_columns)

        except Exception as e:
            final_df = pd.DataFrame()
            self.log_error(e)

        return final_df

    def _read_batch(
        self, db_filepath, table_name, query, params, offset, batch_size, batch_num, total_rows, start_time, alert
    ):
        """Reads a single batch of data."""
        try:
            if alert:
                extra_info = [f"Batch {batch_num + 1}/{(total_rows // batch_size) + 1}"]
                self.print_info(batch_num, (total_rows // batch_size) + 1, start_time, extra_info)

            attempts = 0
            max_retries = self.config.selenium["max_retries"]
            while attempts < max_retries:
                try:
                    with sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True) as conn:
                        try:
                            sql_query = self._construct_query(table_name, query, params, batch_size, offset)
                            df = pd.read_sql_query(sql_query, conn, params=params)
                        except Exception as e:
                            self.log_error(e)
                        return df
                except Exception as e:
                    if "database is locked" in str(e):
                        attempts += 1
                        time.sleep(self.dynamic_sleep())
                    else:
                        raise
            raise Exception(f"Failed to read batch after {max_retries} attempts.")

        except Exception as e:
            self.log_error(e)

    def _extract_table_names(self, sql):
        """
        Extrai todos os nomes de tabelas de um SQL, incluindo subqueries e joins compostos.
        """
        result = []
        try:
            table_names = set()
            parsed = sqlparse.parse(sql)

            def extract_from_tokens(tokens):
                try:
                    idx = 0
                    while idx < len(tokens):
                        token = tokens[idx]

                        if token.is_group:
                            extract_from_tokens(token.tokens)

                        elif token.ttype is Keyword:
                            value = token.value.upper()
                            if value in ("FROM", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "OUTER JOIN", "UPDATE", "INTO"):
                                # Pega o próximo token relevante
                                idx += 1
                                while idx < len(tokens):
                                    next_token = tokens[idx]
                                    if next_token.ttype in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline, sqlparse.tokens.Punctuation):
                                        idx += 1
                                        continue
                                    if isinstance(next_token, IdentifierList):
                                        for identifier in next_token.get_identifiers():
                                            name = identifier.get_real_name()
                                            if name:
                                                table_names.add(name)
                                    elif isinstance(next_token, Identifier):
                                        name = next_token.get_real_name()
                                        if name:
                                            table_names.add(name)
                                    elif next_token.ttype is Name:
                                        table_names.add(next_token.value)
                                    break
                        idx += 1
                except Exception as e:
                    self.log_error(f"Erro interno ao percorrer tokens: {e}")

            for statement in parsed:
                extract_from_tokens(statement.tokens)

            result = list(table_names)

        except Exception as e:
            self.log_error(f"Erro ao extrair nomes de tabelas: {e}")

        return result

    def load_data(
        self,
        table_name: str | None = None,
        query: str | None = None,
        params: tuple | None = None,
        db_filepath: str | None = None,
        *,
        multi_thread: bool = True,  # <<< nova flag
        max_retries: int | None = None,
        alert: bool = True,
    ):
        """
        Carrega dados de um banco SQLite em DataFrame – com ou sem multithread,
        e com paginação adaptativa (por rowid ou ROW_NUMBER).

        - Se `table_name` for passado, pagina usando rowid.
        - Se `query` for passado, encapsula em CTE, numera com ROW_NUMBER()
        - Se `multi_thread=False`, lê os batches sequencialmente.
        """
        try:
            params        = params or ()
            max_retries   = max_retries or self.config.selenium["max_retries"]
            db_filepath   = db_filepath or self.config.databases["raw"]["filepath"]
            database_name = os.path.basename(db_filepath)
            dataframes    = []

            # ---------- Inicialização de banco e tabela ----------
            with self.db_lock:
                self._initialize_database(db_filepath, database_name, table_name)
                self._configure_db(db_filepath)
                if table_name:
                    table_names = [table_name]
                else:
                    table_names = self._extract_table_names(query)
                for table_name in table_names:
                    if table_name:
                        with self._get_db_connection(db_filepath, read_only=False) as conn:
                            cur = conn.cursor()
                            cur.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                                (table_name,),
                            )
                            if cur.fetchone() is None:
                                self._initialize_table(db_filepath, database_name, table_name)

            # ---------- 1. Contar linhas ----------
            total_rows = 0
            attempts   = 0
            while attempts < max_retries:
                try:
                    with self._get_db_connection(db_filepath, read_only=True) as conn:
                        cur = conn.cursor()
                        if query:
                            base_query = query.strip().rstrip(";")
                            query_sub = f"SELECT COUNT(*) FROM ({base_query}) AS sub"
                            cur.execute(query_sub, params)
                            total_rows = cur.fetchone()[0]
                        elif table_name:
                            cur.execute(f"SELECT MAX(rowid) FROM {table_name}")
                            max_rowid = cur.fetchone()[0]
                            total_rows = max_rowid or 0
                        break
                except Exception as e:
                    self.log_error(e)
                    attempts += 1
                    time.sleep(self.dynamic_sleep())

            if total_rows == 0:
                return pd.DataFrame()

            # ---------- 2. Definir batches ----------
            batch_size    = self.config.scraping["chunk_size"]
            batch_number  = (total_rows // batch_size) + (1 if total_rows % batch_size else 0)
            batch_threads = min(self.config.scraping["max_workers"], batch_number)
            start_time    = time.monotonic()

            if table_name:
                rowid_starts = [i * batch_size + 1 for i in range(batch_number)]
                rowid_ends   = [s + batch_size for s in rowid_starts]
                rowid_ends[-1] = rowid_starts[-1] + batch_size
            else:
                pass  # ROW_NUMBER() paginará dinamicamente

            # ---------- 3. Função para ler lote ----------
            def read_batch(idx: int):
                attempt = 0
                while attempt < max_retries:
                    try:
                        with self._get_db_connection(db_filepath, read_only=True) as conn:
                            if query:
                                start_row = idx * batch_size + 1
                                end_row   = min(start_row + batch_size - 1, total_rows)
                                base_q    = query.strip().rstrip(";")
                                sql = f"""
                                WITH filtered AS (
                                    {base_q}
                                ),
                                numbered AS (
                                    SELECT filtered.*, ROW_NUMBER() OVER () AS rownum
                                    FROM filtered
                                )
                                SELECT * FROM numbered
                                WHERE rownum BETWEEN {start_row} AND {end_row};
                                """
                                df = pd.read_sql_query(sql, conn, params=params)
                            elif table_name:
                                start_id = rowid_starts[idx]
                                end_id   = rowid_ends[idx]
                                sql = (
                                    f"SELECT * FROM {table_name} "
                                    f"WHERE rowid >= {start_id} AND rowid < {end_id}"
                                )
                                df = pd.read_sql_query(sql, conn)
                            return df
                    except Exception as e:
                        if "database is locked" in str(e):
                            attempt += 1
                            time.sleep(self.dynamic_sleep())
                        else:
                            raise
                raise RuntimeError(f"Falha após {max_retries} tentativas no batch {idx}")

            # ---------- 4. Execução dos batches ----------
            if multi_thread:
                # Modo original com ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=batch_threads) as worker_pool_executor:
                    futures = [worker_pool_executor.submit(read_batch, i) for i in range(batch_number)]
                    with tqdm(total=total_rows, unit=" rows", desc=str(table_name or 'query'), leave=False) as pbar:
                        for fut in as_completed(futures):
                            part = fut.result()
                            dataframes.append(part)
                            pbar.update(len(part))
            else:
                # Novo modo sequencial
                with tqdm(total=total_rows, unit=" rows", desc=str(table_name or 'query'), leave=False) as pbar:
                    for i in range(batch_number):
                        part = read_batch(i)
                        dataframes.append(part)
                        pbar.update(len(part))

            return pd.concat(dataframes, ignore_index=True)

        except Exception as e:
            self.log_error(e)

            # ---------- fallback simples: OFFSET/LIMIT sequencial ----------
            try:
                batch_size   = self.config.scraping["chunk_size"]
                offset       = 0
                dfs_fallback = []

                with self._get_db_connection(db_filepath, read_only=True) as conn:
                    while True:
                        if table_name:
                            sql_fb = f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
                            df_part = pd.read_sql_query(sql_fb, conn)
                        else:
                            sql_fb = f"{query.strip().rstrip(';')} LIMIT {batch_size} OFFSET {offset}"
                            df_part = pd.read_sql_query(sql_fb, conn, params=params)

                        if df_part.empty:
                            break
                        dfs_fallback.append(df_part)
                        offset += batch_size

                return pd.concat(dfs_fallback, ignore_index=True) if dfs_fallback else pd.DataFrame()

            except Exception as ex2:
                self.log_error(ex2)
                return pd.DataFrame()

    def save_to_db(
        self,
        dataframe,
        table_name=None,
        db_filepath=None,
        alert=True,
        max_retries=None,
        update=True,
        sql_update=None,
        sql_update_params=None,
    ):
        """
        Save or update a DataFrame in a SQLite database table.

        Args:
            dataframe (DataFrame): The DataFrame containing data to insert or update.
            table_name (str): The name of the database table.
            db_filepath (str): The SQLite database file path.
            alert (bool): Whether to print update messages.
            max_retries (int): Maximum retry attempts if the database is locked.
            update (bool): Whether to update existing rows on conflict.
            sql_update (str, optional): SQL command to execute instead of inserting data.
            sql_update_params (tuple, optional): Parameters for the `sql_update` statement.
        """
        try:
            db_filepath = db_filepath or self.config.db_filepath
            database_name = os.path.basename(db_filepath)
            max_retries = max_retries or self.config.selenium["max_retries"]
            columns, dtypes, primary_keys = self._get_table_structure(table_name, database_name)

            # Conexão inicial para verificar/criar tabela
            with self._get_db_connection(db_filepath, read_only=False) as conn:
                cursor = conn.cursor()

                # Verifica se a tabela existe
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                    (table_name,)
                )
                table_exists = cursor.fetchone() is not None

                if not table_exists:
                    try:
                        # Cria a tabela a partir do schema salvo (se existir)
                        schema = self.config.schemas[database_name][table_name]
                        cursor.executescript(schema)
                        conn.commit()
                    except KeyError:
                        # Se não houver schema, cria a partir do DataFrame
                        columns = list(dataframe.columns)
                        dtypes = {
                            col: self._map_pd_to_sql_dtype(dataframe[col].dtype)
                            for col in columns
                        }
                        col_defs = [
                            f'"{col}" {dtypes.get(col, "TEXT")}' for col in columns
                        ]
                        create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)});"
                        cursor.execute(create_sql)
                        conn.commit()

            # Se for inserção, prepara dados e SQL
            if not sql_update:
                dataframe = self._prepare_dataframe(dataframe)
                data_tuples = [tuple(row) for row in dataframe.itertuples(index=False)]
                sql = self._get_sql_statement(dataframe, primary_keys, table_name, update=update)

            # Segunda conexão protegida por lock para executar a escrita
            with self.db_lock, self._get_db_connection(db_filepath, read_only=False) as conn:
                cursor = conn.cursor()
                attempts = 0

                while attempts < max_retries:
                    try:
                        # Refactored sql_update branch with detailed step-by-step logic
                        if sql_update:
                            # 1. Find everything from WHERE up to the first semicolon (or end)
                            m = re.search(r'(WHERE\b.*?)(?:;|$)', sql_update, flags=re.IGNORECASE | re.DOTALL)
                            if not m:
                                raise ValueError("sql_update must contain a WHERE clause")
                            where_clause = m.group(1).strip()
                            pre_count_sql =  f"SELECT COUNT(*) FROM {table_name} {where_clause};"

                            # 2. Count how many rows are still unprocessed before running the update
                            cursor.execute(pre_count_sql, sql_update_params)
                            before_count = cursor.fetchone()[0]

                            # 3. Execute the UPDATE statement (sets processed = version)
                            cursor.execute(sql_update, sql_update_params)
                            conn.commit()
                            # SQLite reports the number of rows it "touched" via rowcount
                            touched_count = cursor.rowcount

                            # 4. Re-count how many rows remain unprocessed after the update
                            cursor.execute(pre_count_sql, sql_update_params)
                            after_count = cursor.fetchone()[0]

                            # 5. Compute how many rows were actually moved from unprocessed to processed
                            actually_updated = before_count - after_count

                            # 6. Compare SQLite's reported rowcount with our computed delta
                            if touched_count != actually_updated:
                                print(
                                    f"DEBUG mismatch: touched_count={touched_count}, "
                                    f"actually_updated={actually_updated}"
                                )
                            
                            # Optional: honor the original `alert` flag to print success message
                            if alert:
                                print(f"Updated {table_name}: {actually_updated} rows processed")

                        # if sql_update:
                        #     # Executa SQL personalizado (ex: UPDATE processed = version)
                        #     cursor.execute(sql_update, sql_update_params or ())
                        #     conn.commit()

                        #     # Debug opcional
                        #     time.sleep(self.dynamic_sleep())
                        #     row_count = cursor.rowcount
                        #     verify_sql = f"""
                        #         SELECT COUNT(*) FROM {table_name}
                        #         WHERE processed IS NOT NULL AND company_name = ?;
                        #     """
                        #     cursor.execute(verify_sql, sql_update_params or ())
                        #     row_updated = cursor.fetchone()[0]
                        #     if row_count != row_updated:
                        #         print(f"DEBUG executed: {row_count}, updated: {row_updated}")
                        #         print(
                        #             f"  SELECT COUNT(*) FROM {table_name} WHERE processed IS NOT NULL AND company_name = '{sql_update_params[0]}';"
                        #         )

                        else:
                            # Verifica se há colunas faltantes e ajusta tabela
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            existing_columns = {row[1] for row in cursor.fetchall()}
                            missing_columns = [col for col in dataframe.columns if col not in existing_columns]

                            for col in missing_columns:
                                safe_col = f'"{col}"'
                                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {safe_col} REAL;"
                                cursor.execute(alter_query)
                            conn.commit()

                            # Insere os dados
                            cursor.executemany(sql, data_tuples)
                            conn.commit()

                        if alert:
                            print(f"Updated {table_name} in {database_name}")

                        break  # Sai do loop em caso de sucesso

                    except Exception as e:
                        if "database is locked" in str(e):
                            attempts += 1
                            time.sleep(self.dynamic_sleep())
                        else:
                            raise  # Repassa exceções reais

        except Exception as e:
            print(dataframe.dtypes)
            if not sql_update:
                print(sql)
                dataframe.to_csv("dataframe.csv", index=False)
            self.log_error(f"Error saving to database: {e}")

    def get_columns(self, schema_str):
        """
        Extract column names and corresponding pandas dtypes from a SQL CREATE TABLE string.

        Returns:
            dict: {column_name: pandas_dtype}
        """
        try:
            match = re.search(r"\((.*?)\)\s*(;|\n)", schema_str, re.DOTALL)
            if not match:
                return {}

            column_block = match.group(1)
            column_lines = column_block.splitlines()

            col_type_dict = {}

            for line in column_lines:
                line = line.strip().strip(",")
                if not line or line.upper().startswith("PRIMARY KEY") or line.upper().startswith("FOREIGN KEY"):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue  # Skip invalid lines

                col_name = parts[0]
                sql_type = parts[1].upper()

                # SQL to pandas dtype mapping
                if "INT" in sql_type:
                    pandas_type = "Int64"
                elif "REAL" in sql_type or "FLOAT" in sql_type or "DECIMAL" in sql_type:
                    pandas_type = "float"
                elif "TEXT" in sql_type or "CHAR" in sql_type:
                    pandas_type = "string"
                else:
                    pandas_type = "object"  # Default fallback

                col_type_dict[col_name] = pandas_type

            return col_type_dict

        except Exception as e:
            self.log_error(e)
            return {}

    def _get_table_structure(self, table_name, db_filepath):
        """
        Extracts all column names, pandas dtypes, and primary key columns from a CREATE TABLE statement.

        Args:
            table_name (str): Name of the table.
            db_filepath (str): Path to the database file.

        Returns:
            tuple: (columns: List[str], dtypes: Dict[str, str], primary_keys: List[str])
        """
        columns = []
        dtypes = {}
        primary_keys = []
        database_name = os.path.basename(db_filepath)

        try:
            schema = self.config.schemas[database_name][table_name]
            lines = schema.strip().splitlines()

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Detect PRIMARY KEY
                if "PRIMARY KEY" in line.upper():
                    primary_key_index = line.upper().find("PRIMARY KEY")
                    key_part_before = line[:primary_key_index].strip()
                    key_part_after = line[primary_key_index + len("PRIMARY KEY"):].strip()

                    if key_part_before:
                        key = key_part_before.split()[0]
                        primary_keys.append(key)

                    if key_part_after.startswith("(") and key_part_after.endswith(")"):
                        keys_in_parentheses = key_part_after[1:-1].split(",")
                        primary_keys.extend(key.strip() for key in keys_in_parentheses)

                # Detect column definitions
                elif any(type_hint in line.upper() for type_hint in ["TEXT", "INTEGER", "REAL", "FLOAT", "DECIMAL", "CHAR", "DATE", "BLOB", "BOOLEAN"]):
                    parts = line.replace(",", "").split()
                    if len(parts) >= 2:
                        column_name = parts[0].strip()
                        sql_type = parts[1].strip().upper()

                        columns.append(column_name)
                        dtypes[column_name] = self._map_sql_to_pd_dtype(sql_type)

        except Exception as e:
            self.log_error(e)

        return columns, dtypes, primary_keys

    def _map_sql_to_pd_dtype(self, sql_type):
        """
        Map a SQL data type to the closest equivalent pandas dtype.

        Args:
            sql_type (str): SQL column type.

        Returns:
            str: pandas dtype string.
        """
        try:
            sql_type = sql_type.upper().strip()

            # SQL to pandas dtype mapping
            if "INT" in sql_type:
                pandas_type = "Int64"  # nullable integer
            elif "REAL" in sql_type or "FLOAT" in sql_type or "DOUBLE" in sql_type or "DECIMAL" in sql_type:
                pandas_type = "float64"
            elif "TEXT" in sql_type or "CHAR" in sql_type or "CLOB" in sql_type:
                pandas_type = "string"
            elif "BLOB" in sql_type:
                pandas_type = "object"  # binary/blob is generic object
            elif "BOOLEAN" in sql_type:
                pandas_type = "boolean"
            elif "DATE" in sql_type or "TIME" in sql_type:
                pandas_type = "datetime64[ns]"
            else:
                pandas_type = "object"  # fallback for unknown types

        except Exception as e:
            self.log_error(e)
            pandas_type = "object"

        return pandas_type

    def _get_sql_statement(self, dataframe, primary_keys, table_name, update=True):
        """Generate a SQL statement dynamically, ensuring column names are
        correctly formatted to prevent syntax errors in SQLite.

        Args:
            dataframe (DataFrame): DataFrame containing the data to insert or update.
            primary_keys (list): List of primary key columns to check for conflicts.
            table_name (str): Name of the table where the data will be saved.
            update (bool): Whether to update existing rows on conflict (default is True).

        Returns:
            str: The dynamically generated SQL statement.
        """
        sql = ""
        try:
            def quote_column(col):
                return f'"{col}"' if not col.isidentifier() or col[0].isdigit() else col

            quoted_columns = [quote_column(col) for col in dataframe.columns]
            quoted_primary_keys = [quote_column(col) for col in primary_keys] if primary_keys else []

            f_fields = "(" + ", ".join(quoted_columns) + ")"
            f_values = "(" + ", ".join(["?"] * len(dataframe.columns)) + ")"

            sql = f"INSERT INTO {table_name} {f_fields} VALUES {f_values}"

            if quoted_primary_keys and update:
                f_primary_keys = f"({', '.join(quoted_primary_keys)})"
                sql += f" ON CONFLICT {f_primary_keys}"

                f_update_set_parts = []
                for col in quoted_columns:
                    col_raw = col.strip('"')  # unquoted name
                    if col in quoted_primary_keys:
                        continue
                    elif col_raw == "processed":
                        f_update_set_parts.append(
                            f"""processed = CASE
                                WHEN {table_name}.version = excluded.version
                                THEN {table_name}.processed
                                ELSE NULL
                            END"""
                        )
                    else:
                        f_update_set_parts.append(f"{col} = excluded.{col}")

                if f_update_set_parts:
                    sql += f" DO UPDATE SET {', '.join(f_update_set_parts)}"
                else:
                    sql += " DO NOTHING"
            else:
                sql = f"INSERT OR IGNORE INTO {table_name} {f_fields} VALUES {f_values}"

        except Exception as e:
            self.log_error(f"Error in SQL statement generation: {e}")

        return sql

    def _prepare_dataframe(self, dataframe):
        """"""
        try:
            text_columns = ["version"]
            date_columns = ["quarter", "sent_date", "date", "ex_date"]
            numeric_columns = ["price_or_factor"]

            # Replace NaN with None for SQLite compatibility
            dataframe = dataframe.where(pd.notnull(dataframe), None)

            # Replace NaN and None with an empty string for text columns
            try:
                for col in text_columns:
                    if col in dataframe.columns:
                        dataframe[col] = dataframe[col].replace([None, ""], "").astype(str)
            except Exception:
                pass

            # Convert datetime columns to string in ISO format or None
            try:
                for col in date_columns:
                    if col in dataframe.columns:
                        # Convert column to datetime safely
                        try:
                            # Attempt to convert the datetime with a stricter format
                            dataframe[col] = pd.to_datetime(dataframe[col], format="%Y-%m-%d", errors="raise")
                        except Exception as e_outer:
                            try:
                                # Handle ISO 8601 format like '2010-12-31T00:00:00'
                                dataframe[col] = pd.to_datetime(dataframe[col], format="ISO8601", errors="raise")
                            except Exception as e_inner:
                                # Fallback to automatic inference of format
                                dataframe[col] = pd.to_datetime(dataframe[col], errors="coerce")
                                print(e_outer, e_inner)

                        # Apply the conversion to ISO format
                        dataframe[col] = dataframe[col].apply(
                            lambda x: (x.isoformat() if isinstance(x, pd.Timestamp) and pd.notna(x) else None)
                        )
            except Exception:
                pass

            # Ensure numeric columns have valid values or are set to None
            try:
                for col in numeric_columns:
                    if col in dataframe.columns:
                        dataframe[col] = dataframe[col].apply(lambda x: float(x) if pd.notna(x) else None)
            except Exception:
                pass

        except Exception as e:
            self.log_error(e)

        return dataframe

    def db_optimize(self, db_filepath=None):
        """Optimize the SQLite database by running VACUUM, ANALYZE, and
        REINDEX.

        Parameters:
            db_filepath (str): The file path to the SQLite database.
        """
        db_filepath = db_filepath or self.config.db_filepath

        try:
            # Acquire the lock to ensure thread safety
            with self.db_lock:
                with self._get_db_connection(db_filepath, read_only=False) as conn:
                    cursor = conn.cursor()

                    # Runs a WAL checkpoint to reduce WAL file size
                    conn.execute("PRAGMA wal_checkpoint(FULL);")

                    # Start ANALYZE to update statistics for query optimization
                    cursor.execute("ANALYZE")

                    # Start REINDEX to rebuild indexes for better performance
                    cursor.execute("REINDEX")

                    # Start VACUUM to reduce file size and defragment the database
                    cursor.execute("VACUUM")

                    conn.commit()

        except sqlite3.Error as e:
            self.log_error(f"An error occurred during database optimization: {e}")

    # OTHER NOT CLASSIFIED YET
    def explode_company(self, company_info):
        def process_ticker_isin(row):
            ticker_codes = json.loads(row["ticker_codes"]) if row["ticker_codes"] else []
            isin_codes = json.loads(row["isin_codes"]) if row["isin_codes"] else []
            ticker_isin = [
                pair for pair in sorted(list(zip(ticker_codes, isin_codes)), key=lambda x: x[0]) if "ACN" in pair[1]
            ]
            return ticker_isin

        company_info["ticker_isin"] = company_info.apply(process_ticker_isin, axis=1)
        mask = company_info["ticker_isin"].apply(lambda x: len(x) > 0)
        company_info = company_info[mask]

        company_info_exploded = company_info.explode("ticker_isin")
        company_info_exploded[["ticker_code", "isin_code"]] = pd.DataFrame(
            company_info_exploded["ticker_isin"].tolist(), index=company_info_exploded.index
        )
        company_info_exploded = company_info_exploded.drop(columns=["ticker_isin"])

        return company_info_exploded


class TemplateProcessor(BaseProcessor):
    """docstrings."""

    def __init__(self):
        """docstrings."""
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # # Initialize the WebDriver
        # self.driver, self.driver_wait = self._initialize_driver()

    def process_instance(self, sub_batch, payload, verbose, progress):
        """Process a single batch by delegating from abstract base_processor
        method to this class process_batch (true process info method) via this
        process_instance method (create instance method).

        sub_batch progress

        return result from process_batch
        """
        try:
            extra_info = [f"Worker {progress['thread_id']}", " ".join(sub_batch)]
            self.print_info(progress["batch_index"], progress["total_batches"], progress["start_time"], extra_info)
            # Delegate to process_batch for the actual batch processing
            result = self.process_batch(sub_batch, progress, verbose)

        except Exception:
            pass

        return result

    def process_batch(self, sub_batch, payload, verbose, progress):
        """"""
        result = ""

        try:
            pass
        except Exception as e:
            self.log_error(e)

        return result

    def main(self, thread=True):
        """docstring."""
        try:
            # Run existing information
            table_name = ""
            db_filepath = ""
            data_1 = self.load_data(table_name=table_name, db_filepath="")
            data_2 = self.load_data()

            # Fetch Scrape targets
            targets = ""

            # if no targets, optimize db and return True
            if targets:
                if targets.size == 0:  # Check if the array is empty
                    self.db_optimize(self.config.databases["raw"]["filepath"])
                    return True

            # Process targets using threading or sequential logic
            processed_batch = self.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            # save/update db
            if not processed_batch.empty:
                self.save_to_db(
                    dataframe=processed_batch,
                    table_name=self.config.historical_tickers_urls_table,
                    db_filepath=self.config.databases["raw"]["filepath"],
                )

        except Exception as e:
            self.log_error(e)

        return True
