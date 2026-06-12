$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python -m pytest tests/parity/static -q
