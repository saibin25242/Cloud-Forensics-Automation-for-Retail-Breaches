# 🛡 Retail Breach Forensics System

So this is a real-time file monitoring and forensics tool I built using Python Flask, PostgreSQL, and Watchdog. The idea is simple  you drop files into a folder, and the system keeps an eye on them. Any time something changes (a file gets modified, deleted, or a new one appears), it logs everything into a database with SHA256 hashes so you have a full evidence trail.

It's genuinely useful for catching unauthorized file changes in a retail or enterprise environment.

---

## Before You Start

Make sure you have these installed on your machine:

- Python 3.8 or higher
- PostgreSQL
- pip

Nothing too crazy, just the basics.

---

## Step 1 — Install the Dependencies

Open your terminal and run:

```bash
pip install flask psycopg2-binary watchdog
```

That's all you need. Flask runs the web server, psycopg2 talks to PostgreSQL, and watchdog listens for file changes in real time.

---

## Step 2 — Set Up the Database

First, open **pgAdmin** or a **psql** terminal and create the database:

```sql
CREATE DATABASE forensics_db;
```

Then connect to it and create the evidence table:

```sql
\c forensics_db

CREATE TABLE evidence (
    id            SERIAL PRIMARY KEY,
    file_name     TEXT,
    file_path     TEXT,
    created_time  TEXT,
    modified_time TEXT,
    sha256        TEXT,
    status        TEXT,
    scan_time     TEXT,
    risk_level    TEXT
);
```

This table is where everything gets stored — every scan, every file, every change.

---

## Step 3 — Update Your Password

Open both `app.py` and `db.py` and find this section near the top. Change the password to match your PostgreSQL setup:

```python
DB_CONFIG = {
    "dbname": "forensics_db",
    "user": "postgres",
    "password": "YOUR_PASSWORD_HERE",   # ← just change this
    "host": "localhost",
    "port": "5432"
}
```

Easy one, don't skip it or you'll get a connection error and wonder why nothing works.

---

## Step 4 — Check Your Project Structure

Your folder should look like this before you run anything:

```
project/
├── app.py
├── db.py
├── scanner.py
├── watcher.py
├── scan_folder/             ← drop your files in here
│   ├── employee_access.txt
│   ├── payment_logs.txt
│   ├── sales_data.txt
│   └── message.txt
└── templates/
    ├── client.html
    ├── index.html
    ├── edit.html
    └── view.html
```

The `scan_folder/` gets created automatically when you first run the app, so don't stress if it's not there yet.

---

## Step 5 — Run the App

You'll need two terminals open for this.

**Terminal 1 — Start the Flask server:**

```bash
python app.py
```

Once it's running, open your browser and go to [http://localhost:5000](http://localhost:5000).

**Terminal 2 — Start the file watcher:**

```bash
python watcher.py
```

This is what monitors your `scan_folder/` in real time. Any file change triggers an automatic scan — you don't have to do anything manually.

---

## Step 6 — Manual Scan (if you need it)

If you just want to run a quick one-time scan without the watcher running, this does it:

```bash
python scanner.py
```

Useful for testing or if you've made a bunch of changes and want an immediate snapshot.

---

## Pages

| URL | What it does |
|-----|-------------|
| `http://localhost:5000/` | Upload portal — upload and manage your files |
| `http://localhost:5000/admin` | Forensics dashboard — charts, evidence log, history |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/evidence` | GET | Returns the latest scan results |
| `/api/summary` | GET | Returns counts by status |
| `/api/history` | GET | Returns scan history over time |
| `/api/scan` | POST | Triggers a manual scan |

---

## Working with the Database

This is something you'll probably come back to often, so here's everything in one place.

### Connect to the database

Open a terminal and run:

```bash
psql -U postgres
```

It'll ask for your password. Once you're in, switch to the right database:

```sql
\c forensics_db
```

> ⚠️ This is important — if you skip this and just run queries straight away, you'll get a `relation "evidence" does not exist` error because you're still on the default `postgres` database.

Or if you want to skip the switch, connect directly:

```bash
psql -U postgres -d forensics_db
```

---

### Viewing Records

**See everything:**
```sql
SELECT * FROM evidence;
```

**Only the latest scan:**
```sql
SELECT * FROM evidence
WHERE scan_time = (SELECT MAX(scan_time) FROM evidence);
```

**Only the risky stuff (modified or deleted files):**
```sql
SELECT * FROM evidence
WHERE status IN ('MODIFIED', 'DELETED');
```

**Look up a specific file:**
```sql
SELECT * FROM evidence
WHERE file_name = 'employee_access.txt';
```

**Quick count by status:**
```sql
SELECT status, COUNT(*) FROM evidence
GROUP BY status;
```

---

### Clearing Records

**Wipe everything and reset the ID counter back to 1:**
```sql
TRUNCATE TABLE evidence RESTART IDENTITY;
```

**Wipe everything but keep the ID counter going:**
```sql
DELETE FROM evidence;
```

**Remove just one specific file:**
```sql
DELETE FROM evidence WHERE file_name = 'employee_access.txt';
```

**Remove all deleted-status records:**
```sql
DELETE FROM evidence WHERE status = 'DELETED';
```

After clearing, double check it worked:
```sql
SELECT * FROM evidence;
-- You should see: (0 rows)
```

---

## Risk Levels — What They Mean

| Status | Risk Level | What happened |
|--------|------------|---------------|
| DELETED | CRITICAL | A file was removed — investigate immediately |
| MODIFIED | HIGH | File content changed since last scan |
| NEW | MEDIUM | A new file appeared that wasn't there before |
| UNCHANGED | LOW | All good, nothing changed |

The dashboard sorts by risk automatically, so the most critical stuff always shows up at the top.

---

## How It All Works Together

1. You drop files into `scan_folder/`
2. The watcher notices immediately and triggers a scan
3. The scanner reads each file, generates a SHA256 hash, and compares it to the last known hash
4. Based on what changed, it assigns a status and risk level
5. Everything gets saved to PostgreSQL
6. The dashboard at `/admin` pulls the latest data and shows it in real time — charts, tables, the works
7. if you need CSV report you generate it through export option where details of each file's name,path,time,hash value,status,scan time and risk level can be seen.

---

## Stopping Everything

Just hit `Ctrl + C` in both terminals. Clean stop, no drama.

---

## Troubleshooting

**Getting a connection error?**
Check that PostgreSQL is actually running, and that the password in `app.py` and `db.py` matches your setup.

**`relation "evidence" does not exist`?**
Classic one — you're connected to the wrong database. Run `\c forensics_db` first, then try again.

**Watcher not picking up changes?**
Make sure the watcher terminal is still open and active, and that your files are inside `scan_folder/` not somewhere else.

**Everything showing as NEW on first run?**
That's expected. The first scan has nothing to compare against, so every file is NEW. Next scan they'll show as UNCHANGED (assuming you didn't touch them).


