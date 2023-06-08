#!/bin/bash
set -e
poetry install
poetry run pre-commit install
echo -e "\e[1mProject has been setup successfully\e[0m"
poetry run uvicorn --app-dir ./src/ api:app --host=0.0.0.0 --port=${PORT:-5000}
