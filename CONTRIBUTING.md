# Contributing to NOKAR

Thank you for your interest in contributing to **NOKAR – Fully Autonomous AI Assistant**! We welcome contributions from developers, researchers, designers, and open-source enthusiasts worldwide.

This document outlines the guidelines and best practices for contributing to the repository.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Local Development Setup](#local-development-setup)
- [Coding Guidelines](#coding-guidelines)
  - [Python Style & Standards](#python-style--standards)
  - [Commit Message Conventions](#commit-message-conventions)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Community & Contact](#community--contact)

---

## Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to **[info@obrixlabs.com](mailto:info@obrixlabs.com)**.

---

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates. When opening a new bug report:

1. Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
2. Clearly describe the issue, including expected vs. actual behavior.
3. Provide your operating system version, Python version, and hardware specifications.
4. Include minimal, reproducible steps or logs (ensure all API keys, email credentials, and private paths are redacted).

### Suggesting Enhancements

Have an idea for a new capability, tool integration, or UI improvement?

1. Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
2. Clearly describe the problem your feature solves and why it benefits users.
3. Outline how the feature should behave and any architectural considerations.

### Submitting Pull Requests

1. **Fork the repository** on GitHub: `https://github.com/anasraheemdev/nokar-fully-autonomous-ai-assistant`.
2. **Create a topic branch**: `git checkout -b feature/my-new-feature` or `git checkout -b fix/issue-123`.
3. **Keep changes focused**: One PR should address one specific feature or bug fix.
4. **Follow project conventions**: Adhere to PEP 8, write clean docstrings, and avoid unnecessary external dependencies.
5. **Add tests**: Verify your changes using `python tests/test_ui_features.py` or appropriate unit tests.
6. **Open a Pull Request**: Submit your PR with a descriptive title and summary referencing any related issues.

---

## Local Development Setup

### Prerequisites

- **Python**: Version 3.11, 3.12, or 3.13 (recommended: Python 3.11 or 3.12).
- **Git**: Installed and configured.
- **Operating System**: Windows 10/11 (native voice/shortcuts optimized), macOS, or Linux.
- **Microphone & Speakers**: Required for real-time duplex audio sessions.
- **Gemini API Key**: Free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### Step-by-Step Setup

1. **Clone your fork**:
   ```bash
   git clone https://github.com/<your-username>/nokar-fully-autonomous-ai-assistant.git
   cd nokar-fully-autonomous-ai-assistant
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # OS-aware setup (auto-skips platform-incompatible wheels)
   python setup.py

   # Or manual installation
   pip install -r requirements.txt
   ```

4. **Configure your environment**:
   ```bash
   # Copy the example environment template
   cp .env.example .env

   # Or configure config/api_keys.json on first GUI boot
   ```

5. **Run the assistant**:
   ```bash
   python main.py
   ```

---

## Coding Guidelines

### Python Style & Standards

- **PEP 8 Compliance**: Follow standard Python conventions (4-space indentation, descriptive naming).
- **Type Annotations**: Use Python type hints (`from typing import Optional, List, Dict, Any`) where possible.
- **Cross-Platform Safety**:
  - Always use `pathlib.Path` for file system paths.
  - Guard platform-specific imports (e.g. `ctypes.windll`, `win32gui`) with platform checks or `try/except ImportError`.
  - Avoid unencoded emojis in stdout prints on Windows consoles to prevent `UnicodeEncodeError`.
- **Secret Isolation**: Never commit API keys, email passwords, session cookies, or personal database files. Verify `.gitignore` rules before committing.

### Commit Message Conventions

We adhere to [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]
```

**Common types**:
- `feat`: A new feature or capability
- `fix`: A bug fix
- `docs`: Documentation updates
- `style`: Formatting, missing semicolons, white-space changes
- `refactor`: Code restructure without changing behavior
- `test`: Adding or correcting tests
- `chore`: Build scripts, dependencies, configuration

**Examples**:
- `feat(rag): add support for markdown chunking in vault`
- `fix(video): prevent audio drift during HLS stream playback`
- `docs(readme): add installation guide for macOS`

---

## Testing & Quality Assurance

Before submitting a Pull Request, run the integration and test suites:

```bash
# Run the UI and feature integration test suite
python tests/test_ui_features.py

# Verify clean startup import
python -c "import main; print('Main imports successfully')"
```

Ensure all 14 capability checks pass with a 100% success rate.

---

## Community & Contact

- **Maintainer**: Muhammad Anas Raheem ([@anasraheemdev](https://github.com/anasraheemdev))
- **Email**: [info@obrixlabs.com](mailto:info@obrixlabs.com)
- **Organization**: [Obrix Labs](https://obrixlabs.com)
- **WhatsApp Support**: [wa.me/923462440356](https://wa.me/923462440356)
- **LinkedIn**: [linkedin.com/in/anasraheem](https://www.linkedin.com/in/anasraheem/)
