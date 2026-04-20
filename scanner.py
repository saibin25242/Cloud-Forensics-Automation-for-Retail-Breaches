import os
import hashlib
from datetime import datetime
from db import insert_data, get_previous_hashes


# =========================
# HASH FUNCTION
# =========================
def hashf(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        print(f"[ERROR] Cannot hash file {path}: {e}")
        return None


# =========================
# RISK LEVEL FUNCTION
# =========================
def risk_level(status):
    if status == "MODIFIED":
        return "HIGH"
    elif status == "NEW":
        return "MEDIUM"
    elif status == "DELETED":
        return "CRITICAL"
    return "LOW"


# =========================
# SCAN FUNCTION
# =========================
def scan():
    data = []

    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # previous snapshot (path -> hash)
    previous = get_previous_hashes()

    current_paths = set()

    # =========================
    # SCAN FILE SYSTEM
    # =========================
    for root, _, files in os.walk("scan_folder"):
        for file in files:

            path = os.path.normpath(os.path.join(root, file))
            current_paths.add(path)

            if not os.path.exists(path):
                continue

            file_hash = hashf(path)
            if file_hash is None:
                continue

            created = datetime.fromtimestamp(
                os.path.getctime(path)
            ).strftime("%Y-%m-%d %H:%M:%S")

            modified = datetime.fromtimestamp(
                os.path.getmtime(path)
            ).strftime("%Y-%m-%d %H:%M:%S")

            # =========================
            # STATUS LOGIC
            # =========================
            if path not in previous:
                status = "NEW"

            elif previous.get(path) == file_hash:
                status = "UNCHANGED"

            else:
                status = "MODIFIED"

            # =========================
            # FINAL ROW
            # =========================
            data.append((
                file,              # file_name
                path,              # file_path
                created,           # created_time
                modified,          # modified_time
                file_hash,         # sha256
                status,            # status
                scan_time,         # scan_time
                risk_level(status) # risk_level
            ))

    # =========================
    # OPTIONAL: DETECT DELETED FILES
    # =========================
    previous_paths = set(previous.keys())
    deleted_files = previous_paths - current_paths

    for path in deleted_files:
        data.append((
            os.path.basename(path),
            path,
            None,
            None,
            None,
            "DELETED",
            scan_time,
            risk_level("DELETED")
        ))

    # =========================
    # INSERT INTO DATABASE
    # =========================
    insert_data(data)

    print(f"✅ Scan complete: {len(data)} records processed")


# =========================
# RUN MANUALLY
# =========================
if __name__ == "__main__":
    scan()