#!/bin/bash
set -e

echo "Starting Graham script..."
python graham.py

echo "Starting MACD script..."
python macd.py

echo "All tasks completed."
