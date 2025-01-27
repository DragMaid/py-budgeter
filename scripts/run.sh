#!/bin/sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ./venv/bin/activate
python ./main.py --size=360x740 --dpi=529
