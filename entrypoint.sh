#!/bin/bash

set -e

# Accept the allowed licenses as the first argument
ALLOWED_LICENSES_INPUT="$1"

# Check if allowed_licenses input is provided
if [ -z "$ALLOWED_LICENSES_INPUT" ]; then
  echo "Error: 'allowed_licenses' input is required but not provided."
  exit 1
fi

# Convert the comma-separated string into an array
IFS=',' read -ra ALLOWED_LICENSES <<< "$ALLOWED_LICENSES_INPUT"

# Trim whitespace from each element
for i in "${!ALLOWED_LICENSES[@]}"; do
  ALLOWED_LICENSES[$i]=$(echo "${ALLOWED_LICENSES[$i]}" | xargs)
done

echo "Allowed Licenses: ${ALLOWED_LICENSES[@]}"

# Run Scancode to scan the codebase
scancode --license --json-pp scan_results.json /github/workspace

# Extract the list of detected licenses
jq -r '
  .license_detections[].license_expression |
  gsub("[()]"; "") |
  gsub(" AND "; " ") |
  gsub(" OR "; " ") |
  split(" ")[]' scan_results.json | sort | uniq > detected_licenses.txt

echo "Detected Licenses:"
cat detected_licenses.txt

# Compare detected licenses against allowed licenses
DISALLOWED_LICENSES=()

while read -r license; do
  if [[ ! " ${ALLOWED_LICENSES[@]} " =~ " ${license} " ]]; then
    DISALLOWED_LICENSES+=("$license")
  fi
done < detected_licenses.txt

if [ ${#DISALLOWED_LICENSES[@]} -ne 0 ]; then
  echo "Disallowed licenses found:"
  for license in "${DISALLOWED_LICENSES[@]}"; do
    echo "- $license"
  done
  exit 1
else
  echo "All detected licenses are allowed."
fi