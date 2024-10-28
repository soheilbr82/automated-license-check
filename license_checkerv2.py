import json
import ast
import os
import subprocess
import sys
import glob
import toml
import importlib.util
import re
import difflib
import requests

def download_spdx_licenses(file_path="spdx_licenses.json"):
    """
    Download the SPDX license list JSON file if it doesn't already exist.
    """
    spdx_url = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
    
    if not os.path.exists(file_path):
        print("Downloading SPDX license list...")
        response = requests.get(spdx_url)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print("SPDX license list downloaded successfully.")
        else:
            print("Failed to download SPDX license list.")
            sys.exit(1)
    else:
        print("SPDX license list already exists.")

def load_spdx_licenses(file_path="spdx_licenses.json"):
    """Load the SPDX license list from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        spdx_data = json.load(f)
    return {license['licenseId'].lower(): license['name'] for license in spdx_data['licenses']}

def parse_pyproject_toml(file_path):
    """Parses pyproject.toml and extracts dependencies from the [tool.poetry.dependencies] section."""
    dependencies = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            pyproject_data = toml.load(f)
            poetry = pyproject_data.get('tool', {}).get('poetry', {})
            for section in ['dependencies', 'dev-dependencies']:
                dependencies.update({pkg for pkg in poetry.get(section, {}) if pkg != "python"})
    return dependencies

def parse_poetry_lock(file_path):
    """Parses poetry.lock and extracts all locked dependencies."""
    dependencies = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            poetry_lock_data = toml.load(f)
            dependencies.update({pkg['name'] for pkg in poetry_lock_data.get('package', [])})
    return dependencies

def is_builtin_module(module_name):
    """Check if a module is a built-in Python module or part of the standard library."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return True
        return spec.origin is None or 'site-packages' not in spec.origin
    except ModuleNotFoundError:
        return True

def extract_imports_from_file(file_path):
    """Extract imported libraries from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
    imported_packages = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if not is_builtin_module(module_name):
                    imported_packages.add(module_name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_name = node.module.split('.')[0]
            if not is_builtin_module(module_name):
                imported_packages.add(module_name)
    return imported_packages

def scan_directory_for_imports(directory):
    """Recursively scans all Python files for imported libraries."""
    all_imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_imports.update(extract_imports_from_file(file_path))
    return all_imports

def run_scancode(scan_output="scan_results.json", project_dir="."):
    """Run scancode-toolkit to scan the project directory."""
    scancode_command = [
        "./scancode",
        "--format", "json-pp",
        "--output", scan_output,
        project_dir
    ]
    result = subprocess.run(scancode_command, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to run scancode-toolkit.")
        print(result.stderr)
        sys.exit(1)

def check_compliance(scan_results, allowed_licenses):
    """Checks if the package licenses comply with the allowed licenses."""
    with open(scan_results, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    
    non_compliant = []
    for file in scan_data['files']:
        for license in file.get('licenses', []):
            license_id = license['spdx_license_key']
            if license_id and license_id.lower() not in allowed_licenses:
                non_compliant.append((file['path'], license_id))
    
    return non_compliant

def main():
    project_dir = '.'
    
    # Download SPDX license list if not present
    download_spdx_licenses()

    # Load the SPDX license list
    spdx_licenses = load_spdx_licenses()
    
    allowed_licenses = sys.argv[1].split(',') if len(sys.argv) > 1 else ["mit", "apache-2.0", "bsd-3-clause"]

    # Parse dependencies from pyproject.toml and poetry.lock
    pyproject_dependencies = parse_pyproject_toml(os.path.join(project_dir, 'pyproject.toml'))
    poetry_lock_dependencies = parse_poetry_lock(os.path.join(project_dir, 'poetry.lock'))

    # Scan imports from Python files
    imported_dependencies = scan_directory_for_imports(project_dir)

    # Combine all dependencies
    all_dependencies = pyproject_dependencies.union(poetry_lock_dependencies, imported_dependencies)

    # Run scancode-toolkit
    run_scancode()

    # Check compliance
    non_compliant_packages = check_compliance("scan_results.json", allowed_licenses)

    if non_compliant_packages:
        print("Non-compliant packages found:")
        for package, license in non_compliant_packages:
            print(f" - {package}: {license}")
        sys.exit(1)
    else:
        print("All packages are compliant.")

if __name__ == "__main__":
    main()