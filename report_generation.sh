#!/bin/bash
script_dir=$(dirname "${BASH_SOURCE[0]}")

cd "$script_dir"

source ./bin/activate

python report_generation.py --languages zh --skip-mongodb --industry $1 &

