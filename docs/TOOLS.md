# NOKAR Bundled Tools & Actions Catalog

NOKAR includes a rich suite of built-in actions designed specifically to control and automate your desktop environment. Every action self-describes via a `TOOL` schema definition and is automatically discovered at boot by `core/action_loader.py`.

---

## Bundled Actions Index

| Action | Module | Description |
|---|---|---|
| **RAG Vault** | `actions/rag_vault_action.py` | Query, index, and retrieve snippets from local documents and codebase |
| **Screen Processor** | `actions/screen_processor.py` | Capture foreground window context and full-screen vision frames |
| **Video Player** | `actions/video_player.py` | In-HUD & Picture-in-Picture playback for YouTube, media URLs, and files |
| **Antigravity Automation**| `actions/antigravity_control.py`| Inspect and control Antigravity IDE instances |
| **System Monitor** | `actions/system_monitor.py` | Telemetry for CPU, RAM, GPU utilization, and thermals |
| **Computer Settings** | `actions/computer_settings.py` | Adjust volume, brightness, dark mode, power, and Wi-Fi |
| **Computer Control** | `actions/computer_control.py` | Mouse clicks, keystrokes, window focus, and keyboard shortcuts |
| **Open App** | `actions/open_app.py` | Launch applications across Windows, macOS, and Linux |
| **Browser Control** | `actions/browser_control.py` | Open URLs, manage tabs, and execute web automation |
| **File Controller** | `actions/file_controller.py` | Create, move, copy, rename, delete files with automatic Undo logging |
| **File Processor** | `actions/file_processor.py` | Read and summarize text, markdown, CSV, and code files |
| **Web Search** | `actions/web_search.py` | Multi-mode search (`news`, `research`, `price`, `compare`, `search`) |
| **Background Monitor** | `actions/background_monitor.py` | Periodic topic watching and headline aggregation |
| **Proactive Engine** | `actions/proactive.py` | Context-aware check-ins and time-based alerts |
| **Reminders** | `actions/reminder.py` | OS-native scheduled system notifications |
| **Send Message** | `actions/send_message.py` | WhatsApp and messaging integration |
| **Weather Report** | `actions/weather_report.py` | Live atmospheric conditions and forecasts |
| **Desktop Manager** | `actions/desktop.py` | Desktop organization, clutter cleanup, and taskbar management |

---

## Detailed Tool Specifications

### 1. Local Codebase & Document RAG Vault (`actions/rag_vault_action.py`)

- **Tool Name**: `query_rag_vault`
- **Supported Operations**:
  - `search`: Query indexed knowledge chunks using semantic keyword similarity.
  - `index`: Index a single file or an entire directory recursively into `memory/rag_vault.json`.
  - `stats`: Retrieve index statistics (total chunks, file count, and storage size).

**Example Invocation**:
```json
{
  "action": "search",
  "query": "How is authentication handled in this project?"
}
```

---

### 2. Screen Vision & Active Window Inspection (`actions/screen_processor.py`)

- **Capture Pipeline**:
  - Automatically queries the active foreground window title using Win32 API (`GetForegroundWindow` / `GetWindowTextW`).
  - Grabs current monitor frames, compresses them into JPEG format, and feeds them into the active Gemini Live stream tagged as `[ACTIVE WINDOW: 'Title']`.

---

### 3. In-App Video Picture-in-Picture (`actions/video_player.py`)

- **Features**:
  - Resolves YouTube URLs, HLS streams (`.m3u8`), and local media files.
  - Starts in muted mode to avoid acoustic feedback.
  - Seamlessly toggles between Center HUD stage and floating 360×240 PiP overlay (`VideoPipWidget`).

---

## Authoring Custom Plugins

You can add new autonomous capabilities by dropping a single Python file into the `plugins/` directory.

### Plugin Template (`plugins/_template.py`)

```python
"""
Custom Skill Template for NOKAR
"""

TOOL = {
    "name": "my_custom_tool",
    "description": "Performs an automated custom desktop task.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search term or instruction"
            }
        },
        "required": ["query"]
    }
}

def handle(params: dict) -> str:
    """Execute the tool when invoked by the AI agent."""
    query = params.get("query", "")
    # Your custom automation logic here
    return f"Successfully processed: {query}"
```

NOKAR discovers new plugins automatically on boot without modifying the core codebase.
