#!/bin/bash

set -euo pipefail

# Accept the allowed licenses as the first argument
ALLOWED_LICENSES_INPUT="$1"

# Check if allowed_licenses input is provided
if [ -z "$ALLOWED_LICENSES_INPUT" ]; then
  echo "Error: 'allowed_licenses' input is required but not provided."
  exit 1
fi

# Convert the comma-separated string into an array and normalize
IFS=',' read -ra ALLOWED_LICENSES <<< "$ALLOWED_LICENSES_INPUT"

# Trim whitespace and convert to lowercase
for i in "${!ALLOWED_LICENSES[@]}"; do
  ALLOWED_LICENSES[$i]=$(echo "${ALLOWED_LICENSES[$i]}" | tr '[:upper:]' '[:lower:]' | xargs)
done

echo "Allowed Licenses:"
for license in "${ALLOWED_LICENSES[@]}"; do
  echo "- $license"
done

# Run Scancode to scan the codebase
echo "Running Scancode on /github/workspace..."
scancode --license --json-pp scan_results.json /github/workspace

echo "Scancode completed."

# Check if scan_results.json was created
if [ ! -f scan_results.json ]; then
  echo "Error: scan_results.json not found."
  exit 1
fi

# Extract the list of detected licenses
echo "Extracting detected licenses..."
LICENSE_DETECTIONS_COUNT=$(jq '.license_detections | length' scan_results.json)

if [ "$LICENSE_DETECTIONS_COUNT" -eq 0 ]; then
  echo "No licenses detected in the scanned files."
  exit 1  # Or adjust according to your policy
fi

jq -r '
  .license_detections[].license_expression |
  gsub("[()]"; "") |
  gsub(" AND "; " ") |
  gsub(" OR "; " ") |
  split(" ")[]' scan_results.json | tr '[:upper:]' '[:lower:]' | xargs -n1 > detected_licenses.txt

echo "Detected Licenses:"
cat detected_licenses.txt

# Ensure detected_licenses.txt is not empty
if [ ! -s detected_licenses.txt ]; then
  echo "No detected licenses found."
  exit 1  # Or adjust according to your policy
fi

# Compare detected licenses against allowed licenses
DISALLOWED_LICENSES=()

while read -r license; do
  license=$(echo "$license" | xargs)  # Trim whitespace
  license_found=false
  for allowed_license in "${ALLOWED_LICENSES[@]}"; do
    if [[ "$license" == "$allowed_license" ]]; then
      license_found=true
      break
    fi
  done
  if [ "$license_found" = false ]; then
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