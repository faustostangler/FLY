import os
import re
import sqlite3
import time
from threading import Lock

import pandas as pd
from tqdm import tqdm
from typing import Generator, Tuple, List

from utils import intel
from utils.base_processor import BaseProcessor


class IntelProcessor(BaseProcessor):
    """docstrings."""

    def __init__(self):
        """
        Initialize the IntelProcessor class.

        Sets up threading, caching, and database/table references required for 
        processing and standardizing financial statements. Loads section-based
        classification criteria from the intel module.
        """
        super().__init__()

        # Initialize a threading Lock to ensure thread safety during database operations
        self.db_lock = Lock()

        # Cache for compiled regex patterns to optimize repeated operations
        self.regex_cache = {}

        # Retrieve database table and index names from the configuration
        self.tbl_statements_raw = self.config.databases["raw"]["table"]["statements_raw"]
        self.tbl_pending_companies = self.config.databases["raw"]["table"]["pending_companies"]
        self.idx_statements_raw = self.config.databases["raw"]["index"]["statements_raw"]
        self.tbl_statements_normalized = self.config.databases["raw"]["table"]["statements_normalized"]
        self.primary_key_columns = self.config.domain["statements_sheet_columns"]

        # Define the path to the database file
        self.db_filepath = self.config.databases["raw"]["filepath"]

        # Define standard section classification rules for financial statements
        self.section_criterias = {
            "Composição do Capital": intel.section_0_criteria,
            "Balanço Patrimonial Ativo": intel.section_1_criteria,
            "Balanço Patrimonial Passivo": intel.section_2_criteria,
            "Demonstração do Resultado": intel.section_3_criteria,
            "Demonstração de Fluxo de Caixa": intel.section_6_criteria,
            "Demonstração de Valor Adiconado": intel.section_7_criteria,
        }

    def process_instance(self, sub_batch, payload, verbose, progress):
        """
        Process a single batch of financial data.

        This method serves as an override of the BaseProcessor abstract method.
        It creates a new IntelProcessor instance, delegates the data processing 
        to `process_batch`, and optionally logs the batch progress.

        Args:
            sub_batch (pd.DataFrame): A slice of the full dataset to be processed in this batch.
            payload (Any): Optional extra data passed to the batch processor.
            progress (dict): Dictionary tracking the progress of the batch (index, thread ID, etc).
            verbose (bool): If True, prints progress information to stdout.

        Returns:
            pd.DataFrame: Processed and transformed financial data. Returns an empty DataFrame on failure.
        """
        result = pd.DataFrame()  # Return an empty DataFrame on failure

        try:
            # Print batch progress if messaging is enabled
            if verbose:
                print(
                    f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} "
                    f"{100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
                )

            # Create a fresh instance for isolated batch processing
            batch_processor = IntelProcessor()

            # Process the batch and benchmark execution time
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, verbose, progress, benchmark_mode=False
            )

            # Optional: Log processed company names and worker info for traceability
            # first = f"{sub_batch['company_name'].iloc[0]}"
            # last = f"{sub_batch['company_name'].iloc[-1]}"
            # extra_info = [f"Worker download {progress['thread_id']}"]
            # self.print_info(progress['batch_index'], progress['total_batches'], progress['start_time'], extra_info)

        except Exception as e:
            # Log and suppress exceptions to prevent total failure
            self.log_error(f"Error in process_instance: {e}")

        return result

    @BaseProcessor().profile_generator()
    def process_batch(self, sub_batch, payload, verbose, progress):
        """
        Process a batch of financial statement data, grouped by company,
        applying version control, standardization, cleaning, transformation,
        and persistence to the database.
        """
        all_results = []
        result = pd.DataFrame(columns=sub_batch.columns)

        try:
            # Extract unique company names to iterate per-company
            companies = sub_batch["company_name"].unique()
            total_companies = len(companies)

            start_time = time.monotonic()
            for i, company_name in enumerate(companies):
                # Filter rows for current company
                mask = sub_batch["company_name"] == company_name
                df = sub_batch[mask]

                # Apply version control: keep only most recent, discard old/duplicates
                result, df_older, df_duplicates = self._filter_newer_versions(df)

                # Generate standard financial structure from raw data
                result1 = self.generate_standard_financial_statements(result, progress, verbose)

                # Ensure consistency in column formats, naming, types
                result2 = self.adjust_columns(result1)

                # Detect and correct data outliers or anomalies
                result3 = self.detect_and_correct_outliers(result2)

                # Apply mathematical logic to adjust values by quarter
                result4 = self._transform_quarterly_values(result3)

                # Save final cleaned and transformed data
                self.save_to_db(
                    dataframe=result4,
                    table_name=self.tbl_statements_normalized,
                    db_filepath=self.db_filepath,
                    alert=False,
                    update=False,
                )

                # Update `processed` version in the raw table only if it's new
                sql_update = """
                    UPDATE tbl_statements_raw
                    SET processed = version
                    WHERE company_name = ?
                    AND (processed IS NULL OR processed <> version);
                """
                self.save_to_db(
                    dataframe=df,
                    table_name="tbl_statements_raw",
                    db_filepath=self.db_filepath,
                    alert=False,
                    sql_update=sql_update,
                    sql_update_params=(company_name,),
                )

                # after you’ve built and saved result4:
                all_results.append(result4)

                # Calculate progress info
                actual_item = progress["batch_start"] + i + 1
                total_items = progress["scrape_size"]
                worker_info = f"Worker download {progress['thread_id']} Item {100 * actual_item / total_items:.02f}% ({actual_item}/{total_items})"

                # Quarter range for logging
                quarter_min = (
                    pd.to_datetime(df["quarter"].min(), errors="coerce").strftime("%Y-%m")
                    if not df["quarter"].isna().all()
                    else None
                )
                quarter_max = (
                    pd.to_datetime(df["quarter"].max(), errors="coerce").strftime("%Y-%m")
                    if not df["quarter"].isna().all()
                    else None
                )
                quarter_info = f"from {quarter_min} to {quarter_max}"

                # Compose log metadata (sector omitted by choice)
                extra_info = [worker_info, company_name, quarter_info]
                self.print_info(i, total_companies, start_time, extra_info, indent_level=1)

        except Exception as e:
            self.log_error(e)

        # prepare all results to return as a dataframe
        if all_results:
            final_result = pd.concat(all_results, ignore_index=True)
        else:
            final_result = pd.DataFrame(columns=sub_batch.columns)

        return final_result
    
    def generate_standard_financial_statements(self, sub_batch, progress, verbose):
        """
        Standardizes financial statement sections based on pre-defined criteria.

        This method prepares the input data and applies hierarchical criteria
        to classify financial accounts into standard statement sections such as
        'Balanço Patrimonial', 'DRE', and 'DFC'. The result is a single enriched
        DataFrame with updated `section_name`, `account`, and `description`.

        Parameters
        ----------
        sub_batch : pd.DataFrame
            Raw financial data for a single company.
        progress : dict
            A dictionary tracking batch index and thread ID for logging.

        Returns
        -------
        pd.DataFrame
            The same DataFrame with standardized financial section mappings applied.
        """
        try:
            # Precompute helper columns for faster criteria matching
            sub_batch["account_lower"] = sub_batch["account"].astype(str).str.lower().str.strip()
            sub_batch["description_lower"] = sub_batch["description"].astype(str).str.lower().str.strip()
            sub_batch["account_level"] = sub_batch["account"].astype(str).str.count(r"\.") + 1

            # Apply each set of section criteria defined in intel.py
            for i, (section_name, section_criteria) in enumerate(self.section_criterias.items()):
                sub_batch = self.apply_section_criteria(sub_batch, section_name, section_criteria)

                # Optional logging for benchmarking section mapping
                # extra_info = [progress['thread_id'], progress['batch_index'], company_name, section_name.upper()]
                # self.print_info(i, len(self.section_criterias), start_time, extra_info, indent_level=3)

        except Exception as e:
            self.log_error(f"Error applying standardization criteria: {e}")

        return sub_batch

    def apply_section_criteria(self, df, section_name, section_criteria, output_file="output.txt"):
        """
        Apply a list of classification criteria (including subcriteria) to assign financial accounts
        to a specified financial statement section.

        This method processes a criteria tree, applying recursive filters to label rows of the
        DataFrame with hierarchical financial structure. It delegates each criteria item to 
        `apply_criteria`, which handles actual filtering and assignment.

        Parameters:
            df (pd.DataFrame): The financial data to be processed.
            section_name (str): The name of the financial statement section to classify under.
            section_criteria (list): List of criteria dictionaries defining matching rules and sub-structure.
            output_file (str): Optional path for debugging or export (currently unused).

        Returns:
            pd.DataFrame: The updated DataFrame with matched rows classified by section.
        """
        try:
            # Track time for logging or benchmarking (optional)
            start_time = time.monotonic()

            # Iterate over each criteria item in the section tree
            for i, criteria_item in enumerate(section_criteria):
                # Apply this criteria and any nested sub-criteria
                df, section_name, account, description = self.apply_criteria(
                    df, section_name, criteria_item, output_file=output_file
                )

                # Optional verbose logging for each matched pattern
                # extra_info = [section_name.upper(), account, description]
                # self.print_info(i, len(section_criteria), start_time, extra_info, indent_level=4)

        except Exception as e:
            # Log any errors encountered during criteria evaluation
            self.print_info(e)

        return df

    def get_regex_union(self, values):
        """
        Compile or retrieve a regex pattern that matches any of the provided terms.

        This method checks the cache for an existing compiled regex pattern
        for the given list of terms. If not cached, it compiles a new pattern
        using logical OR and stores it.

        Args:
            values (list[str]): List of string values to match against.

        Returns:
            re.Pattern: A compiled regex pattern matching any of the input terms (case-insensitive).
        """
        try:
            # Convert to tuple for immutability to use as cache key
            pattern_key = ("ANY", tuple(values))

            # Compile and cache regex if not already done
            if pattern_key not in self.regex_cache:
                # Join all terms using OR (|), escaping special characters
                pattern = "|".join(map(re.escape, values))
                self.regex_cache[pattern_key] = re.compile(pattern, re.IGNORECASE)

            # Return the compiled pattern from cache
            return self.regex_cache[pattern_key]

        except Exception as e:
            self.log_error(f"Error in get_regex_union: {e}")
            return values
    
    def get_regex_all(self, values):
        """
        Compile or retrieve a regex pattern that matches when all terms are present.

        This method uses positive lookahead assertions to ensure that all specified
        terms appear somewhere in the string. If the pattern was previously compiled,
        it retrieves it from the cache; otherwise, it compiles and stores it.

        Args:
            values (list[str]): List of string values that must all be present.

        Returns:
            re.Pattern: A compiled regex pattern matching all input terms (case-insensitive).
        """
        try:
            # Convert list to tuple to form an immutable cache key
            pattern_key = ("ALL", tuple(values))

            # If not already cached, compile pattern using positive lookaheads
            if pattern_key not in self.regex_cache:
                pattern = "^" + "".join(f"(?=.*{re.escape(val)})" for val in values)
                self.regex_cache[pattern_key] = re.compile(pattern, re.IGNORECASE)

            # Return the compiled pattern
            return self.regex_cache[pattern_key]

        except Exception as e:
            self.log_error(f"Error in get_regex_all: {e}")
            return values

    def get_regex_include_exclude(self, includes, excludes, require_all=False):
        """
        Compile or retrieve a regex pattern based on inclusion and exclusion criteria.

        Combines positive and negative lookahead assertions to ensure that:
        - All or any of the `includes` terms are present.
        - None of the `excludes` terms are present.

        Args:
            includes (list[str]): Terms that must be present (all or any).
            excludes (list[str]): Terms that must not be present.
            require_all (bool): If True, all includes must be matched. If False, any is enough.

        Returns:
            re.Pattern: A compiled regex pattern that meets the inclusion and exclusion rules.
        """
        try:
            # Define key based on inclusion logic and exclusion list
            key = ("ALL_NONE" if require_all else "ANY_NONE", tuple(includes), tuple(excludes))

            # If not cached, compile and store the pattern
            if key not in self.regex_cache:
                # Create negative lookaheads for each excluded term
                neg_part = "".join(f"(?!.*{re.escape(term)})" for term in excludes)

                # Create positive lookaheads for included terms
                if require_all:
                    pos_part = "".join(f"(?=.*{re.escape(term)})" for term in includes)
                else:
                    pos_part = f"(?=.*(?:{'|'.join(map(re.escape, includes))}))"

                # Combine into final pattern
                pattern = "^" + neg_part + pos_part
                self.regex_cache[key] = re.compile(pattern, re.IGNORECASE)

            return self.regex_cache[key]

        except Exception as e:
            self.log_error(f"Error in get_regex_include_exclude: {e}")
            return self.regex_cache

    def apply_criteria(
        self, df, section_name, criteria_item,
        parent_mask=None, output_file="output.txt", level=1
    ):
        """
        Applies a single classification criterion (and any subcriteria) to standardize accounts and descriptions.

        This function filters the DataFrame using a logical set of rules (criteria tree), assigns standard
        account/description values to matching rows, and recursively applies subcriteria where needed.

        Parameters:
            df (pd.DataFrame): The DataFrame to filter and annotate.
            section_name (str): Name of the financial section being processed.
            criteria_item (dict): A single criterion node with filters and optional sub_criteria.
            parent_mask (pd.Series, optional): Boolean mask inherited from a parent criteria. Defaults to all True.
            output_file (str): Path for optional debug output (not currently used).
            level (int): Tree depth level, used for recursive control or indentation. Defaults to 1.

        Returns:
            Tuple: (Modified DataFrame, section_name, standardized_account, standardized_description)
        """
        target = criteria_item["target_line"]
        filters = criteria_item["criteria"]
        sub_criteria = criteria_item.get("sub_criteria", [])

        df = df.reset_index(drop=True)  # Reset index to prevent alignment errors

        # Run with a base mask (True for all rows) or refine from parent
        mask = parent_mask.copy() if parent_mask is not None else pd.Series(True, index=df.index)

        # Optimize: Merge multiple filters on same column (e.g., multiple contains_any)
        combined_filters = []
        seen_col = {}

        for col, cond, val in filters:
            # Normalize value to list when needed
            if cond in {"contains_any", "contains_none", "contains_all", "not_contains", "not_contains_all"}:
                if not isinstance(val, list):
                    val = [val]

            # Attempt to merge filters applied to the same column
            if col in seen_col:
                prev_idx = seen_col[col]
                prev_col, prev_cond, prev_val = combined_filters[prev_idx]

                # Merge: contains_any + contains_any
                if prev_cond == "contains_any" and cond == "contains_any":
                    prev_list = prev_val if isinstance(prev_val, list) else [prev_val]
                    new_list = prev_list + val
                    combined_filters[prev_idx] = (col, "contains_any", list({v.lower() for v in new_list}))
                    continue

                # Merge: contains_none + contains_none
                if prev_cond == "contains_none" and cond == "contains_none":
                    prev_list = prev_val if isinstance(prev_val, list) else [prev_val]
                    new_list = prev_list + val
                    combined_filters[prev_idx] = (col, "contains_none", list({v.lower() for v in new_list}))
                    continue

                # Combine one positive + one negative on same column
                pos_conds = {"contains_any", "contains_all"}
                neg_conds = {"contains_none", "not_contains"}
                if (prev_cond in pos_conds and cond in neg_conds) or (prev_cond in neg_conds and cond in pos_conds):
                    includes = prev_val if prev_cond in pos_conds else val
                    excludes = val if prev_cond in pos_conds else prev_val
                    require_all = prev_cond == "contains_all" if prev_cond in pos_conds else cond == "contains_all"
                    combined_filters[prev_idx] = (col, "combined_include_exclude", (includes, excludes, require_all))
                    continue

            # Add new filter to list
            seen_col[col] = len(combined_filters)
            combined_filters.append((col, cond, val))

        # Apply each compiled filter to refine the row mask
        for filter_col, filter_cond, filter_val in combined_filters:
            # Use cached lowercased column when available
            if filter_col in ("account", "description"):
                col_series = df[f"{filter_col}_lower"]
            else:
                col_series = df[filter_col].astype(str).str.lower().str.strip()

            # Vectorized condition matching
            if filter_cond == "equals":
                condition_mask = (col_series == str(filter_val).lower())
            elif filter_cond == "not_equals":
                condition_mask = (col_series != str(filter_val).lower())
            elif filter_cond == "startswith":
                condition_mask = col_series.str.startswith(str(filter_val).lower())
            elif filter_cond == "not_startswith":
                condition_mask = ~col_series.str.startswith(str(filter_val).lower())
            elif filter_cond == "endswith":
                condition_mask = col_series.str.endswith(str(filter_val).lower())
            elif filter_cond == "not_endswith":
                condition_mask = ~col_series.str.endswith(str(filter_val).lower())
            elif filter_cond == "contains_any":
                regex = self.get_regex_union([v.lower() for v in filter_val])
                condition_mask = col_series.str.contains(regex, na=False)
            elif filter_cond == "contains_none":
                regex = self.get_regex_union([v.lower() for v in filter_val])
                condition_mask = ~col_series.str.contains(regex, na=False)
            elif filter_cond == "contains_all":
                regex = self.get_regex_all([v.lower() for v in filter_val])
                condition_mask = col_series.str.contains(regex, na=False)
            elif filter_cond in ("not_contains", "not_contains_all"):
                regex = self.get_regex_all([v.lower() for v in filter_val])
                condition_mask = ~col_series.str.contains(regex, na=False)
            elif filter_cond == "level":
                condition_mask = (df["account_level"] == int(filter_val))
            elif filter_cond == "combined_include_exclude":
                includes, excludes, require_all = filter_val
                regex = self.get_regex_include_exclude(
                    [v.lower() for v in includes], [w.lower() for w in excludes], require_all
                )
                condition_mask = col_series.str.contains(regex, na=False)
            else:
                raise ValueError(f"Unknown filter condition: {filter_cond}")

            # Update global mask
            mask &= condition_mask

            # Stop early if nothing matches
            if not mask.any():
                break

        # Ensure required columns exist before assignment
        for col in ("account_standard", "description_standard", "standard_criteria", "items_match"):
            if col not in df.columns:
                df[col] = ""

        # Assign standardized info to matched rows
        std_account, std_desc = target.split(" - ")
        df.loc[mask, "account_standard"] = std_account
        df.loc[mask, "description_standard"] = std_desc
        df.loc[mask, "standard_criteria"] = " | ".join(f"{c} {cond} {val}" for c, cond, val in filters)

        # Record exact matches for debugging
        if mask.any():
            matched_items = (
                df.loc[mask, ["account", "description"]]
                .drop_duplicates()
                .apply(lambda row: f"{row['account']} - {row['description']}", axis=1)
                .tolist()
            )
            df.loc[mask, "items_match"] = " | ".join(matched_items)

        # Recursively apply subcriteria on child-level accounts
        for sub in sub_criteria:
            parent_accounts = df.loc[mask, "account"].astype(str).unique()
            if len(parent_accounts) == 0:
                continue
            child_mask = df["account"].astype(str).str.startswith(tuple(parent_accounts))
            df, section_name, _, _ = self.apply_criteria(
                df, section_name, sub, parent_mask=child_mask, level=level + 1
            )

        return df, section_name, std_account, std_desc

    def apply_criteria_cached_alternative(
        self, df, section_name, criteria_item,
        parent_mask=None, output_file="output.txt", level=1
    ):
        """
        Applies a single classification criterion (and any subcriteria) to standardize accounts and descriptions.

        This function filters the DataFrame using a logical set of rules (criteria tree), assigns standard
        account/description values to matching rows, and recursively applies subcriteria where needed.

        Parameters:
            df (pd.DataFrame): The DataFrame to filter and annotate.
            section_name (str): Name of the financial section being processed.
            criteria_item (dict): A single criterion node with filters and optional sub_criteria.
            parent_mask (pd.Series, optional): Boolean mask inherited from a parent criteria. Defaults to all True.
            output_file (str): Path for optional debug output (not currently used).
            level (int): Tree depth level, used for recursive control or indentation. Defaults to 1.

        Returns:
            Tuple: (Modified DataFrame, section_name, standardized_account, standardized_description)
        """
        target = criteria_item["target_line"]
        filters = criteria_item["criteria"]
        sub_criteria = criteria_item.get("sub_criteria", [])

        df = df.reset_index(drop=True)  # Ensure consistent indexing
        account_str = df["account"].astype(str)  # Cache for reuse

        # Run with all rows or inherited parent mask
        mask = parent_mask.copy() if parent_mask is not None else pd.Series(True, index=df.index)

        # Merge filters efficiently when possible
        combined_filters = []
        seen_col = {}

        for col, cond, val in filters:
            if cond in {"contains_any", "contains_none", "contains_all", "not_contains", "not_contains_all"}:
                if not isinstance(val, list):
                    val = [val]
            if col in seen_col:
                prev_idx = seen_col[col]
                prev_col, prev_cond, prev_val = combined_filters[prev_idx]
                if prev_cond == "contains_any" and cond == "contains_any":
                    prev_list = prev_val if isinstance(prev_val, list) else [prev_val]
                    new_list = prev_list + val
                    combined_filters[prev_idx] = (col, "contains_any", list({v.lower() for v in new_list}))
                    continue
                if prev_cond == "contains_none" and cond == "contains_none":
                    prev_list = prev_val if isinstance(prev_val, list) else [prev_val]
                    new_list = prev_list + val
                    combined_filters[prev_idx] = (col, "contains_none", list({v.lower() for v in new_list}))
                    continue
                pos_conds = {"contains_any", "contains_all"}
                neg_conds = {"contains_none", "not_contains"}
                if (prev_cond in pos_conds and cond in neg_conds) or (prev_cond in neg_conds and cond in pos_conds):
                    includes = prev_val if prev_cond in pos_conds else val
                    excludes = val if prev_cond in pos_conds else prev_val
                    require_all = prev_cond == "contains_all" if prev_cond in pos_conds else cond == "contains_all"
                    combined_filters[prev_idx] = (col, "combined_include_exclude", (includes, excludes, require_all))
                    continue
            seen_col[col] = len(combined_filters)
            combined_filters.append((col, cond, val))

        for filter_col, filter_cond, filter_val in combined_filters:
            if filter_col in ("account", "description"):
                col_series = df[f"{filter_col}_lower"]
            else:
                col_series = df[filter_col].astype(str).str.lower().str.strip()

            if filter_cond == "equals":
                condition_mask = (col_series == str(filter_val).lower())
            elif filter_cond == "not_equals":
                condition_mask = (col_series != str(filter_val).lower())
            elif filter_cond == "startswith":
                condition_mask = col_series.str.startswith(str(filter_val).lower())
            elif filter_cond == "not_startswith":
                condition_mask = ~col_series.str.startswith(str(filter_val).lower())
            elif filter_cond == "endswith":
                condition_mask = col_series.str.endswith(str(filter_val).lower())
            elif filter_cond == "not_endswith":
                condition_mask = ~col_series.str.endswith(str(filter_val).lower())
            elif filter_cond == "contains_any":
                regex = self.get_regex_union([v.lower() for v in filter_val])
                condition_mask = col_series.str.contains(regex, na=False)
            elif filter_cond == "contains_none":
                regex = self.get_regex_union([v.lower() for v in filter_val])
                condition_mask = ~col_series.str.contains(regex, na=False)
            elif filter_cond == "contains_all":
                regex = self.get_regex_all([v.lower() for v in filter_val])
                condition_mask = col_series.str.contains(regex, na=False)
            elif filter_cond in ("not_contains", "not_contains_all"):
                regex = self.get_regex_all([v.lower() for v in filter_val])
                condition_mask = ~col_series.str.contains(regex, na=False)
            elif filter_cond == "level":
                condition_mask = (df["account_level"] == int(filter_val))
            elif filter_cond == "combined_include_exclude":
                includes, excludes, require_all = filter_val
                regex = self.get_regex_include_exclude(
                    [v.lower() for v in includes], [w.lower() for w in excludes], require_all
                )
                condition_mask = col_series.str.contains(regex, na=False)
            else:
                raise ValueError(f"Unknown filter condition: {filter_cond}")

            mask &= condition_mask
            if not mask.any():
                break

        for col in ("account_standard", "description_standard", "standard_criteria", "items_match"):
            if col not in df.columns:
                df[col] = ""

        std_account, std_desc = target.split(" - ")
        df.loc[mask, "account_standard"] = std_account
        df.loc[mask, "description_standard"] = std_desc
        df.loc[mask, "standard_criteria"] = " | ".join(f"{c} {cond} {val}" for c, cond, val in filters)

        if mask.any():
            matched_items = (
                df.loc[mask, ["account", "description"]]
                .drop_duplicates()
                .apply(lambda row: f"{row['account']} - {row['description']}", axis=1)
                .tolist()
            )
            df.loc[mask, "items_match"] = " | ".join(matched_items)

        # Reuse cached account strings for subcriteria filtering
        for sub in sub_criteria:
            parent_accounts = account_str[mask].unique()
            if len(parent_accounts) == 0:
                continue
            child_mask = account_str.str.startswith(tuple(parent_accounts))
            df, section_name, _, _ = self.apply_criteria(
                df, section_name, sub, parent_mask=child_mask, level=level + 1
            )

        return df, section_name, std_account, std_desc

    def _filter_newer_versions(self, df):
        """
        Keep only the most recent version of each financial statement entry.

        Groups the data by a unique financial statement signature
        (company, quarter, type, frame, account) and retains only the entry
        with the highest version value per group.

        Args:
            df (pd.DataFrame): DataFrame containing raw or partially processed financial statement records.

        Returns:
            tuple:
                - pd.DataFrame: Only the newest records for each group.
                - pd.DataFrame: All non-kept (older) records.
                - pd.DataFrame: Duplicate groups with conflicting versions.
        """
        group_columns = ["company_name", "quarter", "type", "frame", "account"]
        version_column = "version"

        try:
            # Sort by group keys, then by version descending (latest first)
            df_sorted = df.sort_values(
                by=group_columns + [version_column],
                ascending=[True] * len(group_columns) + [False]
            )

            # Drop duplicate keys, keeping only the highest version per group
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep="first")

            # Identify the non-latest entries
            mask_other = ~df_sorted.index.isin(df_filtered.index)
            df_older = df_sorted[mask_other]

            # Identify groups that have conflicting versions (but not full duplicates)
            df_duplicates = df_sorted[
                df_sorted.duplicated(subset=group_columns, keep=False)
                & ~df_sorted.duplicated(subset=group_columns + [version_column], keep=False)
            ]

            return df_filtered, df_older, df_duplicates

        except Exception as e:
            # Log error and return empty structured DataFrames for safe fallback
            self.log_error(f"Error during filtering newer versions: {e}")
            columns, dtypes, primary_keys = self._get_table_structure(
                table_name=self.tbl_statements_raw,
                db_filepath=self.db_filepath
            )
            return pd.DataFrame(columns=columns), pd.DataFrame(columns=columns)

    def _pivot_and_adjust(self, df, target, tipo, index_cols, merge_cols):
        """
        Pivot quarterly values into wide format, apply period-specific transformations,
        and return the result back in long format with preserved metadata.

        This method supports two transformation types:
        - "year_end": Adjust Q4 by subtracting the sum of Q1–Q3 from December.
        - "cumulative": Convert cumulative Q2–Q4 into incremental quarterly values.

        Parameters:
            df (pd.DataFrame): Full DataFrame with original structure.
            target (pd.DataFrame): Subset of `df` matching a specific account type.
            tipo (str): Either "year_end" or "cumulative", defines the transformation rule.
            index_cols (list[str]): List of index columns for pivoting.
            merge_cols (list[str]): Columns used to align back the adjusted results.

        Returns:
            pd.DataFrame: Melted (long format) DataFrame with adjusted 'value' column
                          and merged original metadata (e.g. NSD, version, etc).
        """
        try:
            # Pivot to wide format with columns for each quarter number
            pivot = (
                target.pivot_table(
                    index=index_cols,
                    columns="quarter_num",
                    values="value",
                    aggfunc="first",
                )
                .reset_index()
                .fillna(0)  # Fill missing quarter values with 0
            )

            # Figure out which quarters really got pivoted
            quarter_cols = [c for c in pivot.columns if isinstance(c, int)]

            if tipo == "year_end":
                # Only touch Q4 if Q1, Q2 and Q3 were all there
                if 4 in quarter_cols and all(q in quarter_cols for q in (1, 2, 3)):
                    pivot[4] = pivot[4] - pivot[1] - pivot[2] - pivot[3]

            elif tipo == "cumulative":
                # For each quarter N = 2,3,4: only rewite pivot[N] if 1..N-1 are present
                for q in (2, 3, 4):
                    prev = list(range(1, q))
                    if q in quarter_cols and all(p in quarter_cols for p in prev):
                        pivot[q] = pivot[q] - sum(pivot[p] for p in prev)

            # figure out which of 1–4 actually landed in your pivot
            value_quarters = [q for q in (1, 2, 3, 4) if q in pivot.columns]

            # if nothing to melt, return empty (or handle as you wish)
            if not value_quarters:
                return pd.DataFrame(columns=merge_cols + index_cols + ["quarter_num", "value"])

            # melt only the present quarters
            melted = pivot.melt(
                id_vars=index_cols,
                value_vars=value_quarters,
                var_name="quarter_num",
                value_name="value",
            )

            # Identify additional columns to preserve (metadata, e.g. nsd, version)
            other_cols = [c for c in df.columns if c not in merge_cols]

            # Extract distinct metadata rows based on merge key
            df_temp = df[merge_cols + other_cols].drop_duplicates(subset=merge_cols)

            # Merge metadata back to adjusted values
            melted = (
                melted.merge(
                    df_temp,
                    on=merge_cols,
                    how="left",
                    suffixes=("", "_original"),
                )
                .drop_duplicates(subset=merge_cols)
            )

            # Drop rows where NSD is fully missing — should not be kept
            melted = melted.dropna(subset=["nsd"], how="all")

            return melted

        except Exception as e:
            self.log_error(f"Error during pivot_and_adjust ({tipo}): {e}")
            return pd.DataFrame(columns=merge_cols + ["value"])  # Safe fallback

    def _transform_quarterly_values(self, df):
        """
        Apply B3 quarterly-value adjustments.

        • Prefix **03 / 04** (income-statement): December is cumulative; derive Q4 by
        subtracting Q1–Q3 (“year_end” logic).

        • Prefix **06 / 07** (cash-flow): each quarter after Q1 is converted from
        cumulative to single-period value (“cumulative” logic).

        Original dates are preserved; only the numeric “value” column is updated.
        """
        index_cols = ["company_name", "type", "frame", "account", "year"]
        merge_cols = index_cols + ["quarter_num"]

        try:
            # Work on a copy to avoid side effects
            df = df.copy()

            # Derive year and quarter number from the 'quarter' date column
            df["quarter"] = pd.to_datetime(df["quarter"])
            df["year"] = df["quarter"].dt.year
            df["quarter_num"] = df["quarter"].dt.quarter

            # Guarantee numeric dtype for arithmetic operations
            df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

            # Normalize account code and capture its prefix
            df["account"] = df["account"].astype(str).str.strip()
            df["account_prefix"] = df["account"].str.split(".").str[0]

            # Keep only the latest NSD for each unique quarterly key
            df = (
                df.sort_values("nsd")
                .drop_duplicates(subset=merge_cols, keep="last")
            )

            # Log any surviving duplicates for offline inspection
            dup = df[df.duplicated(subset=merge_cols, keep=False)]
            if not dup.empty:
                self.log_error(f"{len(dup)} rows duplicated in quarterly index")
                filename = "rows_duplicated_in_quarterly_index.csv"
                temp_path = os.path.join(self.config.paths["temp_folder"], filename)
                dup.groupby(merge_cols).size().to_csv(temp_path)

            # Loop through account prefix groups and apply their specific adjustment rules
            for prefix, tipo in [(("03", "04"), "year_end"), (("06", "07"), "cumulative")]:
                
                # Filter only the rows matching the current account prefix group
                target = df[df["account_prefix"].isin(prefix)]
                
                # Proceed only if there's data to transform
                if not target.empty:
                    
                    # Transform the quarterly values based on the account type rule
                    transformed = self._pivot_and_adjust(df, target, tipo, index_cols, merge_cols)

                    # Extract adjusted values and align them by index for merging
                    adjusted = (
                        transformed.set_index(merge_cols)["value"]
                                .rename("adjusted_value")
                    )

                    # Replace original values with adjusted ones where available
                    df = df.set_index(merge_cols)
                    df["value"] = adjusted.combine_first(df["value"])
                    df = df.reset_index()

            # Remove helper columns
            df.drop(
                columns=["account_prefix", "year", "quarter_num"],
                inplace=True,
                errors="ignore",
            )

            return df

        except Exception as e:
            self.log_error(f"Erro ao transformar valores trimestrais: {e}")
            return df

    def adjust_columns(self, df0):
        """
        Final cleanup of financial statement data columns.

        This method standardizes column names and structure by:
        1. Removing rows without valid standardized accounts.
        2. Dropping original raw fields no longer needed.
        3. Renaming standardized columns to final names.
        4. Reordering columns according to schema.
        5. Sorting rows based on the canonical sort order.

        Parameters:
            df0 (pd.DataFrame): Raw or semi-processed DataFrame.

        Returns:
            pd.DataFrame: Cleaned and structured DataFrame ready for saving or further use.
        """
        try:
            # Drop rows where 'account_standard' is missing or blank
            df = df0.dropna(subset=["account_standard"])
            df = df[df["account_standard"].str.strip() != ""]

            # Drop unneeded original raw columns
            df = df.drop(columns=["account", "description"])

            # Rename standardized fields to final column names
            df = df.rename(columns={
                "account_standard": "account",
                "description_standard": "description"
            })

            # Reorder DataFrame columns according to project schema
            df = df[self.config.domain["statements_columns"]]

            # Sort rows to ensure consistent order
            df = df.sort_values(by=self.config.domain["statements_order"])

        except Exception as e:
            self.log_error(f"Error in adjust_columns: {e}")

        return df

    def get_targets_old(self, use_index=True, process_new=True, limit=False, max_retries=None, wait_time=None):
        """
        Retrieve financial statement records from the raw table that are missing in the normalized table.

        This function queries `tbl_statements_raw` for new or updated rows that do not yet exist
        in `tbl_statements_normalized`, based on primary key fields. It supports batched loading with
        retry logic for locked SQLite databases.

        Parameters:
            use_index (bool): Whether to use an indexed join for better performance.
            process_new (bool): If True, excludes rows that have already been processed (same version).
            limit (bool): If True, limits number of rows fetched (used for testing/debug).
            max_retries (int, optional): Max retry attempts in case of database lock. Defaults from config.
            wait_time (float, optional): Time to wait between retries. Defaults to dynamic sleep config.

        Returns:
            pd.DataFrame: A DataFrame with rows to process, or an empty DataFrame if no work is needed.
        """
        try:
            # Run retry configuration from fallback values or system config
            max_retries = max_retries or self.config.selenium["max_retries"]
            wait_time = wait_time or self.dynamic_sleep()

            # Construct SQL ON clause from primary keys for EXISTS subquery
            on_conditions = " AND ".join([f"r.{col} = n.{col}" for col in self.primary_key_columns])

            # Build base SQL to select all rows from the raw table (r)
            # that do NOT have a matching row in the normalized table (n),
            # based on primary key fields. This identifies unprocessed or new data.
            query_base = f"""
            FROM {self.tbl_statements_raw} AS r
            {f"INDEXED BY {self.idx_statements_raw}" if use_index else ""}
            WHERE NOT EXISTS (
                SELECT 1 FROM {self.tbl_statements_normalized} AS n
                WHERE {on_conditions}
            )
            """

            # Exclude already-processed records unless explicitly requested
            if process_new:
                query_base += " AND (r.processed IS NULL OR r.processed <> r.version)"

            # Optional row limit for testing or quick runs
            limit = False
            limit_rows = 100000
            limit_clause = f"LIMIT {limit_rows}" if limit else ""

            # Final composed queries
            query = f"SELECT r.* {query_base}"
            if limit:
                query += f" LIMIT {limit_rows};"
            else:
                query += ";"
            query_count = f"SELECT COUNT(*) {query_base};"

            # Set chunk size for loading in batches
            chunk_size = int(self.config.scraping["chunk_size"] / 10)

            df_list = []
            attempts = 0

            print("should use load_data!!!! adjust")  # TODO: Replace with self.load_data or remove

            # Retry loop for SQLite lock handling
            while attempts < max_retries:
                with self.db_lock:  # Ensure safe multi-threaded DB access
                    try:
                        with sqlite3.connect(self.db_filepath) as conn:
                            if not limit:
                                # Count total rows to fetch
                                total_rows = pd.read_sql_query(query_count, conn).iloc[0, 0]
                            else:
                                total_rows = limit_rows

                            if total_rows == 0:
                                return pd.DataFrame()  # No rows to process

                            # Run rows in chunks with progress bar
                            with tqdm(total=total_rows, unit="rows", desc="") as pbar:
                                for chunk in pd.read_sql_query(query, conn, chunksize=chunk_size):
                                    df_list.append(chunk)
                                    pbar.update(len(chunk))  # Update progress

                            # Concatenate all chunks into one DataFrame
                            df = pd.concat(df_list, ignore_index=True)
                        return df

                    except sqlite3.OperationalError as e:
                        if "database is locked" in str(e):
                            # Wait and retry if the database is locked
                            attempts += 1
                            time.sleep(wait_time)
                        else:
                            raise  # Reraise unexpected database errors

            # Raise error if retries exhausted
            raise Exception(f"Failed to fetch new records after {max_retries} attempts.")

        except Exception as e:
            self.log_error(e)

    def get_targets_old2(
        self,
        use_index: bool = True,
        process_new: bool = True,
        limit: bool = False,
        max_retries: int | None = None,
        wait_time: float | None = None
    ) -> pd.DataFrame:
        """
        Retrieve rows from `tbl_statements_raw` that are not yet in `tbl_statements_normalized`.

        Constructs a NOT EXISTS query on the primary key fields to find new or updated records.
        Delegates actual data loading to `self.load_data`, which handles batching, retries, and
        optional multithreading.

        Parameters:
            use_index (bool): Whether to hint SQLite to use the raw-table index for speed.
            process_new (bool): If True, excludes rows whose 'processed' flag equals their 'version'.
            limit (bool): If True, restricts returned rows to a fixed debug size (100_000).
            max_retries (int | None): Max attempts on DB lock; defaults to selenium.max_retries.
            wait_time (float | None): Seconds to wait between retry attempts; defaults to dynamic sleep.

        Returns:
            pd.DataFrame: DataFrame of new or updated raw-statement rows. Empty if none found.
        """
        try:
            # Determine retry parameters
            max_retries = max_retries or self.config.selenium["max_retries"]
            wait_time   = wait_time   or self.dynamic_sleep()

            # Build ON conditions for matching primary-key columns
            on_conditions = " AND ".join(
                f"r.{col} = n.{col}" for col in self.primary_key_columns
            )

            # Compose the common FROM/WHERE clause
            base_where = f"""
                FROM {self.tbl_statements_raw} AS r
                {'INDEXED BY ' + self.idx_statements_raw if use_index else ''}
                WHERE NOT EXISTS (
                    SELECT 1 FROM {self.tbl_statements_normalized} AS n
                    WHERE {on_conditions}
                )
            """
            # Exclude already-processed rows when requested
            if process_new:
                base_where += " AND (r.processed IS NULL OR r.processed <> r.version)"

            # Assemble full SELECT query with optional LIMIT
            sql = f"SELECT r.* {base_where}"
            if limit:
                sql += " LIMIT 100000;"
            else:
                sql += ";"

            # load_data handles chunking, multithreading, progress bar, and retries.
            df = self.load_data(
                query=sql,
                multi_thread=True,
                max_retries=max_retries,
                alert=False
            )

            return df

        except Exception as e:
            # Log and return empty DataFrame on unexpected errors
            self.log_error(f"Error in get_targets: {e}")
            return pd.DataFrame()

    def get_targets(self, targets) -> pd.DataFrame:
        try:
            if targets.empty:
                return targets

            batch_size = self.config.scraping.get("batch_size", 100) // 10 # fallback caso não exista

            # Garante que 'year' está disponível
            targets = targets.copy()
            targets["quarter"] = pd.to_datetime(targets["quarter"], errors="coerce")
            targets["year"] = targets["quarter"].dt.year

            # Obtenha os pares únicos (company_name, year) do targets atual
            pairs = targets[["company_name", "year"]].drop_duplicates().reset_index(drop=True)
            batches = [pairs[i:i + batch_size] for i in range(0, len(pairs), batch_size)]

            results = []

            for batch in batches:
                filters = " OR ".join(
                    f"(company_name = '{row.company_name}' AND strftime('%Y', quarter) = '{row.year}')"
                    for _, row in batch.iterrows()
                )

                sql = f"""
                    SELECT *
                    FROM {self.tbl_statements_raw}
                    WHERE {filters}
                """

                df = self.load_data(query=sql, multi_thread=True)
                results.append(df)

            return pd.concat(results, ignore_index=True)

        except Exception as e:
            self.log_error(f"Erro ao estender targets por (company_name, year) com paginação: {e}")
            return targets

    def iter_statements_by_company(self, db_path: str):
        """
        Iterate over grouped raw financial statement records by company.

        This method yields company-level subsets of data from `tbl_statements_raw`,
        where each subset includes only rows that:
        - Have not yet been processed (`processed IS NULL`)
        - OR have a different version from the `processed` column

        Intended for use in batch or threaded processing pipelines that handle one
        company at a time.

        Parameters:
            db_path (str): Path to the SQLite database file.

        Yields:
            Tuple[str, list[sqlite3.Row], list[str]]: 
                - company_name (str)
                - list of unprocessed records (as sqlite3.Row)
                - list of column names (as str)
        """
        try:
            # Establish database connection with row access by column name
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            with self.profiling():
                # Query 1: Get distinct companies with records needing (re)processing
                query_companies = """
                    SELECT DISTINCT company_name
                    FROM tbl_statements_raw
                    WHERE processed IS NULL OR processed <> version
                    ORDER BY company_name
                """

            for row in cursor.execute(query_companies):
                company_name = row[0]

                with self.profiling():
                    # Query 2: Fetch only the raw rows needing processing for that company
                    query_data = """
                        SELECT *
                        FROM tbl_statements_raw
                        WHERE company_name = ?
                        AND (processed IS NULL OR processed <> version)
                    """
                    cursor2 = conn.cursor()
                    cursor2.execute(query_data, (company_name,))
                    statements = cursor2.fetchall()

                    # Extract column names for downstream DataFrame construction
                    columns = [desc[0] for desc in cursor2.description]

                    # Convert raw records into a DataFrame
                    pretargets = pd.DataFrame.from_records(statements, columns=columns)

                yield company_name, pretargets

            conn.close()

        except Exception as e:
            self.log_error(f"Error in iter_statements_by_company: {e}")

    def main(self, thread=True):
        """
        Orchestrates normalization of raw financial statements by company.

        Iterates over `tbl_statements_raw` entries that have not yet been normalized,
        grouped by company, and applies transformation logic (`run`) to each group.
        Normalized results are saved to `tbl_statements_normalized`.

        Parameters:
            thread (bool): Whether to run the processing in threaded mode.

        Returns:
            bool: Always returns True after execution, regardless of result count.
        """
        try:

            # dispara _initialize_table + executescript do schema pending_companies
            df_pending = self.load_data(
                table_name=self.tbl_pending_companies,
                db_filepath=self.db_filepath,
                multi_thread=False,
                alert=False
            )
            # df_pending estará vazio (ou com as empresas pendentes, se já existirem)
            total_companies = len(df_pending)

            # Iterator over only the companies with new/unprocessed statements
            statement_iterator = self.iter_statements_by_company(self.db_filepath)

            start_time = time.monotonic()
            for i, (company_name, pretargets) in enumerate(statement_iterator):
                with self.profiling():
                    targets = self.get_targets(pretargets)

                # Process the DataFrame using normalization logic (threaded if configured)
                result = self.run(
                    targets,
                    thread=thread,
                    module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__,
                    verbose=False
                )

                # Save processed rows to the normalized table
                if not result.empty:
                    self.save_to_db(
                        dataframe=result,
                        table_name=self.tbl_statements_normalized,
                        db_filepath=self.db_filepath,
                        alert=False
                    )

                # Log company-level progress
                extra_info = [f'{company_name} {len(result)} registros normalizados']
                self.print_info(i, total_companies, start_time, extra_info=extra_info)

            # Optimize SQLite database file after processing
            self.db_optimize(self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True

