# Automated License Compliance Checker
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-License%20Compliance%20Checker-blue?style=flat-square)](https://github.com/marketplace/actions/automated-license-check)

Scan your codebase for license compliance using Scancode Toolkit.

**automated-license-check** is a GitHub Action that helps you maintain license compliance across your projects effortlessly. Leveraging the powerful [Scancode Toolkit](https://github.com/aboutcode-org/scancode-toolkit), this action scans your codebase and its dependencies to detect all licenses present. It then compares the detected licenses against a list of allowed licenses you specify, and the workflow will fail if any disallowed licenses are found.



**Key Features:**
- **Customizable Allowed Licenses:** Specify a comma-separated list of allowed licenses based on your organization’s policies.
- **Comprehensive Scanning:** Detects licenses in both your code and dependencies, regardless of the programming language.
- **Automated Enforcement:** Integrates into your CI/CD pipeline to automatically enforce license compliance on every commit and pull request.
- **Clear Reporting:** Provides a detailed output of detected licenses and highlights any disallowed licenses for easy remediation.
- **Easy Integration:** Simple to set up with minimal configuration required.



## **Usage**

Add the following step to your workflow:

```yaml
- name: Run License Compliance Checker
  uses: soheilbr82/automated-license-check@v1
  with:
    allowed_licenses: "MIT, Apache-2.0, BSD-3-Clause"

```


## **Inputs**

- `allowed_licenses (optional)`: Comma-separated list of allowed licenses (e.g., "`MIT, Apache-2.0, BSD-3-Clause`"). 

## **Benefits**

- **Prevent Legal Risks:** Avoid potential legal issues by ensuring all code complies with your approved licenses.
- **Save Time and Resources:** Automate the manual process of license verification, allowing your team to focus on development.
- **Enhance Code Quality:** Maintain a clean codebase with approved and compatible licenses.


## **How It Works**

1. **Scan Codebase:** The action runs the Scancode Toolkit to analyze your repository for license information.
2. **Extract Licenses:** It extracts all detected licenses from the code and dependencies.
3. **Compare Licenses:** The detected licenses are compared against your specified list of allowed licenses.
4. **Report Results:** If disallowed licenses are found, the action fails and reports the disallowed licenses in the workflow logs.


## **Example Workflow File** 

```yaml
name: License Compliance Check

on: [push, pull_request]

jobs:
  license-scan:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Run License Compliance Checker
      uses: soheilbr82/automated-license-check@v1
      with:
        allowed_licenses: "MIT, Apache-2.0, BSD-3-Clause"


```


## **License**

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

**Full Changelog**: https://github.com/soheilbr82/automated-license-check/compare/v1.0.0...v1.0.0
