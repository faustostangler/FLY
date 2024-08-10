import logging
import inspect
import platform
from datetime import datetime
import time
import string
import unidecode
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import winsound

from utils import settings


def log_error(error):
    """
    Logs an error to a file with detailed context, including caller info, 
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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    function_name = caller_frame.f_code.co_name
    line_number = caller_frame.f_lineno
    module_name = caller_frame.f_globals["__name__"]
    system_info = platform.platform()
    caller_name = caller_frame.f_globals["__name__"]

    # Configure logging settings
    logging.basicConfig(
        filename='app_errors.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
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
    """
    Generates a system beep sound with the specified frequency and duration.

    Parameters:
    - frequency (int): The frequency of the beep sound in Hertz (default is 5000 Hz).
    - duration (int): The duration of the beep sound in milliseconds (default is 50 ms).

    Returns:
    bool: True if the beep was successful, False otherwise.
    """
    winsound.Beep(frequency, duration)
    return True

def clean_text(text):
    """
    Limpa e normaliza o texto de entrada removendo pontuações, convertendo para maiúsculas e removendo espaços em branco.

    Parameters:
    - text (str): O texto de entrada a ser limpo.

    Returns:
    str: O texto limpo e normalizado.
    """
    try:
        translation_table = str.maketrans('', '', string.punctuation)
        text = unidecode.unidecode(text).translate(translation_table).upper().strip()
        text = re.sub(r'\s+', ' ', text)
    except Exception as e:
        log_error(e)
    return text

def text(xpath, driver_wait):
    """
    Encontra e recupera o texto de um elemento da web usando o xpath e o objeto de espera fornecido.

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
        return ''

def click(xpath, driver_wait):
    """
    Encontra e clica em um elemento da web usando o xpath e o objeto de espera fornecido.

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
    """
    Encontra e seleciona um elemento da web usando o xpath e o objeto de espera fornecido.

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
        return ''

def raw_text(xpath, driver_wait):
    """
    Encontra e recupera o HTML bruto de um elemento da web usando o xpath e o objeto de espera fornecido.

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
        return ''

def wait_forever(driver_wait, xpath):
    """
    Espera indefinidamente até que o elemento da web localizado pelo xpath seja encontrado.

    Parameters:
    - driver_wait (WebDriverWait): O objeto de espera para usar.
    - xpath (str): O xpath do elemento para esperar.

    Returns:
    WebElement: O elemento da web encontrado.
    """
    while True:
        try:
            element = driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element
        except Exception:
            time.sleep(settings.wait_time)

def print_info(current_index, extra_info, start_time, total_size):
    """
    Prints the provided information along with the progress, elapsed time, and remaining time.

    Parameters:
    - current_index (int): The current index of the item being processed.
    - extra_info (list): The extra information extracted containing multiple values.
    - start_time (float): The start time of the process.
    - total_size (int): The total number of items to be processed.
    """
    completed_items = current_index + 1
    remaining_items = total_size - completed_items
    percentage_completed = completed_items / total_size
    
    elapsed_time = time.time() - start_time
    avg_time_per_item = elapsed_time / completed_items
    remaining_time = remaining_items * avg_time_per_item
    
    elapsed_hours, elapsed_remainder = divmod(int(elapsed_time), 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_remainder, 60)
    elapsed_time_formatted = f'{int(elapsed_hours)}h {int(elapsed_minutes):02}m {int(elapsed_seconds):02}s'

    remaining_hours, remaining_remainder = divmod(int(remaining_time), 3600)
    remaining_minutes, remaining_seconds = divmod(remaining_remainder, 60)
    remaining_time_formatted = f'{int(remaining_hours)}h {int(remaining_minutes):02}m {int(remaining_seconds):02}s'
    
    progress = (
        f'{percentage_completed:.2%} '
        f'{completed_items}+{remaining_items}, '
        f'{avg_time_per_item:.6f}s per item, '
        f'Time: {elapsed_time_formatted} + {remaining_time_formatted}'
    )
    
    extra_info_str = " ".join(map(str, extra_info))
    print(f"{progress} {extra_info_str}")
    winbeep()

