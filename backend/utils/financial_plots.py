import os
import sqlite3
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import system
from utils import settings

class FinancialDataPlotter:
    def __init__(self):
        """
        Initialize the FinancialDataPlotter with a DataFrame.

        Load all tables from an SQLite database into a single DataFrame.
        """
        db_path = os.path.join(settings.db_folder, f"{settings.db_name.split('.')[0]} {settings.statements_standard}.{settings.db_name.split('.')[-1]}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Load each table into a DataFrame
        df_list = []
        start_time = time.time()  # Initialize start time for progress tracking
        for i, table_name in enumerate(tables):
            table_name = table_name[0]  # Extract table name from tuple
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df['table_name'] = table_name  # Add a column to identify the source table
            df_list.append(df)

            # Display progress using system.print_info
            extra_info = [table_name]
            system.print_info(i, extra_info, start_time, len(tables))  # Removed the total_files argument

            print('break')
            break
        conn.close()

        # Concatenate all tables into a single DataFrame
        combined_df = pd.concat(df_list, ignore_index=True)

        self.df = combined_df.copy()
        # Ensure 'quarter' is of datetime type
        if self.df['quarter'].dtype != 'datetime64[ns]':
            self.df['quarter'] = pd.to_datetime(self.df['quarter'])

    def plot_time_series(self, company_name, description, start_date=None, end_date=None):
        """
        Plot a time series of a financial metric for a given company.
        """
        # Filter data
        data = self.df[
            (self.df['company_name'] == company_name) &
            (self.df['description'] == description)
        ]

        # Apply date filters if provided
        if start_date:
            data = data[data['quarter'] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data['quarter'] <= pd.to_datetime(end_date)]

        if data.empty:
            print("No data available for the given filters.")
            return

        # Sort data by date
        data = data.sort_values('quarter')

        # Create line plot
        fig = px.line(
            data,
            x='quarter',
            y='value',
            title=f'{description} Over Time for {company_name}',
            labels={'quarter': 'Quarter', 'value': description}
        )
        fig.update_layout(xaxis_title='Quarter', yaxis_title=description)
        fig.show()

    def plot_company_comparison(self, companies, description, date):
        """
        Compare a financial metric across multiple companies at a specific date.
        """
        # Filter data
        data = self.df[
            (self.df['company_name'].isin(companies)) &
            (self.df['description'] == description) &
            (self.df['quarter'] == pd.to_datetime(date))
        ]

        if data.empty:
            print("No data available for the given filters.")
            return

        # Create bar chart
        fig = px.bar(
            data,
            x='company_name',
            y='value',
            title=f'Comparison of {description} on {date}',
            labels={'company_name': 'Company Name', 'value': description}
        )
        fig.update_layout(xaxis_title='Company Name', yaxis_title=description)
        fig.show()

    def plot_indicator_comparison(self, company_name, descriptions, start_date=None, end_date=None):
        """
        Plot multiple financial metrics over time for a single company.
        """
        # Filter data
        data = self.df[
            (self.df['company_name'] == company_name) &
            (self.df['description'].isin(descriptions))
        ]

        # Apply date filters if provided
        if start_date:
            data = data[data['quarter'] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data['quarter'] <= pd.to_datetime(end_date)]

        if data.empty:
            print("No data available for the given filters.")
            return

        # Pivot data for plotting
        data_pivot = data.pivot_table(
            index='quarter',
            columns='description',
            values='value'
        ).reset_index()

        # Create line plot with multiple traces
        fig = go.Figure()
        for desc in descriptions:
            if desc in data_pivot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data_pivot['quarter'],
                        y=data_pivot[desc],
                        mode='lines+markers',
                        name=desc
                    )
                )

        fig.update_layout(
            title=f'Financial Indicators Over Time for {company_name}',
            xaxis_title='Quarter',
            yaxis_title='Value'
        )
        fig.show()

    def plot_correlation_heatmap(self, company_name, date):
        """
        Plot a correlation heatmap of financial metrics for a given company and date.
        """
        # Filter data
        data = self.df[
            (self.df['company_name'] == company_name) &
            (self.df['quarter'] == pd.to_datetime(date))
        ]

        # Pivot data to have descriptions as columns
        data_pivot = data.pivot_table(
            index='company_name',
            columns='description',
            values='value'
        )

        if data_pivot.empty:
            print("No data available for the given filters.")
            return

        # Compute correlation matrix
        corr_matrix = data_pivot.corr()

        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            title=f'Correlation Heatmap for {company_name} on {date}'
        )
        fig.show()

    def plot_scatter(self, x_metric, y_metric, date, companies=None):
        """
        Plot a scatter plot comparing two financial metrics across companies.
        """
        # Filter data
        data_x = self.df[
            (self.df['description'] == x_metric) &
            (self.df['quarter'] == pd.to_datetime(date))
        ][['company_name', 'value']].rename(columns={'value': x_metric})

        data_y = self.df[
            (self.df['description'] == y_metric) &
            (self.df['quarter'] == pd.to_datetime(date))
        ][['company_name', 'value']].rename(columns={'value': y_metric})

        data = pd.merge(data_x, data_y, on='company_name')

        if companies:
            data = data[data['company_name'].isin(companies)]

        if data.empty:
            print("No data available for the given filters.")
            return

        # Create scatter plot
        fig = px.scatter(
            data,
            x=x_metric,
            y=y_metric,
            text='company_name',
            title=f'{y_metric} vs {x_metric} on {date}',
            labels={x_metric: x_metric, y_metric: y_metric}
        )
        fig.update_traces(textposition='top center')
        fig.show()

    def plot_stacked_bar(self, company_name, descriptions, date):
        """
        Plot a stacked bar chart to show composition of financial metrics.
        """
        # Filter data
        data = self.df[
            (self.df['company_name'] == company_name) &
            (self.df['description'].isin(descriptions)) &
            (self.df['quarter'] == pd.to_datetime(date))
        ]

        if data.empty:
            print("No data available for the given filters.")
            return

        # Create stacked bar chart
        fig = px.bar(
            data,
            x=['quarter'],
            y='value',
            color='description',
            title=f'Composition of Financial Metrics for {company_name} on {date}',
            labels={'value': 'Value', 'description': 'Description'}
        )
        fig.update_layout(barmode='stack')
        fig.show()

    def main(self):
        # Plot a time series of 'Revenue' for 'TIM SA'
        self.plot_time_series(
        company_name='TIM SA',
        description='Receita de Venda de Bens e/ou Serviços',
        start_date='2015-01-01',
        end_date='2023-06-30'
        )

        # # Compare 'Net Income' among multiple companies on a specific date
        # self.plot_company_comparison(
        #     companies=['ALGAR TELECOM SA', 'TIM SA', 'OI SA'],
        #     description='Lucro do Período',
        #     date='2023-06-30'
        # )
        # # Plot multiple indicators over time for a single company
        # self.plot_indicator_comparison(
        #     company_name='TIM SA',
        #     descriptions=['Receita de Venda de Bens e/ou Serviços', 'Lucro do Período'],
        #     start_date='2015-01-01',
        #     end_date='2023-06-30'
        # )

        # # Plot a correlation heatmap for a company at a specific date
        # self.plot_correlation_heatmap(
        #     company_name='TIM SA',
        #     date='2023-06-30'
        # )

        # # Scatter plot comparing 'Total Assets' vs 'Total Liabilities' across companies
        # self.plot_scatter(
        #     x_metric='Ativo Total',
        #     y_metric='Passivo Total',
        #     date='2023-06-30',
        #     companies=['ALGAR TELECOM SA', 'TIM SA', 'OI SA']
        # )

        # # Plot a stacked bar chart showing the composition of liabilities
        # self.plot_stacked_bar(
        #     company_name='TIM SA',
        #     descriptions=['Passivo Circulante de Curto Prazo', 'Passivo Não Circulante de Longo Prazo'],
        #     date='2023-06-30'
        # )
