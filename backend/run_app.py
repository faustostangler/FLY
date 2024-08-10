from utils import settings
from utils import system
from utils import selenium_driver
from utils import company_scrape


if __name__ == "__main__":
    try:
        # Ask the user if they want to scrape company information
        scrape_choice = input("Want to scrape company information? (YES/NO): ")
        # scrape_choice = 'Y'
        if scrape_choice.strip().upper().startswith('Y'):
            # Instancia a classe CompanyScraper e executa o processo de scraping
            scraper = company_scrape.CompanyScraper()  # Instancia a classe, o WebDriver é gerado dentro dela
            scraper.run()  # Executa o processo principal de scraping
            scraper.close()  # Fecha o WebDriver

    except Exception as e:
        e = system.log_error(e)

    print('done')