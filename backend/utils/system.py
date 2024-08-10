import logging
import inspect
import platform
from datetime import datetime

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

