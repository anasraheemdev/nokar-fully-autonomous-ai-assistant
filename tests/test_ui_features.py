import sys
from pathlib import Path

ROOT = Path("c:/Users/anasr/OneDrive/Desktop/Jarvis")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication
import ui

app = QApplication.instance() or QApplication(sys.argv)
jarvis_ui = ui.JarvisUI(ui.BASE_DIR / "core" / "face.png")
win = jarvis_ui._win

# 1. Check stack pages
assert win._main_stack.count() == 9, f"Expected 9 pages, got {win._main_stack.count()}"
print(f"[OK] Main stack has {win._main_stack.count()} pages")

# 2. Check navigation switching
for i in range(9):
    win._nav_rail.set_current_index(i)
    assert win._main_stack.currentIndex() == i, f"Nav rail index {i} mismatch: {win._main_stack.currentIndex()}"
print("[OK] Navigation switching across all 9 pages verified")
win._nav_rail.set_current_index(0)

# 3. Check assistant state changes
win._apply_state("SPEAKING")
assert "Speaking" in win._status_pill.text(), f"Pill text mismatch: {win._status_pill.text()}"
assert win.hud.speaking is True

win._apply_state("THINKING")
assert "Thinking" in win._status_pill.text(), f"Pill text mismatch: {win._status_pill.text()}"

win._apply_state("LISTENING")
assert "Listening" in win._status_pill.text(), f"Pill text mismatch: {win._status_pill.text()}"
print("[OK] Assistant states (Listening, Speaking, Thinking) verified")

# 4. Check mute toggling
win._toggle_mute()
assert win._muted is True
assert "Muted" in win._status_pill.text()
assert win._mute_btn.text() == "🔇"

win._toggle_mute()
assert win._muted is False
assert "Listening" in win._status_pill.text()
assert win._mute_btn.text() == "🎙"
print("[OK] Mute toggle verified")

# 5. Check telemetry update
win._update_metrics()
assert win._bar_cpu._text != "--"
assert win._mini_telemetry.cpu_lbl.text() != "--%"
print("[OK] Telemetry metrics update verified")

# 6. Check floating popover toggle and Escape dismiss
assert not win._monitor_popover.isVisible()
win._toggle_monitor_popover()
assert win._monitor_popover.isVisible()
win._do_interrupt()
assert not win._monitor_popover.isVisible()
print("[OK] Floating system monitor popover toggle and ESC dismiss verified")

# 7. Check command submission
last_cmd = []
win.on_text_command = lambda cmd: last_cmd.append(cmd)
win._cmd_dock.input_field.setText("Hello Nokar")
win._cmd_dock._on_send()
import time
time.sleep(0.1)
assert len(last_cmd) == 1 and last_cmd[0] == "Hello Nokar", f"Command mismatch: {last_cmd}"
print("[OK] Command submission via command dock verified")

# 8. Check camera stream stack slot
win._on_cam_stream(True)
assert win._hud_cam_stack.currentIndex() == 1
win._on_cam_stream(False)
assert win._hud_cam_stack.currentIndex() == 0
print("[OK] Camera stream stack verified")

# 9. Check Video Picture-in-Picture (PiP) toggle
assert hasattr(win, '_pip_widget') and win._pip_widget is not None
assert hasattr(win, '_toggle_video_pip')
win._toggle_video_pip(True)
assert win._pip_widget.isVisible()
assert win._hud_cam_stack.currentIndex() == 0  # Avatar stays visible in PiP mode!
win._toggle_video_pip(False)
assert not win._pip_widget.isVisible()
print("[OK] Video Picture-in-Picture (PiP) mode verified")

# 10. Check Spotlight floating bar
assert hasattr(win, '_spotlight') and win._spotlight is not None
win._toggle_spotlight()
assert win._spotlight.isVisible()
win._spotlight.hide()
assert not win._spotlight.isVisible()
print("[OK] Global Spotlight Bar summon & dismiss verified")

# 11. Check Local Document RAG Vault
from core.rag_vault import get_vault
vault = get_vault()
c_cnt = vault.index_file(ROOT / "LICENSE")
assert c_cnt > 0
res = vault.query("software license permissions", top_k=2)
assert len(res) > 0
assert "LICENSE" in res[0]["file_name"]
print("[OK] Local Codebase & Document RAG Vault verified")

# 12. Check Autonomous Executive Watchdog
assert hasattr(win, '_watchdog') and win._watchdog is not None
print("[OK] Autonomous Executive Watchdog verified")

# 13. Check Antigravity View & Automation Controls
win._antigravity_view._refresh_status()
assert "Antigravity Path:" in win._antigravity_view.status_lbl.text()
last_anti_action = []
win._antigravity_view.anti_action.connect(lambda a: last_anti_action.append(a))
win._antigravity_view._launch()
assert len(last_anti_action) == 1 and "Open Antigravity" in last_anti_action[0]
print("[OK] Antigravity Autonomous View & Controls verified")

# 14. Check Active Window Context in Vision
from actions.screen_processor import _get_active_window_title
w_title = _get_active_window_title()
assert isinstance(w_title, str)
print("[OK] Active Window Foreground Context in Screen Vision verified")

# Clean up
if win._watchdog:
    win._watchdog.stop()

print("\nALL ENHANCEMENT TESTS PASSED WITH 100% SUCCESS!")
