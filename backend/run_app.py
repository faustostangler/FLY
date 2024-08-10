from utils import settings
from utils import system
from utils import selenium_driver
from utils import company_scrape
if __name__ == "__main__":
    try:
        # Initialize the Selenium WebDriver
        driver, driver_wait = selenium_driver.initialize_driver()

        # # Ask the user if they want to scrape company information
        # scrape_choice = input("Want to scrape company information? (YES/NO): ")
        scrape_choice = 'Y'
        if scrape_choice.strip().upper().startswith('Y'):
            company_info = company_scrape.main(driver, driver_wait)

    except Exception as e:
        e = system.log_error(e)

    # Ensure the driver is closed at the end
    driver.quit() if 'driver' in locals() else None

    print('done')