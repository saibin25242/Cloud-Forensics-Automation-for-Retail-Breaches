# CloudForensics — Retail Breach Monitor
### IBM Final Year Project | PRJN26-172

---

## Project Structure

```
project/
y├── app.py                  ← Flask backend with client and admin interfaces
├── forensic_collector.py   ← Evidence collector
├── sync_to_excel.py        ← CSV → Excel sync
├── forensic_report.csv     ← Evidence log (auto-generated)
├── forensic_report.xlsx    ← Excel version (auto-generated)
├── templates/
│   ├── client.html         ← Client file management interface
│   ├── index.html          ← Admin forensics dashboard
│   ├── view.html           ← File viewer
│   └── edit.html           ← File editor
└── scan_folder/
    ├── employee_access.txt
    ├── payment_logs.txt
    └── sales_data.txt
```

---

## Setup & Run

### Step 1 — Install dependencies
```bash
pip install flask pandas openpyxl
```

### Step 2 — Run the forensic collector (first scan)
```bash
python forensic_collector.py
```

### Step 3 — Start the dashboard
```bash
python app.py
```

### Step 4 — Open in browser
```
Client Interface: http://localhost:5000
Admin Dashboard:  http://localhost:5000/admin
```

### Features
- **Client Interface (/)**: Upload, view, and edit files in scan_folder. Any file type can be opened and edited. Text files show content for editing, binary files show replacement options. Changes are automatically tracked via forensics and users can immediately view their edited/replaced files.
- **Admin Dashboard (/admin)**: Monitor forensics data, view alerts, scan history, and download reports.

### Optional — Auto-sync to Excel in background
```bash
python sync_to_excel.py
```

---

## Dashboard Features
- **Live Evidence Table** — All scanned files with SHA256 hash, timestamps, status
- **Status Filters** — Filter by MODIFIED / NEW / UNCHANGED
- **Tamper Alerts** — Red alerts for any modified or new files
- **Scan History** — Timeline of every scan session
- **Run Scan Button** — Trigger a new scan from the browser
- **Export CSV** — Download the evidence report
- **Risk Level** — Automatic HIGH/MEDIUM/LOW risk assessment

---

## Bug Fixes in v1.1
- Fixed: CSV header had 2 empty columns on first scan
- Fixed: Status and Scan Time not written in initial scan
- Improved: `load_previous_hashes()` now keeps the LATEST hash per file

---

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Forensics**: hashlib (SHA256), os (file metadata)
- **Data**: CSV, Excel (pandas + openpyxl)
