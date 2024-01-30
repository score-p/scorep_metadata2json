# scorep-metadata2json
A simple parser to convert Score-P Metadata to JSON

## Installation
```bash
git clone https://github.com/score-p/scorep_metadata2json.git
cd scorep_metadata2json
poetry install
```

## Usage
To use `scorep-metadata2json`, activate the project's virtual environment created by poetry:
```commandline
poetry shell
```
Now, you can run scorep_metadata2json directly:
```bash
scorep-metadata2json <path/to/scorep.fair>
``` 
Hint: Use data located in `test/test_data` for testing. 

Yoy can output the schema of the parser by using the `--schema` option:
```bash
scorep-metadata2json --schema
```
The schema as well as a visual representation is also available in the documentation of the basemodel. 

---
Alternatively, if you prefer not to activate the virtual environment, you can prefix your commands with `poetry run`:
```bash
poetry run scorep-metadata2json -h
```

Hint: Use `jq` to view the output formatted in color.
```bash
scorep-metadata2json <path/to/scorep.fair> | jq
```

## Documentation
To build the documentation, run:
```bash
poetry install --with docs
poetry run sphinx-build docs docs/_build
```
It can then be found in `docs/_build/index.html`.

## Development
To install the development dependencies, run:
```bash
poetry install --with dev
```
After that, run the following commands to check the code style and type annotations: 
```bash
poetry run mypy .
poetry run ruff .
poetry run ruff format . 
```

## Testing
To run the tests, run:
```bash
poetry run python -m unittest test/test_arg_parser.py
poetry run python -m unittest test/test_parser.py
```
