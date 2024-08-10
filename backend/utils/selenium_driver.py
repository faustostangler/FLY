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
    for reg_query in settings.registry_paths:
        try:
            # Query the Windows Registry for Chrome version
            output = subprocess.check_output(reg_query, shell=True)
            # Extract and return the version number from the registry output
            version = re.search(r'\d+\.\d+\.\d+\.\d+', output.decode('utf-8')).group(0)
            return version
        except subprocess.CalledProcessError:
            # Continue to the next registry key if this one fails
            continue

    # If registry queries fail, fallback to querying the Chrome executable directly
    try:
        # Default path to Chrome executable
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        if not os.path.exists(chrome_path):
            chrome_path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        
        # Run the Chrome executable with the version flag
        output = subprocess.check_output([chrome_path, '--version'], shell=True)
        version = re.search(r'\d+\.\d+\.\d+\.\d+', output.decode('utf-8')).group(0)
        return version

    except Exception as e:
        system.log_error(f"Failed to retrieve Chrome version: {e}")
        return None

def get_chromedriver_url(version):
    """
    Generate the download URL for ChromeDriver based on the Chrome version.

    Args:
        version (str): The Chrome version.

    Returns:
        str: The URL for downloading the corresponding ChromeDriver.
    """
    # Hardcoded URL template
    chromedriver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
    
    try:
        # Make an HTTP request to get the ChromeDriver
        response = requests.get(chromedriver_url)
        if response.status_code == 200:
            return settings.chromedriver_url
        else:
            print(f"Error obtaining ChromeDriver for version {version}")
            return None

    except Exception as e:
        system.log_error(e)
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
    try:
        # Download the ChromeDriver zip file
        response = requests.get(url)
        zip_path = dest_folder / 'chromedriver.zip'
        
        # Save the downloaded content to a zip file
        with open(zip_path, 'wb') as file:
            file.write(response.content)
        
        # Extract the ChromeDriver archive
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
        
        # Remove the downloaded zip file
        os.remove(zip_path)
        
        # Return the path to the extracted ChromeDriver executable
        chromedriver_path = dest_folder / 'chromedriver-win64' / 'chromedriver.exe'
        return str(chromedriver_path.resolve())

    except Exception as e:
        system.log_error(e)
        return None

def get_chromedriver_path():
    """
    Download and extract the ChromeDriver based on the Chrome version installed on the system.

    Returns:
        str: The path to the ChromeDriver executable.
    """
    try:
        # Define the base path for ChromeDriver download and extraction
        base_path = Path(__file__).resolve().parent.parent
        path = base_path / settings.bin_folder
        
        # Get the installed Chrome version
        chrome_version = get_chrome_version()
        if not chrome_version:
            raise Exception("Unable to determine Chrome version.")

        # Construct the URL to download the appropriate ChromeDriver version
        chromedriver_url = get_chromedriver_url(chrome_version)
        if not chromedriver_url:
            raise Exception("Unable to determine the correct ChromeDriver URL.")
        
        # Create the directory if it does not exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Download and extract ChromeDriver
        chromedriver_path = download_and_extract_chromedriver(chromedriver_url, path)
        if not chromedriver_path:
            raise Exception("Failed to download or extract ChromeDriver.")
        
        print(chromedriver_path)
        return chromedriver_path

    except Exception as e:
        system.log_error(e)
        return None

def load_driver(chromedriver_path):
    """
    Initialize and return the Selenium WebDriver and WebDriverWait instances.

    Args:
        chromedriver_path (str): The path to the ChromeDriver executable.

    Returns:
        tuple: A tuple containing the WebDriver and WebDriverWait instances.
    """
    try:
        # Initialize the ChromeDriver service
        chrome_service = Service(chromedriver_path)
        
        # Set Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=960,540")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument("--disable-infobars")
        # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode

        # Initialize WebDriver
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # Define exceptions to ignore during WebDriverWait
        exceptions_ignore = (NoSuchElementException, StaleElementReferenceException)
        driver_wait = WebDriverWait(driver, settings.wait_time, ignored_exceptions=exceptions_ignore)

        return driver, driver_wait

    except Exception as e:
        system.log_error(e)
        return None, None

def initialize_driver():
    """
    Obtain the Selenium WebDriver and WebDriverWait instances.

    This function either uses a predefined path to ChromeDriver or fetches and loads it dynamically.

    Returns:
        tuple: A tuple containing the WebDriver and WebDriverWait instances.
    """
    try:
        # Hardcoded ChromeDriver path
        chromedriver_path = r'D:\\Fausto Stangler\\Documentos\\Python\\FLY\\backend\\bin\\chromedriver-win64\\chromedriver.exe'
        driver, driver_wait = load_driver(chromedriver_path)
        
        # If the driver is not None, return it; otherwise, try dynamic path
        if driver is not None:
            return driver, driver_wait
        else:
            raise Exception("Failed to load driver from hardcoded path.")

    except Exception as initial_error:
        try:
            # Dynamically obtain the ChromeDriver path
            chromedriver_path = get_chromedriver_path()
            if not chromedriver_path:
                raise Exception("Failed to obtain ChromeDriver path dynamically.")
            
            # Load the WebDriver and return it
            driver, driver_wait = load_driver(chromedriver_path)
            return driver, driver_wait

        except Exception as dynamic_error:
            system.log_error(dynamic_error)
            return None, None

if __name__ == "__main__":
    print('This is a module, not meant to be run directly.')
