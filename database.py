"""SQLite layer for CrimeSight. Creates the DB, seeds sample data, CRUD helpers."""
import hashlib
import os
import random
import sqlite3
from datetime import date, datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crime.db")

CRIME_TYPES = ["Theft", "Robbery", "Burglary", "Assault", "Fraud", "Cybercrime",
               "Vehicle Theft", "Drug Offence", "Harassment", "Vandalism",
               "Kidnapping", "Murder"]
STATUSES = ["Open", "Under Investigation", "Closed"]
SEVERITIES = ["Low", "Medium", "High"]
AREAS = ["Sector 17", "Sector 22", "Sector 35", "Mohali Phase 7", "Kharar",
         "Zirakpur", "Panchkula", "Manimajra", "Industrial Area", "Sector 43 ISBT",
         "Dera Bassi", "Sunny Enclave"]
OFFICERS = ["Insp. R. Sharma", "SI A. Verma", "Insp. K. Gill", "SI P. Kaur",
            "ASI M. Singh", "Insp. N. Thakur", "SI D. Mehta", "SI S. Bedi"]

COLUMNS = ["case_id", "crime_type", "date", "time", "area", "severity",
           "status", "officer", "description"]


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Weights make the sample data look realistic instead of uniform.
_WEIGHTS = [22, 8, 10, 12, 11, 12, 9, 6, 5, 3, 1, 1]
_AREA_WEIGHTS = [14, 9, 8, 12, 7, 10, 9, 6, 8, 11, 3, 3]
_HOUR_WEIGHTS = [2, 1, 1, 1, 1, 1, 2, 3, 4, 4, 4, 4, 5, 4, 4, 5, 6, 8, 10, 11, 10, 8, 5, 3]
_DESC = {
    "Theft": "Mobile phone / wallet snatched in a crowded market.",
    "Robbery": "Armed robbery reported near a shop at closing time.",
    "Burglary": "House broken into while owners were away; jewellery missing.",
    "Assault": "Physical fight reported outside a restaurant.",
    "Fraud": "Victim cheated through a fake online investment scheme.",
    "Cybercrime": "Phishing / OTP fraud resulting in bank account loss.",
    "Vehicle Theft": "Two-wheeler stolen from a parking lot overnight.",
    "Drug Offence": "Possession of banned substances recovered during checking.",
    "Harassment": "Complaint of repeated harassment and threats.",
    "Vandalism": "Public property and vehicles damaged.",
    "Kidnapping": "Missing person case with suspected abduction.",
    "Murder": "Fatal attack; investigation by crime branch ongoing.",
}


def _seed(conn, n=600):
    rnd = random.Random(47)
    conn.executemany("INSERT INTO users VALUES (?,?,?)", [
        ("admin", hash_pw("admin123"), "Admin"),
        ("officer", hash_pw("officer123"), "Officer"),
    ])
    today = date.today()
    rows = []
    for i in range(1, n + 1):
        ctype = rnd.choices(CRIME_TYPES, _WEIGHTS)[0]
        area = rnd.choices(AREAS, _AREA_WEIGHTS)[0]
        d = today - timedelta(days=int(rnd.triangular(0, 730, 120)))
        hour = rnd.choices(range(24), _HOUR_WEIGHTS)[0]
        t = f"{hour:02d}:{rnd.randint(0, 59):02d}"
        sev = ("High" if ctype in ("Murder", "Kidnapping", "Robbery")
               else rnd.choices(SEVERITIES, [4, 5, 2])[0])
        age = (today - d).days
        status = (rnd.choices(STATUSES, [10, 25, 65])[0] if age > 120
                  else rnd.choices(STATUSES, [45, 40, 15])[0])
        rows.append((f"CR{d.year}-{i:04d}", ctype, d.isoformat(), t, area, sev,
                     status, rnd.choice(OFFICERS), _DESC[ctype]))
    conn.executemany("INSERT INTO crimes VALUES (?,?,?,?,?,?,?,?,?)", rows)


def init_db():
    conn = connect()
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    conn.execute("""CREATE TABLE IF NOT EXISTS crimes (
        case_id TEXT PRIMARY KEY, crime_type TEXT, date TEXT, time TEXT, area TEXT,
        severity TEXT, status TEXT, officer TEXT, description TEXT)""")
    if conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0] == 0:
        _seed(conn)
    conn.commit()
    conn.close()


def login(username, password):
    conn = connect()
    row = conn.execute("SELECT role FROM users WHERE username=? AND password=?",
                       (username, hash_pw(password))).fetchone()
    conn.close()
    return row["role"] if row else None


def fetch(search="", crime_type="All", area="All", status="All",
          date_from="", date_to=""):
    q, p = "SELECT * FROM crimes WHERE 1=1", []
    if search:
        q += " AND (case_id LIKE ? OR description LIKE ? OR officer LIKE ?)"
        p += [f"%{search}%"] * 3
    for col, val in (("crime_type", crime_type), ("area", area), ("status", status)):
        if val != "All":
            q += f" AND {col}=?"
            p.append(val)
    if date_from:
        q += " AND date>=?"
        p.append(date_from)
    if date_to:
        q += " AND date<=?"
        p.append(date_to)
    q += " ORDER BY date DESC, time DESC"
    conn = connect()
    rows = [dict(r) for r in conn.execute(q, p).fetchall()]
    conn.close()
    return rows


def get(case_id):
    conn = connect()
    r = conn.execute("SELECT * FROM crimes WHERE case_id=?", (case_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def next_case_id():
    conn = connect()
    n = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0] + 1
    conn.close()
    while get(f"CR{date.today().year}-{n:04d}"):
        n += 1
    return f"CR{date.today().year}-{n:04d}"


def add(rec):
    conn = connect()
    conn.execute("INSERT INTO crimes VALUES (?,?,?,?,?,?,?,?,?)", [rec[c] for c in COLUMNS])
    conn.commit()
    conn.close()


def update(rec):
    conn = connect()
    conn.execute("""UPDATE crimes SET crime_type=?, date=?, time=?, area=?, severity=?,
                    status=?, officer=?, description=? WHERE case_id=?""",
                 [rec[c] for c in COLUMNS[1:]] + [rec["case_id"]])
    conn.commit()
    conn.close()


def delete(case_id):
    conn = connect()
    conn.execute("DELETE FROM crimes WHERE case_id=?", (case_id,))
    conn.commit()
    conn.close()


def validate(rec, is_new):
    """Return an error message, or None if the record is valid."""
    if not rec["case_id"].strip():
        return "Case ID is required."
    if is_new and get(rec["case_id"]):
        return "This Case ID already exists."
    try:
        datetime.strptime(rec["date"], "%Y-%m-%d")
    except ValueError:
        return "Date must be in YYYY-MM-DD format."
    try:
        datetime.strptime(rec["time"], "%H:%M")
    except ValueError:
        return "Time must be in HH:MM (24h) format."
    if not rec["description"].strip():
        return "Description is required."
    return None
