#!/bin/bash
script_dir=$(dirname "${BASH_SOURCE[0]}")

cd "$script_dir"

source ./bin/activate

python report_generation.py --languages en zh --skip-mongodb --push-to-notion --industry $1 &

