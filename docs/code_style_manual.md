# Code Style Manual

This project adopts a clean and sustainable code style, aligned with modern architecture principles and PEP 8 – Style Guide for Python Code.

---

## 1. General Principles

- Compose processor classes by responsibility (e.g., `EntryCleaner`, `DetailFetcher`, `CompanyDataMerger`).
- Favor the pipeline method pattern: `run()`, `load()`, `transform()`, and `persist()`.
- Write functions and methods that serve one purpose only.
- Inject all collaborators through constructors (e.g., `Logger`, `Scraper`, `Repository`).

---

## 2. Imports and Typing

- Follow this import order:
  1. Standard library
  2. Third-party libraries
  3. Local modules

- Use `@dataclass(frozen=True)` for all data objects passed between layers.
- Never pass raw dictionaries—use typed, immutable DTOs.

---

## 3. Naming

- Use `snake_case` for variables and functions.
- Use `CamelCase` for classes and domain vocabulary.
- Use `CAPITAL_SNAKE_CASE` only for module-level constants.
- Avoid abbreviations unless commonly accepted.

---

## 4. Docstrings and Comments

- Write docstrings using Google style.
- Comment relevant logic steps.
- Use blank lines to separate logical blocks inside functions.

---

## 5. Testing

- Use `pytest` with the `test_*.py` naming pattern.
- Place all tests under the `tests/` directory.
