from flask import Flask, jsonify, render_template, request, redirect, url_for, send_file
import os
import subprocess
import psycopg2

app = Flask(__name__)

# =========================
# ⚙️ CONFIG
# =========================
UPLOAD_FOLDER = "scan_folder"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 🔐 UPDATE YOUR PASSWORD
DB_CONFIG = {
    "dbname": "forensics_db",
    "user": "postgres",
    "password": "25242",
    "host": "localhost",
    "port": "5432"
}


# =========================
# 🔌 DB CONNECT
# =========================
def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def get_current_state():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT file_name, file_path,
               created_time, modified_time,
               sha256, status, scan_time, risk_level
        FROM evidence
        WHERE scan_time = (
            SELECT MAX(scan_time) FROM evidence
        )
        ORDER BY 
            CASE status
                WHEN 'MODIFIED' THEN 0
                WHEN 'NEW' THEN 1
                WHEN 'UNCHANGED' THEN 2
                WHEN 'DELETED' THEN 3
            END
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "file_name": r[0],
            "file_path": r[1],
            "created_time": str(r[2]) if r[2] else None,
            "modified_time": str(r[3]) if r[3] else None,
            "sha256": r[4],   # ✅ FIXED
            "status": r[5],
            "scan_time": str(r[6]),
            "risk_level": r[7]
        }
        for r in rows
    ]

# =========================
# 🌐 MAIN PAGES
# =========================
@app.route("/")
def client():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("client.html", files=files)


@app.route("/admin")
def admin():
    return render_template("index.html")


# =========================
# 📤 UPLOAD FILE
# =========================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or file.filename == "":
        return "No file selected", 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    # 🔁 Run scan automatically
    subprocess.run(["python", "scanner.py"])

    return redirect(url_for("client"))


# =========================
# 📄 VIEW FILE
# =========================
@app.route("/view/<filename>")
def view(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(path):
        return "File not found", 404

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return "Binary file - cannot display"

    return f"<pre>{content}</pre>"


# =========================
# 📥 DOWNLOAD FILE
# =========================
@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if os.path.exists(path):
        return send_file(path, as_attachment=True)

    return "File not found", 404


# =========================
# 📊 API: EVIDENCE
# =========================
@app.route("/api/evidence")
def evidence():
    return jsonify(get_current_state())


# =========================
# 📊 API: SUMMARY
# =========================
@app.route("/api/summary")
def summary():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT status, COUNT(*)
        FROM evidence
        WHERE scan_time = (
            SELECT MAX(scan_time) FROM evidence
        )
        GROUP BY status
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = {"total": 0, "modified": 0, "new": 0, "unchanged": 0, "deleted": 0}

    for status, count in rows:
        key = status.lower()
        data["total"] += count
        if key in data:
            data[key] = count

    return jsonify(data)
@app.route("/edit/<path:filename>")
def edit_file(filename):
    import os

    filename = os.path.basename(filename)   # FIX SECURITY + PATH ISSUE
    path = os.path.join("scan_folder", filename)

    if not os.path.exists(path):
        return f"File not found: {filename}", 404

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return render_template("edit.html",
        filename=filename,
        content=content
    )
@app.route("/save/<path:filename>", methods=["POST"])
def save_file(filename):
    import hashlib
    from datetime import datetime

    filename = os.path.basename(filename)
    path = os.path.join("scan_folder", filename)

    content = request.form.get("content")

    # save file
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    # generate new hash
    sha256 = hashlib.sha256(content.encode()).hexdigest()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # update database (IMPORTANT)
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE evidence
        SET modified_time=%s,
            sha256=%s,
            status='MODIFIED',
            scan_time=%s
        WHERE file_name=%s
    """, (now, sha256, now, filename))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("client"))
# =========================
# 📈 API: HISTORY (FIX)
# =========================
@app.route("/api/history")
def history():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            scan_time,
            SUM(CASE WHEN status='MODIFIED' THEN 1 ELSE 0 END) as modified,
            SUM(CASE WHEN status='NEW' THEN 1 ELSE 0 END) as new,
            SUM(CASE WHEN status='UNCHANGED' THEN 1 ELSE 0 END) as unchanged
        FROM evidence
        GROUP BY scan_time
        ORDER BY scan_time
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([
        {
            "scan_time": str(r[0]),
            "modified": r[1],
            "new": r[2],
            "unchanged": r[3]
        }
        for r in rows
    ])
# =========================
# 📥 EXPORT CSV
# =========================
@app.route("/api/export")
def export_csv():
    import csv
    import io
    from flask import Response

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT file_name, file_path, created_time, modified_time,
               sha256, status, scan_time, risk_level
        FROM evidence
        WHERE scan_time = (
            SELECT MAX(scan_time) FROM evidence
        )
        ORDER BY
            CASE status
                WHEN 'DELETED'   THEN 0
                WHEN 'MODIFIED'  THEN 1
                WHEN 'NEW'       THEN 2
                WHEN 'UNCHANGED' THEN 3
            END,
            file_name ASC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "File Name", "File Path", "Created Time", "Modified Time",
        "SHA256", "Status", "Scan Time", "Risk Level"
    ])

    writer.writerows(rows)
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=forensics_evidence.csv"
        }
    )


# =========================
# 🔁 API: RUN SCAN
# =========================
@app.route("/api/scan", methods=["POST"])
def scan():
    subprocess.run(["python", "scanner.py"])
    return jsonify({"status": "ok"})


# =========================
# 🚀 RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)