from utils import settings
from utils import system
from utils import selenium_driver
from utils import company_scrape
from utils import nsd_scrape
from utils import statements_scrape
from utils import math_transformation

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

        # statements_choice = system.timed_input('Want to scrape Statements Sheets? (YES/NO): ')
        statements_choice = 'Y'
        if statements_choice.strip().upper().startswith('Y'):
            statements_scrape.StatementsDataScraper.main()

        # math_choice = system.timed_input('Want to scrape Statements Sheets? (YES/NO): ')
        math_choice = 'Y'
        if math_choice.strip().upper().startswith('Y'):
            # Call the MathTransformation process
            math_transformation.MathTransformation.main()

    except Exception as e:
        e = system.log_error(e)

    print('done')
