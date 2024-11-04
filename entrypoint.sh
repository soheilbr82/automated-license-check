#!/bin/bash
set -e

# Run ScanCode on the repository and generate a JSON report
/venv/bin/scancode --license --json-pp scan_results.json .

# Read allowed licenses from input or fallback file
if [ -n "$1" ]; then
    allowed_licenses=$(echo "$1" | tr ',' '\n')
else
    allowed_licenses=$(cat /app/allowed_licenses.txt)
fi

# Extract package licenses from ScanCode output
jq -r '.files[] | select(.packages) | .packages[] | "\(.name):\(.version):\(.licenses[].short_name)"' scan_results.json > dependency_licenses.txt

# Initialize flag for disallowed licenses
disallowed=0

# Check each dependency license against the allowed list
while IFS=: read -r name version license; do
    if ! echo "$allowed_licenses" | grep -qw "$license"; then
        echo "Disallowed license detected for $name ($version): $license"
        disallowed=1
    else
        echo "Allowed license for $name ($version): $license"
    fi
done < dependency_licenses.txt

# Set the action result
if [ $disallowed -eq 1 ]; then
    echo "::set-output name=result::fail"
    exit 1
else
    echo "::set-output name=result::pass"
fi