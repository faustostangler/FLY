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
            scraper.run()  # Executa o processo principal de scraping
            scraper.close()  # Fecha o WebDriver

        # nsd_choice = system.timed_input('Want to scrape NSD data? (YES/NO): ')
        nsd_choice = 'N'
        if nsd_choice.strip().upper().startswith('Y'):
            nsd_scraper = nsd_scrape.NSDScraper()
            nsd_scraper.scrape_nsd()
            nsd_scraper.close()

        # capital_choice = system.timed_input('Want to scrape Capital Sheets? (YES/NO): ')
        capital_choice = 'Y'
        if capital_choice.strip().upper().startswith('Y'):
            capital_scraper = capital_scrape.CapitalDataScraper()
            capital_scraper.run_scraper()
            capital_scraper.close()

    except Exception as e:
        e = system.log_error(e)

    print('done')
