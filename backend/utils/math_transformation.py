import time
import os
import glob
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import system, settings

class MathTransformation:
    """
    A class to perform mathematical transformations on financial data.
    """

    def __init__(self):
        """Initialize the MathTransformation with settings."""
        self.db_folder = settings.db_folder
        self.db_name = settings.db_name

    def load_statements(self):
        """
        Load existing financial statements from all .db files in the db_folder.

        Returns:
        DataFrame: A DataFrame containing the statements data from all files.
        """
        included_patterns = [settings.table_name]
        excluded_patterns = [settings.backup_name, 'math']  # List of patterns to exclude from filenames

        try:
            all_dfs = []

            # Get all .db files in the db_folder that match the included_patterns and exclude the excluded_patterns
            database_files = [
                db_file for db_file in glob.glob(f"{self.db_folder}/*.db")
                if any(inc in os.path.basename(db_file) for inc in included_patterns)
                and not any(exc in os.path.basename(db_file) for exc in excluded_patterns)
            ]

            # Sort database files by size, smallest to largest
            database_files = sorted(database_files, key=os.path.getsize, reverse=False)

            total_files = len(database_files)
            start_time = time.time()

            for i, db_file in enumerate(database_files):
                with sqlite3.connect(db_file) as conn:
                    df = pd.read_sql_query(f"SELECT * FROM {settings.table_name}", conn)
                    all_dfs.append(df)

                # Display progress
                extra_info = [os.path.basename(db_file)]
                system.print_info(i, extra_info, start_time, total_files)

            if all_dfs:
                return pd.concat(all_dfs, ignore_index=True).drop_duplicates()
            else:
                return pd.DataFrame(columns=settings.statements_columns)
        except Exception as e:
            system.log_error(f"Error loading existing statements data: {e}")
            return pd.DataFrame()

    def run_math_with_new_instance(self, data):
        """
        Create a new instance of MathTransformation and run the math processing.
        This ensures isolated processing for different batches.

        Args:
            data (pd.DataFrame): The data batch to process.
        """
        transformer = MathTransformation()
        try:
            transformed_data = transformer.run_math(data)
            transformer.save_transformed_data(transformed_data)
        finally:
            del transformer

    def run_in_batches(self):
        """
        Run the math transformations in batches using multiple threads.
        """
        try:
            statements = self.load_statements()
            total_items = len(statements)
            batch_size = int(total_items / settings.max_workers)

            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                futures = []
                for batch_index, start in enumerate(range(0, total_items, batch_size)):
                    end = min(start + batch_size, total_items)
                    batch_data = data.iloc[start:end]
                    futures.append(executor.submit(
                        self.run_math_with_new_instance, batch_data
                    ))

                for future in as_completed(futures):
                    future.result()

        except Exception as e:
            system.log_error(f"Error during batch processing: {e}")

    def main():
        data = MathTransformation()
        data.run_in_batches()

if __name__ == "__main__":
    transformer = MathTransformation()
    transformer.run_in_batches()
