import os
import csv
import hashlib
from datetime import datetime

SCAN_FOLDER = "scan_folder"
REPORT_FILE = "forensic_report.csv"

HEADERS = ["File Name", "File Path", "Created Time", "Last Modified Time", "SHA256 Hash", "Status", "Scan Time"]


def calculate_hash(file_path):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return "Error"


def load_previous_hashes():
    """Load only the LATEST hash per file from the report."""
    hashes = {}
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                fp = row.get("File Path", "")
                h  = row.get("SHA256 Hash", "")
                if fp and h:
                    hashes[fp] = h   # keeps updating → last row wins = most recent
    return hashes


def scan_directory(folder):
    previous_hashes = load_previous_hashes()
    evidence = []
    scan_time = datetime.now()

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            created_time  = datetime.fromtimestamp(os.path.getctime(path))
            modified_time = datetime.fromtimestamp(os.path.getmtime(path))
            file_hash     = calculate_hash(path)

            if path in previous_hashes:
                status = "UNCHANGED" if previous_hashes[path] == file_hash else "MODIFIED"
            else:
                status = "NEW"

            evidence.append([file, path, created_time, modified_time, file_hash, status, scan_time])

    return evidence


def save_report(data):
    """Append scan results. Write header only if file is new/empty."""
    write_header = not os.path.isfile(REPORT_FILE) or os.path.getsize(REPORT_FILE) == 0

    with open(REPORT_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(HEADERS)
        writer.writerows(data)


def main():
    print("\nStarting Cloud Forensics Scan...\n")
    results = scan_directory(SCAN_FOLDER)
    save_report(results)
    print(f"Evidence Report Saved: {REPORT_FILE}")

    modified = [r for r in results if r[5] == "MODIFIED"]
    new_files = [r for r in results if r[5] == "NEW"]

    if modified:
        print(f"\n⚠  ALERT — {len(modified)} MODIFIED file(s) detected:")
        for r in modified:
            print(f"   → {r[1]}")

    if new_files:
        print(f"\n+  {len(new_files)} NEW file(s) found:")
        for r in new_files:
            print(f"   → {r[1]}")

    print("\nScan Completed.\n")


if __name__ == "__main__":
    main()
