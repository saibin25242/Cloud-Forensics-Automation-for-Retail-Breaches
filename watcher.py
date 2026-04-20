import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scanner import scan

WATCH_PATH = "scan_folder"

# =========================
# 🔁 DEBOUNCE CONTROL
# =========================
last_run = 0
LOCK = threading.Lock()
DEBOUNCE_SECONDS = 2


def safe_scan():
    """
    Prevent multiple rapid scans (important for file save/edit)
    """
    global last_run

    with LOCK:
        now = time.time()

        if now - last_run < DEBOUNCE_SECONDS:
            return  # ignore repeated triggers

        last_run = now

    print("🔄 Running forensic scan...")
    scan()
    print("✅ Scan completed\n")


# =========================
# 👁 FILE EVENT HANDLER
# =========================
class WatchHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        # ignore folders
        if event.is_directory:
            return

        print(f"📁 Change detected: {event.event_type} → {event.src_path}")

        safe_scan()


# =========================
# 🚀 START WATCHER
# =========================
if __name__ == "__main__":
    observer = Observer()
    observer.schedule(WatchHandler(), WATCH_PATH, recursive=True)

    observer.start()

    print("🛡 RETAIL FORENSICS WATCHDOG ACTIVE")
    print(f"👀 Monitoring: {WATCH_PATH}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping watchdog...")
        observer.stop()

    observer.join()