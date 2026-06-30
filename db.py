import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import pandas as pd

DB_PATH = "cgpsc_mains_tracker.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS papers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, short_name TEXT, total_marks INTEGER DEFAULT 200, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS topics (id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id INTEGER NOT NULL, section TEXT NOT NULL, topic TEXT NOT NULL, sub_topic TEXT, status TEXT DEFAULT 'Not Started', confidence INTEGER DEFAULT 2, last_studied DATE, notes TEXT DEFAULT '', order_index INTEGER DEFAULT 0, FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS study_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, log_date DATE NOT NULL, paper_id INTEGER, topic_id INTEGER, topic_text TEXT, hours REAL NOT NULL, key_takeaways TEXT, mood TEXT, tags TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (paper_id) REFERENCES papers(id), FOREIGN KEY (topic_id) REFERENCES topics(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS mock_tests (id INTEGER PRIMARY KEY AUTOINCREMENT, test_date DATE NOT NULL, paper_id INTEGER, test_type TEXT DEFAULT 'Mock Test', score REAL, max_score REAL DEFAULT 200, percentage REAL, feedback TEXT, weak_areas TEXT, time_taken_minutes INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (paper_id) REFERENCES papers(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS revisions (id INTEGER PRIMARY KEY AUTOINCREMENT, topic_id INTEGER NOT NULL, revision_date DATE NOT NULL, completed INTEGER DEFAULT 0, notes TEXT, FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE)''')
    conn.commit()
    conn.close()

def seed_initial_data():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM papers")
    if c.fetchone()[0] > 0:
        conn.close()
        return "Already seeded"
    papers_data = [(1, "Paper 1: Language", "Language", 200, "Hindi, English & Chhattisgarhi"), (2, "Paper 2: Essay", "Essay", 200, "National/International + CG Issues"), (3, "Paper 3: GS-I", "GS-I", 200, "History + Constitution + CG History"), (4, "Paper 4: GS-II", "GS-II", 200, "Science + Aptitude"), (5, "Paper 5: GS-III", "GS-III", 200, "Economy + Geography"), (6, "Paper 6: GS-IV", "GS-IV", 200, "Sociology + Philosophy + CG Culture"), (7, "Paper 7: GS-V", "GS-V", 200, "Current Affairs + CG Governance")]
    c.executemany("INSERT INTO papers (id, name, short_name, total_marks, description) VALUES (?, ?, ?, ?, ?)", papers_data)
    topics_data = []
    topics_data.extend([(1, "Part A: Hindi", "Grammar & Vocabulary", "Not Started", 2, 1), (1, "Part B: English", "Comprehension & Grammar", "Not Started", 2, 2), (1, "Part C: Chhattisgarhi", "Grammar & Literature", "Not Started", 2, 3)])
    topics_data.extend([(2, "National Issues", "Poverty, Climate, Governance", "Not Started", 2, 1), (2, "CG Issues", "Naxalism, Tribal Welfare, Employment", "Not Started", 2, 2)])
    topics_data.extend([(3, "History of India", "Ancient, Medieval, Modern + CG History", "Not Started", 2, 1), (3, "Constitution & PA", "FR, DPSP, Governance, CG Admin", "Not Started", 2, 2)])
    topics_data.extend([(4, "General Science", "Physics, Chemistry, Biology", "Not Started", 2, 1), (4, "Aptitude & Reasoning", "Maths + Logical Reasoning", "Not Started", 2, 2)])
    topics_data.extend([(5, "Indian Economy", "Planning, Poverty, Agriculture", "Not Started", 2, 1), (5, "Geography", "India + CG Geography", "Not Started", 2, 2)])
    topics_data.extend([(6, "Sociology & Philosophy", "Social Issues + Indian Philosophy + Yoga", "Not Started", 2, 1), (6, "CG Culture & Welfare", "Tribal + Art & Culture + Schemes", "Not Started", 2, 2)])
    topics_data.extend([(7, "Current Affairs", "National + CG Specific", "Not Started", 2, 1), (7, "Governance & Security", "CG Admin + Environment + Naxal", "Not Started", 2, 2)])
    c.executemany("INSERT INTO topics (paper_id, section, topic, status, confidence, order_index) VALUES (?, ?, ?, ?, ?, ?)", topics_data)
    conn.commit()
    conn.close()
    return "Seeded!"

def get_papers():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM papers ORDER BY id", conn)
    conn.close()
    return df.to_dict('records')

def get_topics(paper_id=None):
    conn = get_conn()
    query = "SELECT t.*, p.name as paper_name, p.short_name FROM topics t JOIN papers p ON t.paper_id = p.id"
    if paper_id: query += f" WHERE t.paper_id = {paper_id}"
    query += " ORDER BY t.paper_id, t.order_index, t.id"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def update_topic_status(topic_id, status, confidence=None, notes=None):
    conn = get_conn()
    c = conn.cursor()
    updates = ["status = ?"]
    params = [status]
    if confidence is not None: updates.append("confidence = ?"); params.append(confidence)
    if notes is not None: updates.append("notes = ?"); params.append(notes)
    updates.append("last_studied = ?"); params.append(date.today().isoformat()); params.append(topic_id)
    c.execute(f"UPDATE topics SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

def add_study_log(log_date, paper_id, hours, topic_text="", topic_id=None, key_takeaways="", mood="Normal", tags=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO study_logs (log_date, paper_id, topic_id, topic_text, hours, key_takeaways, mood, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (log_date.isoformat(), paper_id, topic_id, topic_text, hours, key_takeaways, mood, tags))
    conn.commit()
    conn.close()

def get_study_logs(limit=50):
    conn = get_conn()
    df = pd.read_sql(f"SELECT sl.*, p.short_name as paper FROM study_logs sl LEFT JOIN papers p ON sl.paper_id = p.id ORDER BY sl.log_date DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_daily_hours():
    conn = get_conn()
    df = pd.read_sql("SELECT log_date, SUM(hours) as total_hours FROM study_logs GROUP BY log_date ORDER BY log_date", conn)
    conn.close()
    return df

def add_mock_test(test_date, paper_id, test_type, score, max_score=200, feedback="", weak_areas="", time_taken=None):
    conn = get_conn()
    c = conn.cursor()
    percentage = (score / max_score * 100) if max_score > 0 else 0
    c.execute("INSERT INTO mock_tests (test_date, paper_id, test_type, score, max_score, percentage, feedback, weak_areas, time_taken_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (test_date.isoformat(), paper_id, test_type, score, max_score, percentage, feedback, weak_areas, time_taken))
    conn.commit()
    conn.close()

def get_mock_tests():
    conn = get_conn()
    df = pd.read_sql("SELECT mt.*, p.short_name as paper FROM mock_tests mt LEFT JOIN papers p ON mt.paper_id = p.id ORDER BY mt.test_date DESC", conn)
    conn.close()
    return df

def get_progress_summary():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total_topics, SUM(CASE WHEN status IN ('Completed', 'Revised') THEN 1 ELSE 0 END) as completed, AVG(confidence) as avg_confidence FROM topics")
    row = c.fetchone()
    total = row[0] or 0
    completed = row[1] or 0
    avg_conf = round(row[2] or 0, 1)
    progress_pct = round((completed / total * 100), 1) if total > 0 else 0
    c.execute("SELECT p.short_name, COUNT(t.id) as total, SUM(CASE WHEN t.status IN ('Completed', 'Revised') THEN 1 ELSE 0 END) as done FROM papers p LEFT JOIN topics t ON p.id = t.paper_id GROUP BY p.id ORDER BY p.id")
    paper_progress = []
    for r in c.fetchall():
        pct = round((r[2] / r[1] * 100), 1) if r[1] > 0 else 0
        paper_progress.append({"paper": r[0], "total": r[1], "done": r[2], "progress": pct})
    conn.close()
    return {"overall_progress": progress_pct, "total_topics": total, "completed_topics": completed, "avg_confidence": avg_conf, "paper_progress": paper_progress}

from datetime import timedelta
def calculate_streak():
    conn = get_conn()
    df = pd.read_sql("SELECT DISTINCT log_date FROM study_logs ORDER BY log_date", conn)
    conn.close()
    if df.empty: return 0
    df['log_date'] = pd.to_datetime(df['log_date']).dt.date
    studied_dates = set(df['log_date'].tolist())
    today = date.today()
    streak = 0
    current = today
    if today not in studied_dates:
        current = today - timedelta(days=1)
        if current not in studied_dates: return 0
    while current in studied_dates:
        streak += 1
        current = current - timedelta(days=1)
    return streak