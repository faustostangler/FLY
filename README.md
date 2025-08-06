# FLY

FLY (Financial Ledger Yearly) gathers financial documents from companies listed on the stock exchange.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the main pipeline:

```bash
python main.py
```

The CLI in [`presentation/cli.py`](presentation/cli.py) wires services and executes the data capture and processing flows. Configuration files live under [`infrastructure/config`](infrastructure/config).

## Deployment and Execution

### Local

Execute the application directly with `python main.py`.

### Container

A minimal container image can be built from the project root:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

```bash
docker build -t fly .
docker run --rm fly
```

### Cloud (Outline)

1. Build and push the container image to your registry.
2. Provision a database and set required environment variables.
3. Deploy the image to a cloud service such as AWS ECS, Azure Container Apps, or Google Cloud Run.

## Testing and Validation

Tests mirror the source layout under `tests/` with subfolders for `application`, `domain`, and `infrastructure`. Run all checks before committing:

```bash
ruff format .
ruff check . --fix
pydocstyle --convention=google .
docformatter --in-place --recursive .
pytest
```

## Documentation

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture and domain model reference.

## License

This project is licensed under the MIT License.

