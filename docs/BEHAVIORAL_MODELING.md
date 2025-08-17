# Behavioral Modeling

This document describes the runtime flow of key FLY use cases. Sequence diagrams
use PlantUML syntax and follow the Hexagonal Architecture layers
(Controller → Service → UseCase → Adapter/Repository).

## NSD Synchronization

```
@startuml
actor User
User -> CLIController : start()
CLIController -> NsdService : sync_nsd()
NsdService -> SyncNSDUseCase : synchronize_nsd()
SyncNSDUseCase -> NSDRepositoryPort : get_all_primary_keys()
SyncNSDUseCase -> NsdScraper : fetch_all(skip_codes, save_callback)
loop for each nsd
    NsdScraper -> FetchUtils : fetch_with_retry()
    alt block or timeout
        FetchUtils -> FetchUtils : create_scraper()/sleep
    end
    NsdScraper -> NsdScraper : _parse_html()
    NsdScraper -> SaveStrategy : handle(NsdDTO)
    alt threshold reached
        SaveStrategy -> NSDRepositoryPort : save_all(batch)
    end
end
SaveStrategy -> NSDRepositoryPort : save_all(remaining)
@enduml
```

1. **CLIController** builds dependencies and invokes `NsdService.sync_nsd()`.
2. **SyncNSDUseCase** collects existing NSD ids from the repository.
3. The **NsdScraper** iterates through sequential ids with the worker pool.
4. **FetchUtils.fetch_with_retry** retries on network errors or Cloudflare blocks,
   recreating the scraper session when needed.
5. Parsed pages become `NsdDTO` objects buffered by **SaveStrategy**.
6. Batches are persisted via `NSDRepositoryPort.save_all` until the worker pool
   finishes.

## Statement Fetching

```
@startuml
actor User
User -> CLIController : _statement_service()
CLIController -> StatementFetchService : fetch_statements()
StatementFetchService -> StatementFetchService : _build_targets()
StatementFetchService -> FetchStatementsUseCase : fetch_statement_rows(targets)
FetchStatementsUseCase -> FetchStatementsUseCase : fetch_all()
FetchStatementsUseCase -> WorkerPool : run(tasks, processor)
loop per NSD
    WorkerPool -> RawStatementScraperPort : fetch()
    alt no rows returned
        WorkerPool -> RawStatementScraperPort : fetch() retry
    end
    WorkerPool -> SaveStrategy : handle(rows)
    alt threshold reached
        SaveStrategy -> ParsedStatementRepositoryPort : save_all(batch)
    end
end
SaveStrategy -> ParsedStatementRepositoryPort : save_all(remaining)
@enduml
```

1. The controller builds repositories and `StatementFetchService`.
2. `_build_targets()` filters NSDs that have valid types and are missing
   statement rows.
3. **FetchStatementsUseCase.fetch_all** sets up a worker pool and `SaveStrategy`.
4. Each worker calls the `RawStatementScraperPort.fetch` method. Empty results
   trigger retries until rows are returned.
5. Fetched `StatementRowsDTO` objects are buffered and written in batches via the
   repository.

## Statement Parsing and Classification

```
@startuml
actor User
User -> CLIController : _statement_service()
CLIController -> StatementParseService : parse_statements(fetched)
StatementParseService -> WorkerPool : run(tasks, processor)
loop per statement row
    WorkerPool -> ParseAndClassifyStatementsUseCase : parse_and_store_row(row)
    ParseAndClassifyStatementsUseCase -> SaveStrategy : handle(dto)
    alt threshold reached
        SaveStrategy -> SqlAlchemyRawStatementRepository : save_all(batch)
    end
end
SaveStrategy -> SqlAlchemyRawStatementRepository : save_all(remaining)
ParseAndClassifyStatementsUseCase -> StatementParseService : finalize()
@enduml
```

1. After fetching rows, the controller invokes `StatementParseService.parse_statements()`.
2. A worker pool processes each raw row, calling
   `ParseAndClassifyStatementsUseCase.run`.
3. The use case converts a `StatementRowsDTO` to a `StatementDTO`, classifies the
   section, and buffers it through `SaveStrategy`.
4. Batches are saved using `SqlAlchemyRawStatementRepository.save_all`, and any remaining
   items flush during `finalize()`.

---

These flows highlight how processors, services and use cases collaborate across
layers and where retries or batching occur. DTOs travel from adapters to
repositories without leaking implementation details, preserving a clean
hexagonal structure.
