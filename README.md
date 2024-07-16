# Highwind

A Python SDK for [Highwind](https://highwind.ai/).

## Installation

The package is made available on the Python Package Index ([PyPI](https://pypi.org/)).

```sh
pip install highwind
```

## Usage and Current Features

### 1. Run Use Case inference

```py
from typing import Dict

from highwind import UseCase

use_case: UseCase = UseCase(id="a1...88") # You'll need to get this from the Highwind Web UI

use_case.name # 'IRIS Classifier'

inference_payload: Dict = {
    "inputs": [
        {
            "name": "input-0",
            "shape": [1],
            "datatype": "BYTES",
            "parameters": None,
            "data": [[6.1, 2.8, 4.7, 1.2]],
        }
    ]
}

result: Dict = use_case.run_inference(inference_payload)

print(result)
# {
#     "id": "c1958d66-27d0-403d-9ae4-45fb9f7dac8b",
#     "model_name": "c8uj6o4d",
#     "model_version": None,
#     "outputs": [
#         {
#             "data": [1],
#             "datatype": "INT64",
#             "name": "output-0",
#             "parameters": None,
#             "shape": [1],
#         }
#     ],
#     "parameters": None,
# }
```

## Full feature set

- [ ] Create an Asset and upload its files from your local machine
- [ ] Create a UseCase
- [ ] Search for all your Assets and get their UUIDs
- [ ] Link Assets to a UseCase
- [ ] Search for all your UseCases and get their UUIDs
- [ ] Deploy a UseCase
- [x] Run inference on a deployed UseCase
- [ ] Many more future features as Highwind develops

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

To build the package, simply bump the version number in `pyproject.toml`. Then run:

```sh
poetry build
```

This creates a new (gitignored) folder called `dist/` in the root of the project.

To publish the package to PyPI, simply run:

```sh
poetry publish
```
