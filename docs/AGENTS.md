# Agent Instructions

This repository follows Hexagonal Architecture and uses typed DTOs. Refer to the documentation below for design details:

- `ARCHITECTURE.md` – layer responsibilities and dependency rules.
- `SCOPE.md` – features that are in and out of scope.
- `DTO_NAMING_CONVENTIONS.md` – rules for immutable transport objects.
- `LOGGING_CONTRACT.md` – how to emit logs using `Logger`.
- `WORKER_POOL.md` – guidelines for threaded execution.
- `COMPANY_DETAIL_PIPELINE.md` – overview of the company detail workflow.
- `code_style_manual.md` – general coding principles and naming rules.

## Development workflow

1. Create a virtual environment and install dependencies as shown in `README.md`.
2. Make your changes following the architecture and naming guidelines above.
3. Before committing, run the commands below and ensure they succeed:

   ```bash
   ruff format .
   ruff check . --fix
   pydocstyle --convention=google .
   docformatter --in-place --recursive .
   pytest
   ```

Only code that passes these checks should be committed.
