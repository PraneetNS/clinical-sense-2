#!/bin/bash
# Exit on error
set -e

echo "Build started..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Build finished."
