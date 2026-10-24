# Contributing

Contributions are welcome. Keep pull requests focused and include tests for
behavior changes. Do not commit screenshots, API credentials, or other private
data.

## Development setup

Use Python 3.11 or newer, create a virtual environment, and install the project
with its development dependencies:

```shell
python -m pip install -e ".[dev]"
```

## Checks

Run the configured quality checks from the repository root:

```shell
ruff check .
mypy
pytest
```

CI runs these checks on Ubuntu and Windows. See `docs/architecture.md` and
`docs/providers.md` for implementation notes and provider setup/privacy.
