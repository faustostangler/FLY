import requests
import pandas as pd
import yfinance as yf
import sqlite3
from stocksymbol import StockSymbol
from bcb import sgs
from utils import helper, system


# Yahoo Finance
# Investing.com (via investpy)
# Alpha Vantage - Stock Data
# Alpha Vantage - Forex Data
# Alpha Vantage - Cryptocurrency Data
# Banco Central do Brasil (BCB)

class StockMarketScraper:
    def __init__(self, polygon_api_key, db_path='market_data.db'):
        """
        Inicializa a classe StockMarketScraper com a API Key do Polygon e a conexão ao banco de dados SQLite.
        
        Args:
            polygon_api_key (str): A chave de API para acessar os dados do Polygon.
            db_path (str): O caminho para o banco de dados SQLite.
        """
        self.polygon_api_key = polygon_api_key
        self.db_path = db_path
        self.conn = None
        self.world_markets = None
        self.bcb_series = None
        self._connect_db()

    def _connect_db(self):
        """Estabelece a conexão com o banco de dados SQLite."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to SQLite database at {self.db_path}")
        except Exception as e:
            print(f"Error connecting to SQLite: {e}")
    
    def _create_tables(self):
        """Cria as tabelas no banco de dados, se elas ainda não existirem."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS world_markets (
                    market TEXT,
                    abbreviation TEXT,
                    totalCount INTEGER,
                    lastUpdated TEXT,
                    indexName TEXT,
                    indexId TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_data (
                    ticker TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bcb_series (
                    series_code INTEGER,
                    date TEXT,
                    value REAL
                )
            ''')
            self.conn.commit()
            print("Database tables created or verified.")
        except Exception as e:
            print(f"Error creating tables: {e}")

    def _insert_world_markets(self):
        """Insere os dados de mercados globais no banco de dados."""
        if self.world_markets is not None:
            try:
                self.world_markets.to_sql('world_markets', self.conn, if_exists='replace', index=False)
                print("World markets data inserted into database.")
            except Exception as e:
                print(f"Error inserting world markets data into database: {e}")

    def _insert_stock_data(self, ticker, stock_data):
        """Insere dados de ações no banco de dados."""
        try:
            stock_data['ticker'] = ticker
            stock_data.reset_index(inplace=True)
            stock_data = stock_data[['ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            stock_data.to_sql('stock_data', self.conn, if_exists='append', index=False)
            print(f"Stock data for {ticker} inserted into database.")
        except Exception as e:
            print(f"Error inserting stock data for {ticker}: {e}")

    def _insert_bcb_series(self, series_code):
        """Insere os dados da série histórica do BCB no banco de dados."""
        if self.bcb_series is not None:
            try:
                self.bcb_series.reset_index(inplace=True)
                self.bcb_series['series_code'] = series_code
                self.bcb_series.to_sql('bcb_series', self.conn, if_exists='append', index=False)
                print(f"BCB series {series_code} inserted into database.")
            except Exception as e:
                print(f"Error inserting BCB series {series_code} into database: {e}")

    def fetch_world_markets(self):
        """Coleta dados de mercados globais usando a API Polygon e salva no banco de dados."""
        try:
            ss = StockSymbol(self.polygon_api_key)
            world_markets = pd.DataFrame(ss.market_list())
            index_data = pd.DataFrame(ss.index_list())
            self.world_markets = pd.merge(index_data, world_markets, how="outer")
            
            # Limpeza e formatação
            self.world_markets.fillna("", inplace=True)
            self.world_markets.sort_values(by=["market", "indexName"], inplace=True)

            # Inserir os dados no banco de dados
            self._insert_world_markets()
        except Exception as e:
            print(f"Error fetching world markets: {e}")

    def fetch_stock_data_yahoo(self, ticker):
        """Coleta dados de ações de um ticker específico usando o Yahoo Finance e salva no banco de dados."""
        try:
            ticker_data = yf.Ticker(ticker)
            stock_data = ticker_data.history(period="1y")  # Coletando o histórico de 1 ano
            print(f"Data for {ticker} collected successfully.")
            
            # Inserir os dados no banco de dados
            self._insert_stock_data(ticker, stock_data)
        except Exception as e:
            print(f"Error fetching Yahoo Finance data for {ticker}: {e}")

    def fetch_bcb_series(self, series_code, start_date, end_date):
        """Coleta séries históricas do BCB e salva no banco de dados."""
        try:
            self.bcb_series = sgs.get([series_code], start=start_date, end=end_date)
            print(f"BCB series {series_code} collected successfully.")
            
            # Inserir os dados no banco de dados
            self._insert_bcb_series(series_code)
        except Exception as e:
            print(f"Error fetching BCB series {series_code}: {e}")

    def update_data_sources(self):
        """Atualiza os dados de diferentes fontes de mercado e os insere no banco de dados."""
        print("Updating all market data sources...")
        self._create_tables()
        
        # Coleta e inserção de dados de mercados globais
        self.fetch_world_markets()
        
        # Coleta e inserção de dados de ações do Yahoo Finance
        self.fetch_stock_data_yahoo('AAPL')
        
        # Coleta e inserção de séries históricas do BCB
        self.fetch_bcb_series(1, '2020-01-01', '2023-01-01')

    def close_db(self):
        """Fecha a conexão com o banco de dados SQLite."""
        if self.conn:
            self.conn.close()
            print("SQLite connection closed.")

if __name__ == "__main__":
    # Exemplo de uso da classe
    scraper = StockMarketScraper(polygon_api_key='YOUR_POLYGON_API_KEY')
    scraper.update_data_sources()
    scraper.close_db()
