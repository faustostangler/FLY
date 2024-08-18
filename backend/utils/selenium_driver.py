import os
import re
import requests
import subprocess
import zipfile
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from utils import system
from utils import settings

def get_chrome_version():
    """
    Retrieve the version of Chrome installed on the system.

    Returns:
        str: The Chrome version, or None if not found.
    """
    chrome_path_64 = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    chrome_path_32 = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    chrome_error_msg = 'Failed to retrieve Chrome version: {e}'

    for reg_query in settings.registry_paths:
        try:
            output = subprocess.check_output(reg_query, shell=True)
            version = re.search(r'\d+\.\d+\.\d+\.\d+', output.decode('utf-8')).group(0)
            return version
        except subprocess.CalledProcessError:
            continue

    try:
        chrome_path = chrome_path_64 if os.path.exists(chrome_path_64) else chrome_path_32
        output = subprocess.check_output([chrome_path, '--version'], shell=True)
        version = re.search(r'\d+\.\d+\.\d+\.\d+', output.decode('utf-8')).group(0)
        return version

    except Exception as e:
        system.log_error(chrome_error_msg.format(e=e))
        return None

def get_chromedriver_url(version):
    """
    Generate the download URL for ChromeDriver based on the Chrome version.

    Args:
        version (str): The Chrome version.

    Returns:
        str: The URL for downloading the corresponding ChromeDriver.
    """
    chromedriver_url_template = f'https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip'
    url_error_msg = f'Error obtaining ChromeDriver for version {version}'

    try:
        response = requests.get(chromedriver_url_template)
        if response.status_code == 200:
            return chromedriver_url_template
        else:
            print(url_error_msg)
            return None

    except Exception as e:
        system.log_error(str(e))
        return None

def download_and_extract_chromedriver(url, dest_folder):
    """
    Download and extract ChromeDriver from the given URL.

    Args:
        url (str): The URL for downloading ChromeDriver.
        dest_folder (Path): The destination folder for extraction.

    Returns:
        str: The path to the extracted ChromeDriver executable.
    """
    zip_filename = 'chromedriver.zip'
    chromedriver_folder = 'chromedriver-win64'
    chromedriver_executable = 'chromedriver.exe'
    download_error_msg = 'Failed to download or extract ChromeDriver: {e}'

    try:
        response = requests.get(url)
        zip_path = dest_folder / zip_filename

        with open(zip_path, 'wb') as file:
            file.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)

        os.remove(zip_path)
        chromedriver_path = dest_folder / chromedriver_folder / chromedriver_executable
        return str(chromedriver_path.resolve())

    except Exception as e:
        system.log_error(download_error_msg.format(e=e))
        return None

def get_chromedriver_path():
    """
    Download and extract the ChromeDriver based on the Chrome version installed on the system.

    Returns:
        str: The path to the ChromeDriver executable.
    """
    base_path = Path(__file__).resolve().parent.parent
    bin_folder = settings.bin_folder
    chrome_version_error_msg = 'Unable to determine Chrome version.'
    chromedriver_url_error_msg = 'Unable to determine the correct ChromeDriver URL.'
    path_error_msg = 'Failed to obtain ChromeDriver path dynamically.'

    try:
        chrome_version = get_chrome_version()
        if not chrome_version:
            raise Exception(chrome_version_error_msg)

        chromedriver_url = get_chromedriver_url(chrome_version)
        if not chromedriver_url:
            raise Exception(chromedriver_url_error_msg)

        path = base_path / bin_folder
        path.mkdir(parents=True, exist_ok=True)

        chromedriver_path = download_and_extract_chromedriver(chromedriver_url, path)
        if not chromedriver_path:
            raise Exception(path_error_msg)

        return chromedriver_path

    except Exception as e:
        system.log_error(str(e))
        return None

def load_driver(chromedriver_path):
    """
    Initialize and return the Selenium WebDriver and WebDriverWait instances.

    Args:
        chromedriver_path (str): The path to the ChromeDriver executable.

    Returns:
        tuple: A tuple containing the WebDriver and WebDriverWait instances.
    """
    load_driver_error_msg = 'Failed to load driver: {e}'

    try:
        # Get random headers using the custom function
        headers = system.header_random()

        chrome_service = Service(chromedriver_path)
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
        chrome_options.add_argument('--window-size=960,540')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        exceptions_ignore = (NoSuchElementException, StaleElementReferenceException)
        driver_wait = WebDriverWait(driver, settings.wait_time, ignored_exceptions=exceptions_ignore)

        return driver, driver_wait

    except Exception as e:
        system.log_error(load_driver_error_msg.format(e=e))
        return None, None

def initialize_driver():
    """
    Obtain the Selenium WebDriver and WebDriverWait instances.

    This function either uses a predefined path to ChromeDriver or fetches and loads it dynamically.

    Returns:
        tuple: A tuple containing the WebDriver and WebDriverWait instances.
    """
    hardcoded_chromedriver_path = r'D:\\Fausto Stangler\\Documentos\\Python\\FLY\\backend\\bin\\chromedriver-win64\\chromedriver.exe'
    initialize_driver_error_msg = 'Failed to load driver from hardcoded path.'
    dynamic_driver_error_msg = 'Failed to obtain ChromeDriver path dynamically.'

    try:
        driver, driver_wait = load_driver(hardcoded_chromedriver_path)
        if driver is not None:
            return driver, driver_wait
        else:
            raise Exception(initialize_driver_error_msg)

    except Exception as initial_error:
        try:
            chromedriver_path = get_chromedriver_path()
            if not chromedriver_path:
                raise Exception(dynamic_driver_error_msg)

            driver, driver_wait = load_driver(chromedriver_path)
            return driver, driver_wait

        except Exception as dynamic_error:
            system.log_error(str(dynamic_error))
            return None, None

if __name__ == '__main__':
    print(settings.module_alert)
