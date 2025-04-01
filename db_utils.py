import sqlite3
from datetime import datetime
import os

DB_PATH = "unity_time_waste.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE loading_windows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_datetime DATETIME NOT NULL,
                end_datetime DATETIME,
                window_title TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

def add_loading_window(window_title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO loading_windows (start_datetime, window_title)
        VALUES (?, ?)
    ''', (datetime.now(), window_title))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def end_loading_window(window_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE loading_windows 
        SET end_datetime = ?
        WHERE id = ? AND end_datetime IS NULL
    ''', (datetime.now(), window_id))
    conn.commit()
    conn.close()

def get_today_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().date()
    
    # Count all loadings
    cursor.execute('''
        SELECT COUNT(*) 
        FROM loading_windows
        WHERE date(start_datetime) = date('now')
    ''')
    count = cursor.fetchone()[0] or 0
    
    # Calculate time only for completed loadings
    cursor.execute('''
        SELECT 
            SUM(CASE 
                WHEN end_datetime IS NOT NULL 
                THEN strftime('%s', end_datetime) - strftime('%s', start_datetime)
                ELSE 0 
            END) as total_seconds
        FROM loading_windows
        WHERE date(start_datetime) = date('now')
    ''')
    total_seconds = cursor.fetchone()[0] or 0
    
    # Get count of in-progress loadings
    cursor.execute('''
        SELECT COUNT(*) 
        FROM loading_windows
        WHERE date(start_datetime) = date('now') AND end_datetime IS NULL
    ''')
    in_progress = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'count': count,
        'in_progress': in_progress,
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
            SUM(CASE 
                WHEN end_datetime IS NOT NULL 
                THEN strftime('%s', end_datetime) - strftime('%s', start_datetime)
                ELSE 0 
            END) as total_seconds,
            SUM(CASE WHEN end_datetime IS NULL THEN 1 ELSE 0 END) as in_progress
        FROM loading_windows
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
        'in_progress': row[3] or 0,
        'formatted_time': f"{(row[2] or 0) // 60}m {(row[2] or 0) % 60}s"
    } for row in results]

def get_current_month_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as count,
            SUM(CASE 
                WHEN end_datetime IS NOT NULL 
                THEN strftime('%s', end_datetime) - strftime('%s', start_datetime)
                ELSE 0 
            END) as total_seconds,
            SUM(CASE WHEN end_datetime IS NULL THEN 1 ELSE 0 END) as in_progress
        FROM loading_windows
        WHERE strftime('%Y-%m', start_datetime) = strftime('%Y-%m', 'now')
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    count = result[0] or 0
    total_seconds = result[1] or 0
    in_progress = result[2] or 0
    
    return {
        'count': count,
        'in_progress': in_progress,
        'total_seconds': total_seconds,
        'formatted_time': f"{total_seconds // 60}m {total_seconds % 60}s"
    } 