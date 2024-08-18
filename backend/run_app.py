from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import settings
from utils import system
from utils import selenium_driver
from utils import company_scrape
from utils import nsd_scrape
from utils import capital_scrape

if __name__ == '__main__':
    try:
        # Ask the user if they want to scrape company information
        # scrape_choice = system.timed_input('Want to scrape company information? (YES/NO): ')
        scrape_choice = 'N'
        if scrape_choice.strip().upper().startswith('Y'):
            # Instancia a classe CompanyScraper e executa o processo de scraping
            scraper = company_scrape.CompanyScraper()  # Instancia a classe, o WebDriver é gerado dentro dela
            new_companies = scraper.run()  # Executa o processo principal de scraping
            scraper.close()  # Fecha o WebDriver

        # nsd_choice = system.timed_input('Want to scrape NSD data? (YES/NO): ')
        nsd_choice = 'N'
        if nsd_choice.strip().upper().startswith('Y'):
            nsd_scraper = nsd_scrape.NSDScraper()
            nsd_range = nsd_scraper.scrape_nsd()

        # capital_choice = system.timed_input('Want to scrape Capital Sheets? (YES/NO): ')
        capital_choice = 'Y'
        if capital_choice.strip().upper().startswith('Y'):
            # Initialize the scraper to identify scrape targets
            initial_scraper = capital_scrape.CapitalDataScraper()
            scrape_targets = initial_scraper.identify_scrape_targets()
            total_items = len(scrape_targets)
            batch_size = int(total_items / settings.max_workers)
            initial_scraper.close_scraper()  # Close the initial scraper after identifying targets

            # Create a ThreadPoolExecutor for simultaneous execution
            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                futures = []
                for start in range(0, total_items, batch_size):
                    end = min(start + batch_size, total_items)
                    print(f"Submitting batch from {start} to {end}")

                    futures.append(executor.submit(
                        lambda targets=scrape_targets[start:end]: (
                            capital_scrape.CapitalDataScraper().run_scraper(targets),
                            capital_scrape.CapitalDataScraper().close_scraper()  # Close the scraper after running
                        )
                    ))

                # Optionally, wait for all futures to complete
                for future in as_completed(futures):
                    future.result()  # This will raise an exception if one occurred in the thread

    except Exception as e:
        e = system.log_error(e)

    print('done')
