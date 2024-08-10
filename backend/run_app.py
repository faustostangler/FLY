from utils import settings
from utils import system
from utils import selenium_driver

if __name__ == "__main__":
    try:
        # Initialize the Selenium WebDriver
        driver, driver_wait = selenium_driver.initialize_driver()

        # Perform actions using the driver, e.g., navigate to a webpage
        # driver.get("https://example.com")

        # Clean up and close the driver after use
        driver.quit()

    except Exception as e:
        e = system.log_error(e)

    print('done')