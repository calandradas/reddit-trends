#!/bin/bash
script_dir=$(dirname "${BASH_SOURCE[0]}")

source "$script_dir/bin/activate"

python "$script_dir/report_generation.py" --languages zh --skip-mongodb &

