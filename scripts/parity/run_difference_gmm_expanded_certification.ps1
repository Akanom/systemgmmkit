$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python -m pytest tests/parity/gmm/test_difference_gmm_expanded_certification.py -q
