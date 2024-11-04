#!/bin/bash

set -euo pipefail

# Accept the allowed licenses as the first argument
ALLOWED_LICENSES_INPUT="$1"

# Check if allowed_licenses input is provided
if [ -z "$ALLOWED_LICENSES_INPUT" ]; then
  echo "Error: 'allowed_licenses' input is required but not provided."
  exit 1
fi

# Convert the comma-separated string into a sorted, unique list and normalize to lowercase
echo "$ALLOWED_LICENSES_INPUT" | tr '[:upper:]' '[:lower:]' | tr ',' '\n' | xargs -n1 | sort | uniq > allowed_licenses.txt

echo "Allowed Licenses:"
cat allowed_licenses.txt

# Run Scancode to scan the codebase
echo "Running Scancode on /github/workspace..."
scancode --license --json-pp scan_results.json /github/workspace

echo "Scancode completed."

# Check if scan_results.json was created
if [ ! -f scan_results.json ]; then
  echo "Error: scan_results.json not found."
  exit 1
fi

# Extract the list of detected licenses, normalize to lowercase, and ensure uniqueness
echo "Extracting detected licenses..."
LICENSE_DETECTIONS_COUNT=$(jq '.license_detections | length' scan_results.json)

if [ "$LICENSE_DETECTIONS_COUNT" -eq 0 ]; then
  echo "No licenses detected in the scanned files."
  exit 1
fi

jq -r '
  .license_detections[].license_expression |
  gsub("[()]"; "") |
  gsub(" AND "; " ") |
  gsub(" OR "; " ") |
  split(" ")[]' scan_results.json | tr '[:upper:]' '[:lower:]' | xargs -n1 | sort | uniq > detected_licenses.txt

echo "Detected Licenses:"
cat detected_licenses.txt

# Ensure detected_licenses.txt is not empty
if [ ! -s detected_licenses.txt ]; then
  echo "No detected licenses found."
  exit 1
fi

# Compare detected licenses against allowed licenses using 'comm'
# 'comm' requires both files to be sorted
DISALLOWED_LICENSES=$(comm -23 detected_licenses.txt allowed_licenses.txt)

if [ -n "$DISALLOWED_LICENSES" ]; then
  echo "Disallowed licenses found:"
  echo "$DISALLOWED_LICENSES"
  exit 1
else
  echo "All detected licenses are allowed."
fi