import os
import re
import shutil
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import pandas as pd

from utils_original import intel, settings, system


class StandardizedReport:
    def __init__(self):
        """Initialize the StandardizedReport class with settings from the utils
        module.

        Attributes:
            data_folder (str): The folder path where the database is stored.
            db_filepath (str): The name of the database file.
        """
        try:
            self.data_folder = settings.data_folder
            self.db_filepath = settings.db_filepath
            self.db_lock = Lock()

        except Exception as e:
            system.log_error(f"Error initializing StandardizedReport: {e}")

    def load_data(self, files):
        """Run financial data from the database and process it into
        DataFrames.

        Args:
            files (str): The name part of the database file to load.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames containing the NSD data for that sector.
        """
        try:
            # Run db
            specific_name = (
                f"{settings.db_name.split('.')[0]} {settings.statements_file_math}.{settings.db_name.split('.')[-1]}"
            )
            specific_db_path = os.path.join(settings.data_folder, specific_name)

            conn = sqlite3.connect(specific_db_path)
            cursor = conn.cursor()

            # Fetch all table names excluding internal SQLite tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            dfs = {}
            total_lines = 0
            print(f"loading {files}...")
            start_time = time.monotonic()  # Initialize start time for progress tracking

            with self.db_lock:
                # Iterate through each table (sector) and process the data
                for i, table in enumerate(tables):
                    try:
                        sector = table[0]
                        df = pd.read_sql_query(f"SELECT * FROM {sector}", conn)
                        if sector != "_":
                            sector = sector.upper().replace("_", " ")  # Create a table name from sector name
                        else:
                            pass

                        # Normalize date columns to datetime format
                        df["quarter"] = pd.to_datetime(df["quarter"], errors="coerce")

                        # Normalize numeric columns
                        df["value"] = pd.to_numeric(df["value"], errors="coerce")

                        # Fill missing 'value' with 0
                        df["value"] = df["value"].fillna(0)

                        # Identify rows where 'account' is missing or NaN and 'value' has been set to 0
                        missing_account = df["account"].isna() | df["account"].str.strip().eq("")
                        df.loc[missing_account, "account"] = "0"  # Set 'account' to '0' (as text) for these rows

                        # Filter out only the latest versions for each group
                        df, _ = self.filter_newer_versions(df)
                        dfs[sector] = df  # Store the DataFrame with the sector as the key
                        total_lines += len(df)  # Update the total number of processed lines

                        # Display progress
                        extra_info = [f"Loaded {len(df)} items from {sector} in {files}, total {total_lines}"]
                        system.print_info(i, len(tables), start_time, extra_info)

                        # print('break load math')
                        # break

                    except Exception as e:
                        system.log_error(f"Error processing table {table}: {e}")

            conn.close()
            return dfs

        except Exception as e:
            system.log_error(f"Error loading existing financial statements: {e}")
            return {}

    def filter_newer_versions(self, df):
        """Filter and keep only the newest data from groups of (company_name,
        quarter, type, frame, account).

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data.

        Returns:
            pd.DataFrame: Filtered DataFrame with only the latest versions for each group.
            pd.DataFrame: DataFrame containing duplicates that were not kept.
        """
        group_columns = ["company_name", "quarter", "type", "frame", "account"]
        version_column = "version"

        try:
            # Sort and drop duplicates to keep the latest versions
            df_sorted = df.sort_values(
                by=group_columns + [version_column], ascending=[True] * len(group_columns) + [False]
            )
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep="first")

            # Also return duplicates as an optional output
            df_duplicates = df_sorted[
                df_sorted.duplicated(subset=group_columns, keep=False)
                & (df_sorted.duplicated(subset=group_columns + [version_column], keep=False) == False)
            ]

            return df_filtered, df_duplicates

        except Exception as e:
            system.log_error(f"Error during filtering newer versions: {e}")
            return pd.DataFrame(columns=settings.statements_columns), pd.DataFrame(columns=settings.statements_columns)

    def apply_criteria(
        self, df, criteria, sector, section_name, parent_mask=None, output_file="output.txt", parent_criteria_info=None
    ):
        """Applies a criterion and its sub-criteria to the DataFrame.

        Parameters:
            df (pd.DataFrame): The DataFrame to be modified.
            criteria (dict): A dictionary containing 'target', 'filter', and 'sub_criteria'.
            parent_mask (pd.Series): Optional parent level mask to apply.
            output_file (str): Path to the output file.
            parent_criteria_info (list): List to keep track of parent criteria for output purposes.

        Returns:
            pd.DataFrame: The modified DataFrame.
        """
        try:
            target = criteria["target"]
            filters = criteria["filter"]
            sub_criteria = criteria.get("sub_criteria", [])

            # Initialize the parent criteria info list if not provided
            if parent_criteria_info is None:
                parent_criteria_info = []

            # Initialize the mask for the entire DataFrame or use the parent mask
            df = df.reset_index(drop=True)  # Reset df index for correct df and mask alignment
            base_mask = pd.Series([True] * len(df)) if parent_mask is None else parent_mask.copy()
            mask = base_mask.copy()

            # Append the current criteria to the parent criteria info
            parent_criteria_info.append({"target": target, "filters": filters})

            crits = []

            # Define a dictionary to map filter conditions to functions
            condition_map = {
                "equals": lambda col, val: col == val.lower(),
                "not_equals": lambda col, val: col != val.lower(),
                # 'startswith': lambda col, val: col.str.startswith(tuple(map(str.lower, val))),
                "startswith": lambda col, val: col.astype(str).str.startswith(val),
                "not_startswith": lambda col, val: ~col.str.startswith(tuple(map(str.lower, val))),
                "endswith": lambda col, val: col.str.endswith(tuple(map(str.lower, val))),
                "not_endswith": lambda col, val: ~col.str.endswith(tuple(map(str.lower, val))),
                "contains_all": lambda col, val: col.apply(
                    lambda x: (all(term in x.lower() for term in val) if pd.notna(x) else False)
                ),
                "contains_any": lambda col, val: col.str.contains("|".join(map(re.escape, val)), case=False, na=False),
                "contains_none": lambda col, val: ~col.str.contains(
                    "|".join(map(re.escape, val)), case=False, na=False
                ),
                "not_contains": lambda col, val: col.apply(
                    lambda x: (not all(term in x.lower() for term in val) if pd.notna(x) else True)
                ),
                "not_contains_any": lambda col, val: col.apply(
                    lambda x: (all(term not in x.lower() for term in val) if pd.notna(x) else True)
                ),
                "level": lambda col, val: (col.str.count(r"\.") + 1)
                == int(val),  # Merged level filter for exact levels
            }

            # Apply each filter to the mask
            for filter_column, filter_condition, filter_value in filters:
                crits.append([filter_column, filter_condition, filter_value])

                # Convert filter values to lists for conditions that need lists
                if filter_condition in ["contains_any", "contains_none", "contains_all", "not_contains_all"]:
                    if not isinstance(filter_value, list):
                        filter_value = [filter_value]

                # df_column_lower = df[filter_column].str.lower() if df[filter_column].dtype == 'O' else df[filter_column]
                df_column_lower = (
                    df[filter_column].str.lower().str.strip() if df[filter_column].dtype == "O" else df[filter_column]
                )

                # Apply the filter condition using the mapping
                if filter_condition in condition_map:
                    condition_mask = condition_map[filter_condition](df_column_lower, filter_value)
                    mask &= condition_mask
                else:
                    raise ValueError(f"Unknown filter condition: {filter_condition}")

            # Ensure 'account_standard', 'description_standard', 'standard_criteria', and 'items_match' columns exist
            if "account_standard" not in df.columns:
                df["account_standard"] = ""
            if "description_standard" not in df.columns:
                df["description_standard"] = ""
            if "standard_criteria" not in df.columns:
                df["standard_criteria"] = ""
            if "items_match" not in df.columns:
                df["items_match"] = ""

            # Apply the target modifications to the DataFrame for the current mask
            account, description = target.split(" - ")
            df.loc[mask, "account_standard"] = account
            df.loc[mask, "description_standard"] = description
            df.loc[mask, "standard_criteria"] = " | ".join([
                f"{c[0]} {c[1]} {c[2]}" for c in crits
            ])  # Add criteria details

            # Capture "contém itens como" (items that match the mask)
            items_example = (
                df.loc[mask, ["account", "description"]]
                .drop_duplicates()
                .apply(lambda row: f"{row['account']} - {row['description']}", axis=1)
                .tolist()
            )
            df.loc[mask, "items_match"] = ", ".join(items_example)

            print(sector, section_name, f"{account} - {description}")

            # Recursively apply subcriteria using a new refined mask
            for sub in sub_criteria:
                # Create a new mask for sub-criteria by filtering the df with 'startswith' of the current filtered results
                sub_accounts = df.loc[mask, "account"].unique()
                sub_mask = df["account"].apply(lambda x: any(x.startswith(acct) for acct in sub_accounts))

                df = self.apply_criteria(
                    df,
                    sub,
                    sector,
                    section_name,
                    parent_mask=sub_mask,
                    output_file=output_file,
                    parent_criteria_info=parent_criteria_info.copy(),
                )

        except Exception as e:
            print(f"criteria error {e}")

        return df

    def apply_section_criteria(self, df, section_criteria, sector, section_name, output_file="output.txt"):
        """Main function to apply a criteria tree to the DataFrame.

        Parameters:
            df (pd.DataFrame): The DataFrame to be modified.
            section_criteria (list): List of criteria in a tree format.
            output_file (str): Path to the output file.

        Returns:
            pd.DataFrame: The modified DataFrame after applying all criteria.
        """
        for criteria in section_criteria:
            df = self.apply_criteria(df, criteria, sector, section_name, output_file=output_file)

        return df

    def generate_standard_financial_statements(self, df):
        """Generates various sections of the financial statements based on the
        provided DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing financial data.

        Returns
        -------
        pd.DataFrame
            Combined DataFrame of all generated financial statement sections.
        """
        try:
            sector = df.iloc[0]["sector"]

            standardization_sections = {
                "Composição do Capital": intel.section_0_criteria,
                "Balanço Patrimonial Ativo": intel.section_1_criteria,
                "Balanço Patrimonial Passivo": intel.section_2_criteria,
                "Demonstração do Resultado": intel.section_3_criteria,
                "Demonstração de Fluxo de Caixa": intel.section_6_criteria,
                "Demonstração de Valor Adiconado": intel.section_7_criteria,
            }
            print("standardizing sections...")
            start_time = time.monotonic()
            total_sections = len(standardization_sections)

            # Loop through each section in the standardization pack
            for i, (section_name, section_criteria) in enumerate(standardization_sections.items()):
                extra_info = [sector, section_name]
                system.print_info(i, total_sections, start_time, extra_info)

                # Call the apply_criteria_to_dataframe method for each section
                try:
                    df = self.apply_section_criteria(df, section_criteria, sector, section_name)
                except Exception as e:
                    print(f"Error during generate_standard_financial_statements section {section_name}: {e}")

        except Exception as e:
            system.log_error(f"Error during generate_standard_financial_statements: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

        return df

    def standardize_data(self, dict_df):
        """Standardize data for all sectors in the provided dictionary of
        DataFrames.

        Parameters
        ----------
        dict_df (dict): Dictionary where keys are sectors and values are DataFrames.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            print("standardizing data...")
            start_time = time.monotonic()

            for i, (sector, df) in enumerate(dict_df.items()):
                extra_info = [f"{sector}"]
                system.print_info(i, len(dict_df), start_time, extra_info)

                try:
                    # Generate standardized financial statements
                    df = self.generate_standard_financial_statements(df)

                    # Add updated DataFrame back to the dictionary
                    dict_df[sector] = df

                    # print(f'break standarditizing')
                    # break

                except Exception as e:
                    system.log_error(f"Error in standardize_data section{sector}: {e}")

            dict_df = self.sanitize_db(dict_df)

        except Exception as e:
            system.log_error(f"Error in standardize_data: {e}")
            return {}

        return dict_df

    def sanitize_db(self, dict_df):
        """
        Sanitize all DataFrames in the dictionary by:
        - Dropping rows where `account_standard` is empty.
        - Dropping unnecessary columns.
        - Renaming `account_standard` to `account` and `description_standard` to `description`.
        - Reordering columns based on `settings.statements_order` and adding `value` column.
        - Sorting by sector, subsector, segment, company_name, quarter, account.

        Args:
            dict_df (dict): Dictionary of DataFrames to sanitize, where keys are sector names.

        Returns:
            dict: Sanitized dictionary of DataFrames.
        """
        sanitized_dict = {}

        try:
            for sector, df in dict_df.items():
                # Step 1: Drop rows where 'account_standard' is empty or NaN
                df = df.dropna(subset=["account_standard"])
                df = df[df["account_standard"].str.strip() != ""]

                # Step 2: Drop the unnecessary columns
                df = df.drop(columns=["account", "description", "standard_criteria", "items_match"])

                # Step 3: Rename 'account_standard' to 'account' and 'description_standard' to 'description'
                df = df.rename(columns={"account_standard": "account", "description_standard": "description"})

                # Step 4: Reorder the DataFrame columns
                df = df[settings.statements_columns]

                # Step 5: Sort by the specified columns
                df = df.sort_values(by=settings.statements_order)

                # Add the sanitized DataFrame to the new dictionary
                sanitized_dict[sector] = df

            return sanitized_dict

        except Exception as e:
            system.log_error(f"Error during DataFrame sanitization: {e}")
            return {}

    def save_to_db(self, data_dict):
        """Save the transformed and sanitized data to the SQLite database,
        creating or replacing tables as necessary. Updates existing data and
        inserts new data.

        Args:
            data_dict (dict): Dictionary containing DataFrames of transformed data for each sector.
        """
        chunk_size = settings.chunk_size

        try:
            # Construct the database path
            specific_name = (
                f"{settings.db_name.split('.')[0]} {settings.statements_standard}.{settings.db_name.split('.')[-1]}"
            )
            specific_db_path = os.path.join(settings.data_folder, specific_name)

            # Backup the existing database before saving new data
            backup_name = f"{settings.db_name.split('.')[0]} {settings.statements_standard} {settings.backup_name}.{settings.db_name.split('.')[-1]}"
            backup_db_path = os.path.join(settings.data_folder, backup_name)

            if os.path.exists(specific_db_path):
                shutil.copyfile(specific_db_path, backup_db_path)

            with sqlite3.connect(specific_db_path) as conn:
                cursor = conn.cursor()

                start_time = time.monotonic()
                total_lines = 0

                for i, (sector, df) in enumerate(data_dict.items()):
                    df["quarter"] = df["quarter"].dt.strftime("%Y-%m-%d")

                    table_name = sector.upper().replace(" ", "_")  # Create a table name from the sector name

                    # Step 1: Create table with all the required columns
                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        nsd INTEGER,
                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        company_name TEXT,
                        quarter TEXT,
                        version TEXT,
                        type TEXT,
                        frame TEXT,
                        account TEXT,
                        description TEXT,
                        value REAL,
                        PRIMARY KEY (company_name, quarter, version, type, frame, account, description)
                    )
                    """
                    cursor.execute(create_table_sql)

                    # Step 2: Insert or update data
                    insert_sql = f"""
                    INSERT INTO {table_name} 
                    (nsd, sector, subsector, segment, company_name, quarter, version, type, frame, account, description, value) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company_name, quarter, version, type, frame, account, description) DO UPDATE SET
                    nsd=excluded.nsd,
                    sector=excluded.sector,
                    subsector=excluded.subsector,
                    segment=excluded.segment,
                    value=excluded.value
                    """

                    # Step 3: Ensure that only the necessary columns are selected for insertion
                    df_to_insert = df[
                        [
                            "nsd",
                            "sector",
                            "subsector",
                            "segment",
                            "company_name",
                            "quarter",
                            "version",
                            "type",
                            "frame",
                            "account",
                            "description",
                            "value",
                        ]
                    ]

                    # Convert the DataFrame to a list of tuples for batch insertion
                    data_to_insert = list(df_to_insert.itertuples(index=False, name=None))

                    # Step 4: Execute batch insert
                    total_chunks = len(range(0, len(data_to_insert), chunk_size))
                    total_lines = len(data_to_insert)
                    print("saving in parts...")
                    start_time = time.monotonic()  # Record the start time for progress tracking
                    for c, start in enumerate(range(0, len(data_to_insert), chunk_size)):
                        # Process the chunk
                        chunk = data_to_insert[start : start + chunk_size]
                        cursor.executemany(insert_sql, chunk)
                        conn.commit()  # Commit after each chunk

                    total_lines += len(df)
                    extra_info = [f"{sector}: {len(df)}, {total_lines} lines"]
                    system.print_info(i, len(data_dict), start_time, extra_info)

                    df.to_csv(f"df_{sector}_standard.csv", index=False)

                cursor.close()

            return data_dict

        except Exception as e:
            system.log_error(f"Error saving transformed data to database: {e}")

        def stand_clean(self, dict_df):
            dict_df = self.standardize_data(dict_df)

            dict_df = self.sanitize_db(dict_df)

            return dict_df

    def standardize_data_threaded(self, dict_df):
        """Standardize data using multiple threads.

        Args:
        -----
        dict_df : dict
            Dictionary containing raw data for processing.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            total_lines = sum(len(df) for df in dict_df.values())
            batch_size = max(1, total_lines // settings.max_workers)

            with ThreadPoolExecutor(max_workers=settings.max_workers) as worker_pool_executor:
                futures = []
                standardized_data = {}

                for start in range(0, total_lines, batch_size):
                    batch_dict = {k: dict_df[k] for k in list(dict_df.keys())[start : start + batch_size]}
                    futures.append(worker_pool_executor.submit(self.standardize_batch, batch_dict))

                for future in as_completed(futures):
                    standardized_data.update(future.result())

            return standardized_data

        except Exception as e:
            system.log_error(f"Error during multithreaded standardization: {e}")
            return {}

    def standardize_data_sequential(self, dict_df):
        """Standardize data sequentially.

        Args:
        -----
        dict_df : dict
            Dictionary containing raw data for processing.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            dict_df = self.standardize_batch(dict_df)

            return dict_df
        except Exception as e:
            system.log_error(f"Error during sequential standardization: {e}")
            return {}

    def standardize_batch(self, dict_df):
        """Standardize a batch of data.

        Args:
        -----
        dict_batch : dict
            Dictionary containing a batch of raw data.

        Returns
        -------
        dict: Standardized batch of DataFrames.
        """
        try:
            dict_df = self.standardize_data(dict_df)
            return dict_df
        except Exception as e:
            system.log_error(f"Error during batch standardization: {e}")
            return {}

    def main(self, thread=True):
        """Main function to load, process, and standardize financial statement
        data.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            dict_df = self.load_data(settings.statements_file_math)

            # Conditional execution based on thread parameter
            if thread:
                dict_df = self.standardize_data_threaded(dict_df)
            else:
                dict_df = self.standardize_data_sequential(dict_df)

            # Save standardized data to the database
            dict_df = self.save_to_db(dict_df)

            return dict_df

        except Exception as e:
            system.log_error(f"Error in main method: {e}")
            return {}


if __name__ == "__main__":
    standardization = StandardizedReport()
    standardization.main()
