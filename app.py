from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for
import csv
import os
import subprocess
from collections import defaultdict
from werkzeug.utils import secure_filename

app = Flask(__name__)

REPORT_FILE = "forensic_report.csv"
SCAN_FOLDER = "scan_folder"

app.config['UPLOAD_FOLDER'] = SCAN_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(SCAN_FOLDER, exist_ok=True)

# =========================
# 🔍 FILE TYPE CHECK
# =========================
def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except:
        return False


# =========================
# 📊 LOAD REPORT
# =========================
def load_report():
    if not os.path.exists(REPORT_FILE):
        return []

    rows = []
    with open(REPORT_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            while len(row) < 7:
                row.append("")

            rows.append({
                "file_name": row[0],
                "file_path": row[1],
                "created_time": row[2],
                "modified_time": row[3],
                "sha256": row[4],
                "status": row[5] if row[5] else "NEW",
                "scan_time": row[6]
            })

    return rows


def get_latest_snapshot(rows):
    latest = {}
    for row in rows:
        fp = row["file_path"]
        if fp not in latest or row["scan_time"] > latest[fp]["scan_time"]:
            latest[fp] = row
    return list(latest.values())


# =========================
# 🔄 RUN SCAN
# =========================
def run_scan():
    try:
        subprocess.run(["python", "forensic_collector.py"])
    except Exception as e:
        print("Scan Error:", e)


# =========================
# 📊 SUMMARY
# =========================
def get_summary(rows):
    latest = get_latest_snapshot(rows)

    return {
        "total": len(latest),
        "modified": sum(1 for r in latest if r["status"] == "MODIFIED"),
        "new": sum(1 for r in latest if r["status"] == "NEW"),
        "unchanged": sum(1 for r in latest if r["status"] == "UNCHANGED"),
        "risk_level": (
            "HIGH" if any(r["status"] == "MODIFIED" for r in latest)
            else "MEDIUM" if any(r["status"] == "NEW" for r in latest)
            else "LOW"
        )
    }


# =========================
# 🌐 FILE SERVER
# =========================
@app.route("/files/<path:filename>")
def serve_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    if os.path.exists(filepath):
        return send_file(filepath)

    return "File not found", 404


# =========================
# 🌐 MAIN PAGE
# =========================
@app.route("/")
def index():
    files = []

    for root, _, filenames in os.walk(SCAN_FOLDER):
        for filename in filenames:
            filepath = os.path.join(root, filename)

            files.append({
                "name": filename,
                "path": filename,
                "is_text": is_text_file(filepath)
            })

    return render_template("client.html", files=files)


@app.route("/admin")
def admin():
    return render_template("index.html")


# =========================
# 📊 API
# =========================
@app.route("/api/summary")
def api_summary():
    return jsonify(get_summary(load_report()))


@app.route("/api/evidence")
def api_evidence():
    rows = load_report()
    latest = get_latest_snapshot(rows)

    order = {"MODIFIED": 0, "NEW": 1, "UNCHANGED": 2}
    latest.sort(key=lambda r: order.get(r["status"], 3))

    return jsonify(latest)


@app.route("/api/history")
def api_history():
    rows = load_report()
    sessions = defaultdict(list)

    for row in rows:
        sessions[row["scan_time"]].append(row)

    history = []
    for scan_time in sorted(sessions.keys()):
        entries = sessions[scan_time]

        history.append({
            "scan_time": scan_time,
            "total": len(entries),
            "modified": sum(1 for r in entries if r["status"] == "MODIFIED"),
            "new": sum(1 for r in entries if r["status"] == "NEW"),
            "unchanged": sum(1 for r in entries if r["status"] == "UNCHANGED"),
        })

    return jsonify(history)


# =========================
# 📤 UPLOAD
# =========================
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")

    if not file or file.filename == "":
        return "No file selected", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    file.save(filepath)
    run_scan()

    return redirect(url_for("index"))


# =========================
# 📄 VIEW FILE
# =========================
@app.route("/view/<path:filename>")
def view_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    if not os.path.exists(filepath):
        return "File not found", 404

    file_url = url_for("serve_file", filename=filename)

    if is_text_file(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return render_template(
            "view.html",
            filename=filename,
            content=content,
            is_text=True,
            file_url=file_url
        )

    return render_template(
        "view.html",
        filename=filename,
        content="Binary file - use OPEN button",
        is_text=False,
        file_url=file_url
    )


# =========================
# ✏️ EDIT FILE
# =========================
@app.route("/edit/<path:filename>")
def edit_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    if not os.path.exists(filepath):
        return "File not found", 404

    file_url = url_for("serve_file", filename=filename)

    if is_text_file(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return render_template(
            "edit.html",
            filename=filename,
            content=content,
            is_text=True,
            file_url=file_url
        )

    return render_template(
        "edit.html",
        filename=filename,
        content="Binary file - replace required",
        is_text=False,
        file_url=file_url
    )


# =========================
# 🔥 SAVE ROUTE (FIX ADDED)
# =========================
@app.route("/save/<path:filename>", methods=["POST"])
def save_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    content = request.form.get("content", "")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    run_scan()

    return redirect(url_for("view_file", filename=filename))


# =========================
# 🔁 REPLACE FILE
# =========================
@app.route("/replace/<path:filename>", methods=["POST"])
def replace_file(filename):
    file = request.files.get("file")

    if not file:
        return "No file uploaded", 400

    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    file.save(filepath)
    run_scan()

    return redirect(url_for("index"))


# =========================
# 📥 DOWNLOAD
# =========================
@app.route("/download/<path:filename>")
def download_file(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(SCAN_FOLDER, filename)

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)

    return "File not found", 404


@app.route("/api/download")
def api_download():
    if os.path.exists(REPORT_FILE):
        return send_file(REPORT_FILE, as_attachment=True)
    return jsonify({"error": "Report not found"}), 404


# =========================
# 🚀 RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)