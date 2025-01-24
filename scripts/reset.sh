#!/bin/sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

DEFAULT_CONFIG='{"users": ["u1", "u2"], "sheet_id": ""}'

> ./info/config.json
> ./info/credential.json

echo -e "$DEFAULT_CONFIG" >> ./info/config.json
