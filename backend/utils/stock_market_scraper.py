import requests
import pandas as pd
import yfinance as yf
import sqlite3
import investpy
import quandl
import wbdata
from datetime import datetime
from stocksymbol import StockSymbol
from bcb import sgs
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from fredapi import Fred
from polygon import RESTClient

# Yahoo Finance
# Investing.com (via investpy)
# Alpha Vantage - Stock Data
# Alpha Vantage - Forex Data
# Alpha Vantage - Cryptocurrency Data
# Banco Central do Brasil (BCB)
# Quandl
# Polygon.io
# FRED (Federal Reserve Economic Data)
# World Bank (via wbdata)
class StockMarketScraper:
    def __init__(self, polygon_api_key, alpha_vantage_key, fred_api_key, quandl_api_key, db_path='market_data.db'):
        """
        Inicializa a classe StockMarketScraper com as API Keys e a conexão ao banco de dados SQLite.
        
        Args:
            polygon_api_key (str): A chave de API para acessar os dados do Polygon.io.
            alpha_vantage_key (str): A chave de API para acessar os dados do Alpha Vantage.
            fred_api_key (str): A chave de API para acessar os dados do FRED.
            quandl_api_key (str): A chave de API para acessar os dados do Quandl.
            db_path (str): O caminho para o banco de dados SQLite.
        """
        self.polygon_api_key = polygon_api_key
        self.alpha_vantage_key = alpha_vantage_key
        self.fred_api_key = fred_api_key
        self.quandl_api_key = quandl_api_key
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

    # Method to insert world markets into the database
    def _insert_world_markets(self):
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

    ### New Method for Investing.com
    def fetch_investing_data(self, stock, country, from_date, to_date):
        """
        Coleta dados de ações de um país específico usando o Investing.com.
        
        Args:
            stock (str): O nome da ação.
            country (str): O país da ação.
            from_date (str): Data de início (dd/mm/AAAA).
            to_date (str): Data de fim (dd/mm/AAAA).
        
        Returns:
            pd.DataFrame: Dados da ação em formato DataFrame.
        """
        try:
            data = investpy.get_stock_historical_data(stock=stock,
                                                      country=country,
                                                      from_date=from_date,
                                                      to_date=to_date)
            print(f"Investing data for {stock} collected successfully.")
            return data
        except Exception as e:
            print(f"Error fetching data from Investing.com for {stock}: {e}")
            return pd.DataFrame()

    ### Alpha Vantage: Stock Data
    def fetch_alpha_vantage_stock(self, symbol):
        """
        Coleta dados de ações usando a API Alpha Vantage.
        
        Args:
            symbol (str): O símbolo da ação.
        
        Returns:
            pd.DataFrame: Dados da ação em formato DataFrame.
        """
        try:
            ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
            data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
            print(f"Alpha Vantage data for {symbol} collected successfully.")
            return data
        except Exception as e:
            print(f"Error fetching data from Alpha Vantage for {symbol}: {e}")
            return pd.DataFrame()

    ### Alpha Vantage: Forex Data
    def fetch_alpha_vantage_forex(self, from_currency, to_currency):
        """
        Coleta dados de câmbio (Forex) usando a API Alpha Vantage.
        
        Args:
            from_currency (str): Moeda de origem.
            to_currency (str): Moeda de destino.
        
        Returns:
            dict: Dados da taxa de câmbio.
        """
        try:
            cc = ForeignExchange(key=self.alpha_vantage_key)
            data, _ = cc.get_currency_exchange_rate(from_currency=from_currency, to_currency=to_currency)
            print(f"Alpha Vantage Forex data collected successfully: {from_currency}/{to_currency}")
            return data
        except Exception as e:
            print(f"Error fetching Forex data from Alpha Vantage: {e}")
            return {}

    ### Alpha Vantage: Cryptocurrency Data
    def fetch_alpha_vantage_crypto(self, symbol, market='USD'):
        """
        Coleta dados de criptomoeda usando a API Alpha Vantage.
        
        Args:
            symbol (str): Símbolo da criptomoeda.
            market (str): Moeda do mercado (padrão é USD).
        
        Returns:
            pd.DataFrame: Dados da criptomoeda.
        """
        try:
            crypto = CryptoCurrencies(key=self.alpha_vantage_key, output_format='pandas')
            data, _ = crypto.get_digital_currency_daily(symbol=symbol, market=market)
            print(f"Alpha Vantage crypto data for {symbol} collected successfully.")
            return data
        except Exception as e:
            print(f"Error fetching crypto data from Alpha Vantage for {symbol}: {e}")
            return pd.DataFrame()

    ### Quandl Method
    def fetch_quandl_data(self, dataset_code, start_date, end_date):
        """
        Coleta dados de uma fonte do Quandl.

        Args:
            dataset_code (str): O código do dataset do Quandl (por exemplo, 'WIKI/AAPL').
            start_date (str): Data de início no formato 'AAAA-MM-DD'.
            end_date (str): Data de fim no formato 'AAAA-MM-DD'.

        Returns:
            pd.DataFrame: Dados coletados em formato DataFrame.
        """
        try:
            quandl.ApiConfig.api_key = self.quandl_api_key
            data = quandl.get(dataset_code, start_date=start_date, end_date=end_date)
            print(f"Quandl data for {dataset_code} collected successfully.")
            return data
        except Exception as e:
            print(f"Error fetching data from Quandl: {e}")
            return pd.DataFrame()

    ### FRED Method
    def fetch_fred_data(self, series_id):
        """
        Coleta dados econômicos da série FRED.

        Args:
            series_id (str): O ID da série de dados do FRED (por exemplo, 'GDP').

        Returns:
            pd.DataFrame: Dados da série FRED.
        """
        try:
            fred = Fred(api_key=self.fred_api_key)
            data = fred.get_series(series_id)
            print(f"FRED data for series {series_id} collected successfully.")
            return pd.DataFrame(data, columns=['value']).reset_index()
        except Exception as e:
            print(f"Error fetching data from FRED: {e}")
            return pd.DataFrame()

    ### World Bank (wbdata) Method
    def fetch_wbdata(self, indicator, country, start_date, end_date):
        """
        Coleta dados econômicos de indicadores do Banco Mundial.

        Args:
            indicator (str): O código do indicador do Banco Mundial (por exemplo, 'NY.GDP.MKTP.CD' para PIB).
            country (str): O código do país (por exemplo, 'BR' para Brasil).
            start_date (str): Data de início no formato 'AAAA-MM-DD'.
            end_date (str): Data de fim no formato 'AAAA-MM-DD'.

        Returns:
            pd.DataFrame: Dados do indicador coletado.
        """
        try:
            data = wbdata.get_dataframe({indicator: 'value'}, country=country, data_date=(start_date, end_date))
            print(f"World Bank data for indicator {indicator} in {country} collected successfully.")
            return data
        except Exception as e:
            print(f"Error fetching data from World Bank: {e}")
            return pd.DataFrame()

    ### Existing method for Yahoo Finance
    def fetch_stock_data_yahoo(self, ticker):
        """Coleta dados de ações de um ticker específico usando o Yahoo Finance e salva no banco de dados."""
        try:
            ticker_data = yf.Ticker(ticker)
            stock_data = ticker_data.history(period="1y")
            print(f"Data for {ticker} collected successfully.")
            self._insert_stock_data(ticker, stock_data)
        except Exception as e:
            print(f"Error fetching Yahoo Finance data for {ticker}: {e}")

    ### Existing method for BCB Series
    def fetch_bcb_series(self, series_code, start_date, end_date):
        """Coleta séries históricas do BCB e salva no banco de dados."""
        try:
            self.bcb_series = sgs.get([series_code], start=start_date, end=end_date)
            print(f"BCB series {series_code} collected successfully.")
            self._insert_bcb_series(series_code)
        except Exception as e:
            print(f"Error fetching BCB series {series_code}: {e}")

    ### Update all sources
    def update_data_sources(self):
        """Atualiza os dados de diferentes fontes de mercado e os insere no banco de dados."""
        print("Updating all market data sources...")
        self._create_tables()
        
        # Exemplo: Investir em dados
        investing_data = self.fetch_investing_data(stock='PETR4', country='brazil', from_date='01/01/2022', to_date='01/01/2023')
        print(investing_data.head())

        # Exemplo: Alpha Vantage - Ações
        av_stock_data = self.fetch_alpha_vantage_stock(symbol='AAPL')
        print(av_stock_data.head())
        
        # Exemplo: Alpha Vantage - Forex
        av_forex_data = self.fetch_alpha_vantage_forex(from_currency='USD', to_currency='BRL')
        print(av_forex_data)
        
        # Exemplo: Alpha Vantage - Criptomoedas
        av_crypto_data = self.fetch_alpha_vantage_crypto(symbol='BTC', market='USD')
        print(av_crypto_data.head())
        
        # Exemplo: Yahoo Finance
        self.fetch_stock_data_yahoo(ticker='AAPL')
        
        # Exemplo: BCB Series
        self.fetch_bcb_series(series_code=1, start_date='2020-01-01', end_date='2023-01-01')

        # Exemplo: Quandl
        quandl_data = self.fetch_quandl_data(dataset_code='WIKI/AAPL', start_date='2022-01-01', end_date='2022-12-31')
        print(quandl_data.head())
        
        # Exemplo: FRED
        fred_data = self.fetch_fred_data(series_id='GDP')
        print(fred_data.head())

        # Exemplo: World Bank
        wbdata_data = self.fetch_wbdata(indicator='NY.GDP.MKTP.CD', country='BR', start_date='2020-01-01', end_date='2023-01-01')
        print(wbdata_data.head())

    def close_db(self):
        """Fecha a conexão com o banco de dados SQLite."""
        if self.conn:
            self.conn.close()
            print("SQLite connection closed.")
