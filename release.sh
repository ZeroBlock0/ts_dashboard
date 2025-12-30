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
git commit -m "Release v$VERSION"
git push origin main

git tag "v$VERSION"
git push origin "v$VERSION"

echo "Released v$VERSION"
