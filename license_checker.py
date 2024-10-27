import ast
import os
import subprocess
import sys
import glob
import toml
import importlib.util
import re
import difflib


def is_builtin_module(module_name):
    """
    Check if a module is a built-in Python module or part of the standard library.
    importlib.util.find_spec is used to see if the module is available in the import system.
    If it's found and not in site-packages, we assume it's a standard library module.
    """
    try:
        # Try to find the module spec
        spec = importlib.util.find_spec(module_name)
        # If the module isn't found at all, skip it
        if spec is None:
            return False
        # Check if it's a built-in module (standard library)
        return spec.origin is None or 'site-packages' not in spec.origin
    except ModuleNotFoundError:
        # If module not found, it's likely a built-in or system module
        return True

def extract_imports_from_file(file_path):
    """Extracts imported libraries from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
    
    imported_packages = set()
    
    # Traverse through the AST and capture the import statements
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if not is_builtin_module(module_name):  # Skip built-in/standard modules
                    imported_packages.add(module_name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if not is_builtin_module(module_name):  # Skip built-in/standard modules
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
    pattern = os.path.join(directory, '*requirement*.txt')  # Match all files containing 'requirement'
    return glob.glob(pattern)


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
            if 'tool' in pyproject_data and 'poetry' in pyproject_data['tool']:
                poetry = pyproject_data['tool']['poetry']
                if 'dependencies' in poetry:
                    for package in poetry['dependencies']:
                        if package != "python":  # Skip python itself
                            dependencies.add(package)
                if 'dev-dependencies' in poetry:
                    for package in poetry['dev-dependencies']:
                        dependencies.add(package)
    return dependencies


def parse_poetry_lock(file_path):
    """Parses poetry.lock and extracts all locked dependencies."""
    dependencies = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            poetry_lock_data = toml.load(f)
            if 'package' in poetry_lock_data:
                for package in poetry_lock_data['package']:
                    dependencies.add(package['name'])
    return dependencies



def normalize_license_name(license_name):
    """
    Normalize the license name to improve comparison.
    This converts the license name to lowercase, strips unnecessary words like 'license',
    replaces different punctuation (slashes, commas), and standardizes common license names.
    """
    # Step 1: Convert to lowercase for case-insensitive matching
    normalized = license_name.lower()

    # Step 2: Remove the word 'license', 'version', 'v', and 'with' for simplicity
    normalized = re.sub(r'\blicense\b', '', normalized)
    normalized = re.sub(r'\bversion\b', '', normalized)
    normalized = re.sub(r'\bv\b', '', normalized)
    normalized = re.sub(r'\bwith\b', '', normalized)

    # Step 3: Replace punctuation variations (commas, slashes, and other special chars) with spaces or hyphens
    normalized = re.sub(r'[,/]', ' ', normalized)
    normalized = re.sub(r'[-_]', ' ', normalized)  # Treat hyphens and underscores as spaces
    normalized = re.sub(r'\s+', ' ', normalized)  # Replace multiple spaces with one space

    # Step 4: Remove common exceptions or extensions in licenses (e.g., "with Classpath exception")
    normalized = re.sub(r'with.*exception', '', normalized).strip()

    # Step 5: Standardize common license names to their SPDX identifiers
    known_licenses = {
        "mit": "MIT",
        "apache 2 0": "Apache-2.0",
        "apache license 2 0": "Apache-2.0",
        "apache license": "Apache-2.0",
        "bsd 3 clause": "BSD-3-Clause",
        "bsd 2 clause": "BSD-2-Clause",
        "gnu general public 2 0": "GPL-2.0",
        "gnu general public 3 0": "GPL-3.0",
        "gpl 2 0": "GPL-2.0",
        "gpl 3 0": "GPL-3.0",
        "gnu lesser general public 2 1": "LGPL-2.1",
        "gnu lesser general public 3 0": "LGPL-3.0",
        "lgpl 2 1": "LGPL-2.1",
        "lgpl 3 0": "LGPL-3.0",
        "agpl 3 0": "AGPL-3.0",
        "gnu affero general public 3 0": "AGPL-3.0",
        "mozilla public 2 0": "MPL-2.0",
        "mpl 2 0": "MPL-2.0",
        "eclipse public 2 0": "EPL-2.0",
        "epl 2 0": "EPL-2.0",
        "unlicense": "Unlicense",
        "cc0": "CC0-1.0",
        "creative commons zero": "CC0-1.0",
        "zlib": "Zlib",
        "artistic 2 0": "Artistic-2.0",
        "bsd 0 clause": "0BSD",
        "wtfpl": "WTFPL"
    }

    # Step 6: Normalize known licenses
    normalized = known_licenses.get(normalized.strip(), normalized.strip())

    # Step 7: Attempt fuzzy matching for unknown licenses
    if normalized not in known_licenses.values():
        closest_match = difflib.get_close_matches(normalized, known_licenses.values(), n=1)
        if closest_match:
            normalized = closest_match[0]  # Pick the closest match if available

    return normalized

def check_package_licenses(packages):
    """Uses pip-licenses to retrieve license information of packages."""
    valid_packages = set()
    
    # Step 1: Check which packages can be installed by simulating a dry-run
    result = subprocess.run(['pip', 'install', '--dry-run'] + list(packages), capture_output=True, text=True)
    
    # Only add packages that do not cause installation errors
    for package in packages:
        if package in result.stdout:
            valid_packages.add(package)
    
    if not valid_packages:
        print("No valid third-party packages found.")
        return {}
    
    # Install only valid third-party packages
    subprocess.run(['pip', 'install'] + list(valid_packages), check=False)
    
    # Step 2: Run pip-licenses to get license information
    result = subprocess.run(['pip-licenses', '--from=mixed'], capture_output=True, text=True)
    
    # Debugging: Print raw output from pip-licenses
    print("\nRaw License Output from pip-licenses:\n", result.stdout)

    licenses = {}
    
    # Step 3: Normalize the license names
    for line in result.stdout.splitlines()[2:]:  # Skip the header lines
        columns = line.split()
        package_name = columns[0]
        license_type = " ".join(columns[1:])  # Handle multi-word licenses
        normalized_license = normalize_license_name(license_type)
        
        # Debugging: Print raw and normalized license types
        print(f"Package: {package_name}, Raw License: {license_type}, Normalized License: {normalized_license}")
        
        licenses[package_name] = normalized_license
    
    return licenses


def check_compliance(licenses, allowed_licenses):
    """Checks if the package licenses comply with the allowed licenses."""
    non_compliant = []
    
    # Normalize the allowed licenses
    normalized_allowed_licenses = [normalize_license_name(lic) for lic in allowed_licenses]

    # Debugging: Print the normalized allowed licenses
    print(f"\nAllowed Licenses (Normalized): {normalized_allowed_licenses}\n")

    for package, license in licenses.items():
        if license not in normalized_allowed_licenses:
            non_compliant.append((package, license))
            # Debugging: Print non-compliant packages
            print(f"Non-compliant package found: {package} with license {license}")
    
    return non_compliant

def main():
    project_dir = '.'
    if len(sys.argv) > 1:
        allowed_licenses = sys.argv[1].split(',')
        
    else:
        allowed_licenses = ["MIT", "Apache-2.0", "BSD-3-Clause"]  # Default licenses

    # Step 1: Get imported packages from Python scripts
    detected_imports = scan_directory_for_imports(project_dir)

    # Step 2: Find all requirement-related files and read their dependencies
    requirements_files = find_requirements_files(project_dir)
    all_requirements = set()
    
    for req_file in requirements_files:
        all_requirements.update(read_requirements_file(req_file))

    # Step 3: Parse pyproject.toml if it exists
    pyproject_toml_path = os.path.join(project_dir, 'pyproject.toml')
    poetry_dependencies = parse_pyproject_toml(pyproject_toml_path)

    # Step 4: Parse poetry.lock if it exists
    poetry_lock_path = os.path.join(project_dir, 'poetry.lock')
    poetry_locked_dependencies = parse_poetry_lock(poetry_lock_path)

    # Combine all detected dependencies
    all_dependencies = detected_imports.union(all_requirements, poetry_dependencies, poetry_locked_dependencies)

    # Step 5: Check their licenses
    licenses = check_package_licenses(all_dependencies)

    # Step 6: Check license compliance
    non_compliant_packages = check_compliance(licenses, allowed_licenses)
    
    if non_compliant_packages:
        print("Non-compliant packages found:")
        for package, license in non_compliant_packages:
            print(f" - {package}: {license}")
        sys.exit(1)  # Fail the workflow if non-compliant packages are found
    else:
        print("All packages are compliant.")


if __name__ == "__main__":
    main()
    