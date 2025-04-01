import sqlite3
from datetime import datetime
import os

DB_PATH = "compilation_stats.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE compilation_windows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_datetime DATETIME NOT NULL,
                end_datetime DATETIME,
                window_title TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

def add_compilation_window(window_title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO compilation_windows (start_datetime, window_title)
        VALUES (?, ?)
    ''', (datetime.now(), window_title))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def end_compilation_window(window_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE compilation_windows 
        SET end_datetime = ?
        WHERE id = ? AND end_datetime IS NULL
    ''', (datetime.now(), window_id))
    conn.commit()
    conn.close()

def get_today_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT COUNT(*) as count,
               SUM(strftime('%s', COALESCE(end_datetime, datetime('now'))) - strftime('%s', start_datetime)) as total_seconds
        FROM compilation_windows
        WHERE date(start_datetime) = date('now')
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    count = result[0] or 0
    total_seconds = result[1] or 0
    
    return {
        'count': count,
        'total_seconds': total_seconds,
        'formatted_time': f"{total_seconds // 60}m {total_seconds % 60}s"
    }

def get_last_10_days_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            date(start_datetime) as date,
            COUNT(*) as count,
            SUM(strftime('%s', COALESCE(end_datetime, datetime('now'))) - strftime('%s', start_datetime)) as total_seconds
        FROM compilation_windows
        WHERE start_datetime >= date('now', '-10 days')
        GROUP BY date(start_datetime)
        ORDER BY date DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'date': row[0],
        'count': row[1],
        'total_seconds': row[2] or 0,
        'formatted_time': f"{(row[2] or 0) // 60}m {(row[2] or 0) % 60}s"
    } for row in results]

def get_current_month_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as count,
            SUM(strftime('%s', COALESCE(end_datetime, datetime('now'))) - strftime('%s', start_datetime)) as total_seconds
        FROM compilation_windows
        WHERE strftime('%Y-%m', start_datetime) = strftime('%Y-%m', 'now')
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    count = result[0] or 0
    total_seconds = result[1] or 0
    
    return {
        'count': count,
        'total_seconds': total_seconds,
        'formatted_time': f"{total_seconds // 60}m {total_seconds % 60}s"
    } 