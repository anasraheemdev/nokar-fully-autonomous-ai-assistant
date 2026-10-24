# Changelog

All notable changes to the **NOKAR – Fully Autonomous AI Assistant** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-24

### Initial Production Release — NOKAR (Obrix Labs Edition)

This milestone release elevates NOKAR into a production-grade, fully autonomous AI desktop assistant, unifying agentic desktop automation, real-time voice duplexing, multimodal vision, and rich graphical HUD telemetry.

### Added

#### Interface & Visual HUD
- **Complete Next-Gen HUD Interface**: Frosted-glass cyber-minimalist design with high-definition rendering, responsive sidebar navigation, and multi-view stacking.
- **Floating Command Dock**: Centered action dock with dynamic mic pulse visualizer, real-time audio wave telemetry, and quick-action chips (`⚡ Quick Task`, `🔍 Search`, `🧠 Memory`, `👁 Screen`).
- **In-App Video Picture-in-Picture (PiP)**: Draggable 360×240 floating glass card (`VideoPipWidget`) enabling seamless video playback alongside the active, lip-synced 3D avatar.
- **System-Wide Quick Summon (Spotlight Bar)**: Translucent floating search/command bar summoned instantly via `F8` or `Alt+Space` with embedded mic toggle and quick actions.
- **Real-Time Telemetry Drawer**: Live CPU, RAM, GPU, and VRAM monitoring popovers with automated threshold alerting.

#### Artificial Intelligence & Models
- **Gemini Live Ultra-Low Latency Engine**: Native bidirectional streaming audio loop powered by Gemini Live for conversation without turn-taking delay.
- **Automated Model Ladder**: Resilient 9-model failover ladder with measured response ranking, automatic cooldowns for 429 quotas and 503/504 timeouts, eliminating hung API requests.
- **Session Continuity Protocol**: Reconnection handle tracking allowing seamless conversation resumption across network glitches and audio device toggles.

#### Autonomous Actions & Workflow Automation
- **Multimodal Screen Vision**: Foreground active window title awareness (`ctypes.windll.user32`) and full-screen visual inspection pipeline directly feeding into Gemini Live.
- **Proactive Autonomous Watchdog**: Dedicated background daemon (`core/proactive_watchdog.py`) continually monitoring unread email inboxes (Hostinger/IMAP), hardware spikes (>90% CPU/RAM), and milestone deadlines.
- **Local Codebase & Personal Document RAG (Vector Vault)**: Local vector and semantic retrieval engine (`core/rag_vault.py` & `actions/rag_vault_action.py`) supporting automatic background indexing of codebases, markdown files, PDFs, and text documents.
- **Antigravity IDE Automation**: Bidirectional workspace management, folder browsing, live agent PID status checking, and autonomous task prompt dispatch.
- **Irreversible Confirmation Safety Gate**: Hardware-level confirmation tokens for dangerous operations (shutdown, restart, WiFi toggle) that require explicit human approval and cannot be bypassed by model hallucination.
- **Universal Reversible Action (Undo) Stack**: Instant rollback support for file manipulations (copy, move, rename, delete) and system settings changes.

#### Audio & Hardware
- **Software Holographic Face Rendering**: 3D geometric mesh rendering derived from canonical facial topology without GPU requirements.
- **Acoustic Echo Guard**: Self-calibrating echo suppression ensuring the assistant never speaks over itself.
- **Intelligent Audio Device Enumeration**: Automatic device deduplication across MME, DirectSound, and WASAPI host APIs.

---

### Maintainers & Attribution
- **Founder & Lead Developer**: Muhammad Anas Raheem ([@anasraheemdev](https://github.com/anasraheemdev))
- **Organization**: [Obrix Labs](https://obrixlabs.com)
