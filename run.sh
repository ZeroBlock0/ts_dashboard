#!/bin/bash
echo "Syncing dependencies and running TS Dashboard..."
uv sync
uv run main.py
