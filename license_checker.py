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

def is_builtin_module(module_name):
    """Check if a module is a built-in Python module or part of the standard library."""
    try:
        spec = importlib.util.find_spec(module_name)
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

def find_requirements_files(directory):
    """Finds all text files that include the word 'requirement' in the filename."""
    return glob.glob(os.path.join(directory, '*requirement*.txt'))

def read_requirements_file(file_path):
    """Reads a requirements file and extracts package names."""
    requirements = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                package = line.strip().split('==')[0]
                if package and not package.startswith('#'):
                    requirements.add(package)
    return requirements

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

def normalize_license_name(license_name, spdx_licenses):
    """Normalize the license name to match SPDX identifiers."""
    normalized = license_name.lower()
    normalized = re.sub(r'\blicense\b|\bversion\b|\bv\b|\bwith\b', '', normalized)
    normalized = re.sub(r'[,/_-]', ' ', normalized).strip()

    print(f"Normalized license name: '{normalized}'")  # Debug print

    if normalized in spdx_licenses:
        return spdx_licenses[normalized]
    closest_match = difflib.get_close_matches(normalized, spdx_licenses.keys(), n=1)
    return spdx_licenses.get(closest_match[0], license_name) if closest_match else license_name

def check_package_licenses(packages, spdx_licenses):
    """Uses pip-licenses to retrieve license information of packages."""
    valid_packages = set()
    result = subprocess.run(['pip', 'install', '--dry-run'] + list(packages), capture_output=True, text=True)
    for package in packages:
        if package in result.stdout:
            valid_packages.add(package)
    if not valid_packages:
        print("No valid third-party packages found.")
        return {}

    subprocess.run(['pip', 'install'] + list(valid_packages), check=False)
    result = subprocess.run(['pip-licenses', '--from=mixed'], capture_output=True, text=True)

    licenses = {}
    for line in result.stdout.splitlines()[2:]:
        columns = line.split()
        package_name = columns[0]
        license_type = " ".join(columns[1:])
        licenses[package_name] = normalize_license_name(license_type, spdx_licenses)
    return licenses

def check_compliance(licenses, allowed_licenses):
    """Checks if the package licenses comply with the allowed licenses."""
    non_compliant = []
    normalized_allowed_licenses = [license.lower() for license in allowed_licenses]
    print(f"Allowed licenses (normalized): {normalized_allowed_licenses}")  # Debug print

    for package, license in licenses.items():
        print(f"Checking package: {package}, license: {license}")  # Debug print
        if license.lower() not in normalized_allowed_licenses:
            non_compliant.append((package, license))
            print(f"Non-compliant package found: {package} with license {license}")
    return non_compliant

def main():
    project_dir = '.'
    
    # Download SPDX license list if not present
    download_spdx_licenses()

    # Load the SPDX license list
    spdx_licenses = load_spdx_licenses()
    
    allowed_licenses = sys.argv[1].split(',') if len(sys.argv) > 1 else ["MIT", "Apache-2.0", "BSD-3-Clause"]

    detected_imports = scan_directory_for_imports(project_dir)
    requirements_files = find_requirements_files(project_dir)
    all_requirements = set().union(*[read_requirements_file(f) for f in requirements_files])
    poetry_dependencies = parse_pyproject_toml(os.path.join(project_dir, 'pyproject.toml'))
    poetry_locked_dependencies = parse_poetry_lock(os.path.join(project_dir, 'poetry.lock'))

    all_dependencies = detected_imports.union(all_requirements, poetry_dependencies, poetry_locked_dependencies)
    licenses = check_package_licenses(all_dependencies, spdx_licenses)
    non_compliant_packages = check_compliance(licenses, allowed_licenses)

    if non_compliant_packages:
        print("Non-compliant packages found:")
        for package, license in non_compliant_packages:
            print(f" - {package}: {license}")
        sys.exit(1)
    else:
        print("All packages are compliant.")

if __name__ == "__main__":
    main()