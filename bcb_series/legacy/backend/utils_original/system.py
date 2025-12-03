import inspect
import logging
import platform
import random
import re
import sqlite3
import string
import subprocess
import threading
import time
from datetime import datetime

import pyautogui
import unidecode
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from utils_original import settings

# logging.basicConfig(level=logging.DEBUG)


def log_error(error):
    """Logs an error to a file with detailed context, including caller info,
    module, function, line number, timestamp, and system information.

    Parameters:
    error (Exception): The exception instance that occurred.

    Returns:
    Exception: The passed exception is returned for further handling if needed.
    """
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
    )

    # Log the error message to the file
    logging.error(log_message)

    # Print a simplified error message to the console
    print(f"Error in {function_name} (line {line_number}): {error}")

    return error


def winbeep(frequency=5000, duration=50):
    """Generates a system beep sound with the specified frequency and duration.

    Parameters:
    - frequency (int): The frequency of the beep sound in Hertz (default is 5000 Hz).
    - duration (int): The duration of the beep sound in milliseconds (default is 50 ms).

    Returns:
    bool: True if the beep was successful, False otherwise.
    """
    # winsound.Beep(frequency, duration)
    return True


def clean_text(text):
    """Cleans and normalizes the input text by removing punctuation, converting
    to uppercase, removing extra whitespace, and eliminating specific words.

    Parameters:
    - text (str): The input text to be cleaned.

    Returns:
    str: The cleaned and normalized text.
    """
    try:
        # Remove punctuation, accents, and normalize case
        translation_table = str.maketrans("", "", string.punctuation)
        text = unidecode.unidecode(text).translate(translation_table).upper().strip()
        text = re.sub(r"\s+", " ", text)

        # Regular expression pattern to remove specific words from text
        words_to_remove = "|".join(map(re.escape, settings.words_to_remove))
        pattern = r"\b(?:" + words_to_remove + r")\b"
        text = re.sub(pattern, "", text)

        # Remove extra spaces after word removal
        text = re.sub(r"\s+", " ", text).strip()

    except Exception as e:
        log_error(e)

    return text


def text(xpath, driver_wait):
    """Encontra e recupera o texto de um elemento da web usando o xpath e o
    objeto de espera fornecido.

    Parameters:
    - xpath (str): O xpath do elemento para recuperar o texto.
    - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

    Returns:
    str: O texto do elemento ou uma string vazia se ocorrer uma exceção.
    """
    try:
        element = wait_forever(driver_wait, xpath)
        return element.text
    except Exception as e:
        log_error(e)
        return ""


def click(xpath, driver_wait):
    """Encontra e clica em um elemento da web usando o xpath e o objeto de
    espera fornecido.

    Parameters:
    - xpath (str): O xpath do elemento para clicar.
    - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

    Returns:
    bool: True se o elemento foi encontrado e clicado, False caso contrário.
    """
    try:
        element = wait_forever(driver_wait, xpath)
        element.click()
        return True
    except Exception as e:
        log_error(e)
        return False


def choose(xpath, driver, driver_wait):
    """Encontra e seleciona um elemento da web usando o xpath e o objeto de
    espera fornecido.

    Parameters:
    - xpath (str): O xpath do elemento para selecionar.
    - driver (webdriver.Chrome): O objeto driver Chrome a ser usado.
    - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

    Returns:
    int: O valor da opção selecionada ou uma string vazia se ocorrer uma exceção.
    """
    try:
        element = wait_forever(driver_wait, xpath)
        element.click()
        select = Select(driver.find_element(By.XPATH, xpath))
        options = [int(option.text) for option in select.options]
        highest_option = str(max(options))
        select.select_by_value(highest_option)
        return int(highest_option)
    except Exception as e:
        log_error(e)
        return ""


def select(xpath, text, driver, driver_wait):
    element = wait_forever(driver_wait, xpath, max_attempts=3)
    select = Select(driver.find_element(By.XPATH, xpath))
    select.select_by_visible_text(text)

    return select


def raw_text(xpath, driver_wait):
    """Encontra e recupera o HTML bruto de um elemento da web usando o xpath e
    o objeto de espera fornecido.

    Parameters:
    - xpath (str): O xpath do elemento para recuperar o HTML bruto.
    - driver_wait (WebDriverWait): O objeto de espera para encontrar o elemento.

    Returns:
    str: O HTML bruto do elemento ou uma string vazia se ocorrer uma exceção.
    """
    try:
        element = wait_forever(driver_wait, xpath)
        return element.get_attribute("innerHTML")
    except Exception as e:
        log_error(e)
        return ""


def wait_forever(driver_wait, xpath, max_attempts=None):
    """Espera indefinidamente até que o elemento da web localizado pelo xpath
    seja encontrado.

    Parameters:
    - driver_wait (WebDriverWait): O objeto de espera para usar.
    - xpath (str): O xpath do elemento para esperar.

    Returns:
    WebElement: O elemento da web encontrado.
    """
    attempt = 0
    while True:
        try:
            element = driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element
        except Exception as e:
            attempt += 1
            if max_attempts and attempt >= max_attempts:
                raise TimeoutException(f"Element with xpath '{xpath}' not found after {max_attempts} attempts.") from e
            time.sleep(settings.wait_time)


def subtract_lists(list1, list2):
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


def escape_keywords(keywords):
    """Escape special characters in a list of keywords for regex operations.

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


def print_info(index, size, start_time=time.monotonic(), extra_info=[]):
    """Prints the provided information along with the progress, elapsed time,
    estimated remaining time, and total estimated time.

    Parameters:
    - index (int): The current index of the item being processed.
    - size (int): The total number of items to be processed.
    - start_time (float): The start time of the process.
    - extra_info (list): The extra information extracted containing multiple values.
    """
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
    remaining_time_formatted = f"{int(remaining_hours)}h {int(remaining_minutes):02}m {int(remaining_seconds):02}s"

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

    extra_info_str = " ".join(map(str, extra_info))
    print(f"{progress} {extra_info_str}")
    winbeep()


def prefill_input(text, delay=1):
    """Simulate typing the default text into the input field.

    Parameters:
    - text (str): The text to pre-fill in the input.
    - delay (int): The delay before typing starts.
    """
    time.sleep(delay)
    pyautogui.typewrite(text)


def timed_input(prompt, timeout=5, default="YES"):
    """Display a prompt and return the user's input, with a timeout and pre-
    filled value.

    Parameters:
    - prompt (str): The input prompt to display.
    - timeout (int): The number of seconds to wait for input.
    - default (str): The default value to return if timeout is reached.

    Returns:
    - str: The user's input or the default value if timeout is reached.
    """
    prefill_thread = threading.Thread(target=prefill_input, args=(default,))
    prefill_thread.start()

    print(f"{prompt} (default: {default}) [You have {timeout} seconds to answer]: ", end="", flush=True)

    # Run a thread to run the input() call, which will block until the user provides input
    input_thread = threading.Thread(target=lambda: input())
    input_thread.start()

    # Wait for the input or timeout
    input_thread.join(timeout=timeout)

    if input_thread.is_alive():
        # print(f'\nNo input provided within {timeout} seconds. Using default: {default}')
        return default
    else:
        return input()


def header_random():
    """Generate random HTTP headers for requests."""
    user_agent = random.choice(settings.USER_AGENTS)
    referer = random.choice(settings.REFERERS)
    language = random.choice(settings.LANGUAGES)

    headers = {"User-Agent": user_agent, "Referer": referer, "Accept-Language": language}

    return headers


def test_internet(host="8.8.8.8"):
    """Test internet connection by pinging a specified host. Retries if no
    connection is detected.

    Parameters:
        host (str): The host to ping (default: Google's public DNS server 8.8.8.8).
    """
    wait_time = settings.wait_time

    while True:
        try:
            result = subprocess.run(
                ["ping", "-n", "1", host],  # Use "-n" for Windows; "-c" would be used on Unix systems.
                stdout=subprocess.DEVNULL,  # Suppress standard output.
                stderr=subprocess.DEVNULL,  # Suppress error output.
            )
            if result.returncode == 0:
                break
            else:
                print(f"No Internet connection: code {result.returncode}. Retrying in {wait_time} seconds...")
        except Exception as e:
            print(f"Error running ping command: {e}. Retrying in {wait_time} seconds...")
        time.sleep(wait_time)


def db_optimize(db_filepath=settings.db_filepath):
    """Optimize the SQLite database by running VACUUM, ANALYZE, and REINDEX.

    Parameters:
    db_filepath (str): The file path to the SQLite database.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        # Start VACUUM to reduce file size and defragment the database
        cursor.execute("VACUUM")

        # Start ANALYZE to update statistics for query optimization
        cursor.execute("ANALYZE")

        # Start REINDEX to rebuild indexes for better performance
        cursor.execute("REINDEX")

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print(f"Database optimization completed successfully ({db_filepath}).")

    except sqlite3.Error as e:
        print(f"An error occurred during database optimization: {e}")
