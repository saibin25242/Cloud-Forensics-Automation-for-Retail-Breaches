import psycopg2


# =========================
# CONNECT DATABASE
# =========================
def connect():
    return psycopg2.connect(
        dbname="forensics_db",
        user="postgres",
        password="25242",
        host="localhost",
        port="5432"
    )


# =========================
# INSERT SCAN DATA
# =========================
def insert_data(rows):
    conn = connect()
    cur = conn.cursor()

    cur.executemany("""
        INSERT INTO evidence (
            file_name, file_path, created_time,
            modified_time, sha256, status, scan_time, risk_level
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)

    conn.commit()
    cur.close()
    conn.close()


# =========================
# GET CURRENT SCAN STATE
# =========================
def get_current_state():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT file_name, file_path, created_time,
               modified_time, sha256, status, scan_time
        FROM evidence
        WHERE scan_time = (
            SELECT MAX(scan_time) FROM evidence
        )
        ORDER BY status
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "file_name": r[0],
            "file_path": r[1],
            "created_time": str(r[2]),
            "modified_time": str(r[3]),
            "sha256": r[4],
            "status": r[5],
            "scan_time": str(r[6])
        }
        for r in rows
    ]


# =========================
# GET PREVIOUS HASH SNAPSHOT (FIXED)
# =========================
def get_previous_hashes():
    conn = connect()
    cur = conn.cursor()

    # latest scan time
    cur.execute("SELECT MAX(scan_time) FROM evidence")
    latest = cur.fetchone()[0]

    if not latest:
        cur.close()
        conn.close()
        return {}

    # previous scan time
    cur.execute("""
        SELECT MAX(scan_time)
        FROM evidence
        WHERE scan_time < %s
    """, (latest,))

    prev = cur.fetchone()[0]

    if not prev:
        cur.close()
        conn.close()
        return {}

    # full previous snapshot
    cur.execute("""
        SELECT file_path, sha256
        FROM evidence
        WHERE scan_time = %s
    """, (prev,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {r[0]: r[1] for r in rows}