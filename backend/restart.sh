#!/bin/bash
# Kill any existing uvicorn processes
pkill -f uvicorn

# Activate the virtual environment
source venv/bin/activate

# Start the server
uvicorn main:app --reload --port 8000 