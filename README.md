# Highwind Python

A Python SDK for [Highwind](https://highwind.ai/).

## Installation

TODO: DOCUMENT INSTALLATION

## Contributing

1. Fork the repository
2. Make your desired changes
3. Ensure adequate test coverage
4. Open a Pull Request

### Installing dependencies

We use [Poetry](https://python-poetry.org/), so install that first by following
[the official docs](https://python-poetry.org/docs/#installation).

Then run:

```sh
poetry install
```

We also use [pre-commit](https://pre-commit.com/), so install that too by following
[the official docs](https://pre-commit.com/#installation).

Then run:

```sh
pre-commit install
```

### Running tests

Simply run:

```sh
pytest
```

### Building and Publishing the SDK

To build the package, simply run:

```sh
poetry build
```

This creates a new (gitignored) folder called `dist/` in the root of the project.

To publish the package to PyPI, simply run:

```sh
poetry publish
```
