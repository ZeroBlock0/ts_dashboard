#!/bin/bash

# Extract version from _version.py
VERSION=$(sed -n 's/__version__ = "\(.*\)"/\1/p' _version.py)

if [ -z "$VERSION" ]; then
  echo "Error: Could not extract version from _version.py"
  exit 1
fi

echo "Detected version: $VERSION"

# Update pyproject.toml
sed "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml

# Git operations
git add .
git commit -m "Release v$VERSION" || echo "Warning: Commit failed or nothing to commit. Continuing..."
git push origin main

if git tag "v$VERSION"; then
    git push origin "v$VERSION"
    echo "Released v$VERSION"
else
    echo ""
    echo "[ERROR] Tag v$VERSION already exists!"
    echo "Please update the version in _version.py before releasing."
    echo "The script will stop here to prevent triggering CI with old code."
    exit 1
fi
