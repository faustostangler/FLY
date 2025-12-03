import datetime
import os
import time
from threading import Lock

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils.base_processor import BaseProcessor


class NsdProcessor(BaseProcessor):
    """Processar dados de empresas."""

    def __init__(self):
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # params
        self.homepage_url = 'https://www.google.com'

        # size
        self.shared_total_bytes = {"total": 0, "threads": {}}
        self.shared_lock = Lock()
        self.total_bytes_transferred = 0
        self.thread_id = None
        self.total_block_time = 0

        # Initialize database and table names
        self.table_name = self.config.databases["raw"]["table"]["nsd"]
        self.db_filepath = self.config.databases["raw"]["filepath"]

    def process_instance(self, sub_batch, payload, verbose, progress):
        """Process a single batch by delegating to process_batch."""
        result = pd.DataFrame()

        try:
            print(
                f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} {100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
            )
            batch_processor = NsdProcessor()

            # Inject shared control
            batch_processor.shared_total_bytes = self.shared_total_bytes
            batch_processor.shared_lock = self.shared_lock
            batch_processor.thread_id = progress["thread_id"]  # <- inject thread_id

            # Delegate to process_batch for the actual batch processing
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, verbose, progress, benchmark_mode=False
            )

            # Show subtotal download size
            if self.shared_total_bytes and self.shared_lock and progress.get("thread_id") is not None:
                with self.shared_lock:
                    subtotal = self.shared_total_bytes["threads"].get(progress["thread_id"], 0)
                    print(f"Worker {progress['thread_id']} download: {self._format_bytes(subtotal)}")
            # Save result to database
            self.save_to_db(dataframe=result, table_name=self.table_name, db_filepath=self.db_filepath, alert=False)

        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")

        return result

    @BaseProcessor().profile_generator()
    def process_batch(self, sub_batch, payload, verbose, progress):
        """Process a batch of NSD data by scraping and extracting relevant
        information."""
        try:
            result = pd.DataFrame(columns=self.config.domain["columns_nsd"])
            dfs = []

            # start time
            start_time = time.monotonic()

            # Initialize batch size tracking
            if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                batch_start_bytes = self.shared_total_bytes["threads"].get(self.thread_id, 0)
            else:
                batch_start_bytes = self.total_bytes_transferred

            # create first scraper
            scraper = self._init_scraper(url=self.homepage_url)

            for i, (_, row) in enumerate(sub_batch.iterrows()):
                try:
                    nsd = row["nsd"]
                    # Fetch and process NSD details
                    nsd_data = self._fetch_nsd_html(nsd, scraper)
                    if nsd_data:
                        dfs.append(nsd_data)

                    # Track bytes transferred after this ticker
                    if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                        bytes_after = self.shared_total_bytes["threads"].get(self.thread_id, 0)
                    else:
                        bytes_after = self.total_bytes_transferred
                    bytes_this_item = bytes_after - batch_start_bytes
                    formatted_size = self._format_bytes(bytes_this_item)
                    batch_start_bytes = bytes_after  # Update for next item

                    batch = 1 # self.config.selenium['log_loop']
                    if i % batch == 0 or i == len(sub_batch) - 1:  # Always log last item too
                        # Log progress
                        actual_item = progress["batch_start"] + i + 1
                        total_items = progress["scrape_size"] + 0
                        worker_info = f"Worker {progress['thread_id']} {100 * actual_item / total_items:.02f}% ({actual_item+0}/{total_items})"
                        extra_info = [
                            worker_info,
                            nsd,
                            (nsd_data.get("sent_date").strftime("%Y-%m-%d %H:%M:%S") if nsd_data.get("sent_date") else ""),
                            nsd_data.get("nsd_type", ""),
                            nsd_data.get("company_name", ""),
                            (nsd_data.get("quarter").strftime("%Y-%m") if nsd_data.get("quarter") else ""),
                            f"({formatted_size})", 
                        ]
                        self.print_info(i, len(sub_batch), start_time, extra_info, indent_level=0)

                        # Save result to database
                        temp_df = pd.DataFrame(dfs, columns=self.config.domain["columns_nsd"])
                        self.save_to_db(dataframe=temp_df, table_name=self.table_name, db_filepath=self.db_filepath, alert=False)

                except Exception as e:
                    self.log_error(f"Error processing NSD {row['nsd']}: {e}")

            # Combine results into a DataFrame
            if dfs:
                result = pd.DataFrame(dfs, columns=self.config.domain["columns_nsd"])
        
        except Exception as e:
            self.log_error(e)

        return result

    def _generate_nsd_list(self, existing_nsd, retry=False):
        """"""
        nsd_range = list(range(1, 100))  # <- default se tudo falhar (100 primeiros NSDs)

        try:
            last_nsd = existing_nsd["nsd"].max()
            if pd.isna(last_nsd):  # Check if last_nsd is NaN
                last_nsd = 0

            existing_nsd = existing_nsd[
                existing_nsd["company_name"].notnull() & (existing_nsd["company_name"].str.strip() != "")
            ]

            now = datetime.datetime.now()
            max_date = existing_nsd["sent_date"].max() if not existing_nsd["sent_date"].isna().all() else now
            min_date = (
                existing_nsd["sent_date"].min()
                if not existing_nsd["sent_date"].isna().all()
                else datetime.datetime(2010, 1, 1)
            )
            total_nsds = existing_nsd["nsd"].count() if existing_nsd["nsd"].count() > 0 else 1

            if max_date.normalize() != pd.Timestamp(now).normalize():
                days_span = (max_date - min_date).days
                days_elapsed = (datetime.datetime.now() - max_date).days + 1 if max_date else 1
                daily_submission_estimate = total_nsds / days_span if days_span > 0 else 1
                estimated_new_nsds = (
                    int(daily_submission_estimate * days_elapsed * self.config.domain["safety_factor"]) + 1
                )
                future_nsds = list(range(last_nsd + 1, last_nsd + 1 + estimated_new_nsds))

            else:
                future_nsds = list(range(last_nsd + 1, last_nsd + 1 + self.config.scraping["batch_size"]))
        except Exception as e:
            pass

        # Handle missing NSDs (holes in past)
        all_possible = set(range(1, last_nsd + 1))
        existing_ids = set(existing_nsd["nsd"].dropna().astype(int))
        missing_nsds = list(sorted(all_possible - existing_ids))

        # Combine missing and future
        nsd_range = future_nsds + missing_nsds if retry else future_nsds

        targets = pd.DataFrame({"nsd": list(nsd_range)})

        return targets

    def _fetch_nsd_html(self, nsd, scraper=None):
        """Fetch and parse NSD data for a given NSD value."""
        result = {"nsd": nsd}  # Minimal data to prevent stopping the process

        if scraper is None:
            scraper = self._init_scraper()

        try:
            endpoint = f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"

            # Fire off the three requests, with automatic retry on blocks
            r1 = self._fetch_with_retry(scraper, endpoint)

            # Parse the response HTML
            html = r1.text

            # Create a file with nsd as the name
            file_path = os.path.join(self.config.paths["temp_folder"], f"nsd_{nsd}.html")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html)

            result = self._parse_nsd_data(html, nsd)

        except Exception as e:
            self.log_error(f"Error fetching NSD {nsd}: {e}")

        return result

    def _parse_nsd_data(self, html, nsd):
        """Parse the HTML content to extract NSD data."""
        result = {}
        try:
            soup = BeautifulSoup(html, "html.parser")
            data = {"nsd": nsd}
            hash_value = soup.select_one("#hdnHash")["value"]

            # Define selectors for the required data
            selectors = {
                "company_name": "#lblNomeCompanhia",
                "dri": "#lblNomeDRI",
                "nsd_type_version": "#lblDescricaoCategoria",
                "auditor": "#lblAuditor",
                "responsible_auditor": "#lblResponsavelTecnico",
                "protocol": "#lblProtocolo",
                "quarter": "#lblDataDocumento",
                "sent_date": "#lblDataEnvio",
                "reason": "#lblMotivoCancelamentoReapresentacao",
            }

            for key, selector in selectors.items():
                element = soup.select_one(selector)
                if element:
                    data[key] = self.clean_text(element.text) if key not in ["sent_date", "quarter"] else element.text

            # Parse data information nsd_type, version, quarter and sent_date into datetime objects
            parts = data["nsd_type_version"].split()

            # Extract version, year, and nsd_type
            data["version"] = parts[-1]  # Last part
            year = parts[-2]  # Second last part
            data["nsd_type"] = " ".join(parts[:-2])  # Remaining parts joined

            if len(data["quarter"]) == 4:  # Only a year is provided
                # Assuming the last day of the year
                data["quarter"] = datetime.datetime.strptime(f"31/12/{data['quarter']}", "%d/%m/%Y")
            else:
                data["quarter"] = datetime.datetime.strptime(data["quarter"], "%d/%m/%Y")
            data["quarter"] = pd.to_datetime(data.get("quarter", None), format="%d/%m/%Y", errors="coerce")
            data["sent_date"] = pd.to_datetime(data.get("sent_date", None), format="%d/%m/%Y %H:%M:%S", errors="coerce")

            if data["sent_date"]:
                result = data

        except Exception:
            # self.log_error(f"Error parsing NSD {nsd}: {e}")
            pass

        return result

    def main(self, thread=True):
        """Main method to scrape NSD data, parse it, and save it to the
        database."""
        try:
            # download size
            shared_bytes = {"total": 0, "threads": {}}  # inclui total + subtotais por thread
            shared_lock = Lock()

            batch_processor = NsdProcessor()
            batch_processor.shared_total_bytes = shared_bytes
            batch_processor.shared_lock = shared_lock

            # Run existing NSD data
            existing_nsd = self.load_data(table_name=self.table_name, db_filepath=self.db_filepath)

            if not existing_nsd.empty:
                existing_nsd["sent_date"] = pd.to_datetime(
                    existing_nsd["sent_date"], format="%Y-%m-%dT%H:%M:%S", errors="coerce"
                )
                last_valid_index = existing_nsd.sort_values(by="sent_date", ascending=False).index[0]
                existing_nsd = existing_nsd.loc[:last_valid_index]

            targets = self._generate_nsd_list(existing_nsd)

            # Exit if no targets
            if targets.empty:
                self.db_optimize(self.config.databases["raw"]["filepath"])
                return True

            # Start processing (threaded or sequential)
            result = self.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            # Total Transfered
            if self.shared_total_bytes:
                total_mb = self.shared_total_bytes["total"]
                print(f'Total download: {self._format_bytes(total_mb)}')

            # Save processed data
            if not result.empty:
                self.save_to_db(dataframe=result, table_name=self.table_name, db_filepath=self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True

