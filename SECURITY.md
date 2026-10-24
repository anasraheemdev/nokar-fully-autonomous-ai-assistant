# Security Policy

The NOKAR team and Obrix Labs take the security and privacy of our software and users seriously.

## Supported Versions

We provide security updates and critical patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability, security flaw, or potential credential exposure in NOKAR, please do **NOT** open a public issue on GitHub.

Instead, please report the issue privately to:

- **Security Contact**: Muhammad Anas Raheem
- **Email**: [info@obrixlabs.com](mailto:info@obrixlabs.com)
- **Alternative Contact**: [anasraheem@obrixlabs.com](mailto:anasraheem@obrixlabs.com)

### What to Include in Your Report

To help us triage and resolve the issue quickly, please provide:
1. A description of the vulnerability and its potential impact.
2. Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
3. Affected components (e.g. `core/gemini.py`, `actions/screen_processor.py`, `dashboard/`).
4. Any proposed remediations or patches.

### Response Timeline

- **Initial Acknowledgment**: Within 48 hours of report submission.
- **Triage & Status Update**: Within 5 business days.
- **Remediation & Patch Release**: Coordinated with the reporter before public disclosure.

---

## Local Privacy & Data Handling Guarantees

NOKAR is designed with a **privacy-first, local-first architecture**:

1. **Credentials Stay Local**:
   - All API keys, email passwords, and authentication tokens are stored locally on your machine in `config/api_keys.json` and are ignored by version control.
   - We strictly recommend never publishing your `config/` or `memory/` directories.

2. **No Centralized Telemetry**:
   - NOKAR does not connect to any central tracking servers or analytics backends.
   - All RAG knowledge bases, persistent vectors, and conversation logs remain stored exclusively in your local `memory/` directory.

3. **Duplex Audio Streaming**:
   - Audio input is only streamed to the Google Gemini Live endpoint while an active voice session is open or Push-to-Talk is engaged.
   - When muted or closed, microphone streams are fully terminated at the hardware level.

4. **Irreversible Confirmation Gate**:
   - Critical system-level commands (e.g., system shutdown, hardware restart, Wi-Fi toggling) require explicit human interaction on the UI confirmation banner and cannot be self-confirmed by the AI model.
