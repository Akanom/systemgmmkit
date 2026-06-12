$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python -m pytest tests/parity/gmm/test_system_gmm_certification.py -q
