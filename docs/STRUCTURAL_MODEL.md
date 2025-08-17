# Structural Model - FLY Project

This document summarizes the class relationships and dependencies in the FLY project according to the Hexagonal Architecture.

## Presentation Layer
- **CLI (`presentation/cli.py`)** – builds the object graph and triggers services.

## Application Layer
- **Services**
  - `CompanyDataService` – orchestrates company synchronization using `SyncCompanyDataUseCase`.
  - `NsdService` – orchestrates NSD synchronization via `SyncNSDUseCase`.
  - `StatementFetchService` – fetches raw statement pages with `FetchStatementsUseCase`.
  - `StatementParseService` – parses and persists rows using `ParseAndClassifyStatementsUseCase` and a `WorkerPool`.
  - `NsdPredictionService` – computes missing NSD numbers from repository data.
- **Use Cases**
  - `SyncCompanyDataUseCase` – fetches companies and saves them to the repository.
  - `SyncNSDUseCase` – downloads NSD documents and persists them.
  - `FetchStatementsUseCase` – retrieves raw statement rows concurrently.
  - `ParseAndClassifyStatementsUseCase` – converts rows to `StatementDTO` and persists them.
- **Mappers**
  - `CompanyDataMapper` – merges listing and detail DTOs using a `DataCleaner`.

Dependencies are injected through constructors and point inward to domain ports and DTOs.

## Domain Layer
- **DTOs** (`domain/dto`)
  - `CompanyDataDTO`, `CompanyDataRawDTO`, `CompanyDataListingDTO`, `CompanyDataDetailDTO`
  - `NsdDTO`
  - `StatementDTO`, `StatementRowsDTO`
  - `ExecutionResultDTO`, `PageResultDTO`, `MetricsDTO`, `SyncCompanyDataResultDTO`, `WorkerTaskDTO`
- **Ports** (`domain/ports`)
  - Repository ports: `SqlAlchemyCompanyDataRepositoryPort`, `NSDRepositoryPort`, `SqlAlchemyRawStatementRepository`, `ParsedStatementRepositoryPort`.
  - Source ports: `CompanyDataScraperPort`, `NSDSourcePort`, `RawStatementScraperPort`.
  - `LoggerPort`, `WorkerPoolPort`, `MetricsCollectorPort`, `DataCleanerPort`.
- **Utilities**
  - `statement_processing.classify_section` – maps account names to statement sections.

The domain contains no infrastructure references and consists only of dataclasses and protocols.

## Infrastructure Layer
- **Repositories** (`infrastructure/repositories`)
  - `SqlAlchemyCompanyDataRepository`, `SqlAlchemyNSDRepository`, `SqlAlchemyRawStatementRepository`, `SqlAlchemyParsedStatementRepositoryPort` – implement respective repository ports and manage database persistence using SQLAlchemy.
  - `SqlAlchemyRepositoryBase` – shared connection logic used by concrete repositories.
- **Scrapers & Adapters** (`infrastructure/scrapers`)
  - `CompanyDataScraper` – implements `CompanyDataScraperPort` using `FetchUtils`, `DataCleaner`, and several processor classes (`EntryCleaner`, `DetailFetcher`, `CompanyDataMerger`, `CompanyDataDetailProcessor`).
  - `NsdScraper` – implements `NSDSourcePort` and fetches sequential documents.
  - `StatementsSourceAdapter` – implements `RawStatementScraperPort` for statement pages.
- **Helpers** (`infrastructure/helpers`)
  - `FetchUtils` – HTTP fetching with retry logic.
  - `SaveStrategy` – buffers DTOs before persistence.
  - `WorkerPool` – thin wrapper over `ThreadPoolExecutor`.
  - `MetricsCollector`, `ByteFormatter`, `DataCleaner`, `TimeUtils`.
- **Logging** (`infrastructure/logging`)
  - `Logger` – emits structured logs.
  - `ProgressFormatter`, `ContextTracker`.
- **Configuration** (`infrastructure/config`)
  - `Config` – aggregates all configuration sections such as exchange endpoints and global settings.

Infrastructure classes depend only on interfaces defined in the domain/application layers.

## Example Constructor Signatures
```python
class CompanyDataService:
    def __init__(
        self,
        config: Config,
        logger: LoggerPort,
        repository: SqlAlchemyCompanyDataRepositoryPort,
        scraper: CompanyDataScraperPort,
    ) -> None:
        ...
```
```python
class SqlAlchemyCompanyDataRepository(SqlAlchemyCompanyDataRepositoryPort):
```

```python
class SqlAlchemyCompanyDataRepositoryPort(SqlAlchemyRepositoryBasePort[CompanyDataDTO, str]):
```

```python
class SqlAlchemyRepositoryBasePort(ABC, Generic[T, K]):
```
e também 

```python
class CompanyDataScraper(CompanyDataScraperPort):
```

```python
class CompanyDataScraperPort(BaseScraperPort[CompanyDataRawDTO]):
```

```python
class BaseScraperPort(ABC, Generic[T]):
```

Dependencies always point inward (scrapers depend on ports and helpers, services depend on use cases and ports).

## Layer Rules Verification
- Domain modules import only other domain modules.
- Application modules depend on domain DTOs and ports, not on infrastructure.
- Infrastructure implementations import domain ports to satisfy interfaces but never import application logic.
- Presentation layer imports services from application to start workflows.

This structure enables testing and swapping implementations while keeping business rules isolated in the domain.