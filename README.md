# Automated License Compliance Checker
A GitHub Action to automatically scan and verify your Python project’s dependencies for license compliance. Checks requirements.txt, pyproject.toml, and code imports against a customizable list of approved licenses, flagging any non-compliant packages to help you maintain open-source license standards.


### Supported Licenses

This action recognizes a comprehensive range of open-source licenses, including commonly used ones such as:

- **Permissive Licenses**: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Zlib, Unlicense, CC0-1.0, and more.
- **Copyleft Licenses**: GPL-2.0, GPL-3.0, AGPL-3.0, EPL-2.0, and others.
- **Weak Copyleft Licenses**: LGPL-2.1, LGPL-3.0, MPL-2.0, and similar.
- **Creative Commons Licenses**: CC-BY-4.0, CC-BY-SA-4.0, and other content licenses.
- **Other Licenses**: Artistic-2.0, OFL-1.1, CECILL-2.1, EUPL-1.2, and more.

For full coverage, this action covers licenses listed in the [SPDX License List](https://spdx.org/licenses/).
You can download the latest SPDX licenses from [spdx/license-list-data](https://github.com/spdx/license-list-data) github repo.




[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-License%20Compliance%20Checker-blue?style=flat-square)](https://github.com/marketplace/actions/automated-license-check)

Scan your codebase for license compliance using Scancode Toolkit.

## **Usage**

Add the following step to your workflow:

```yaml
- name: Run License Compliance Checker
  uses: soheilbr82/automated-license-check@v1
  with:
    allowed_licenses: "MIT, Apache-2.0, BSD-3-Clause"
