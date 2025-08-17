# CompanyData Detail Pipeline

The detail pipeline is triggered by `sync_companies.py` via `CompanyDataService`.

1. `CompanyDataScraper.fetch_all()` retrieves a list of companies and for each one:
   - `EntryCleaner` normalizes the listing entry.
   - `DetailFetcher` downloads the detail page and converts it to `CompanyDataDetailDTO`.
   - `CompanyDataMerger` merges listing and detail data into `CompanyDataRawDTO`.
2. The use case converts each `CompanyDataRawDTO` to `CompanyDataDTO` and calls the repository.
3. `SqlAlchemyCompanyDataRepository` persists the data with `insert_or_update` semantics.

All steps emit logs and accumulate metrics. Results are stored in the SQLite tables declared in `infrastructure/models`.
