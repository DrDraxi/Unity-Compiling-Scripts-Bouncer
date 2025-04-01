from flask import Flask, render_template, jsonify
import db_utils
from datetime import datetime, timedelta
import os
import webbrowser
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/today')
def today_stats():
    return jsonify(db_utils.get_today_stats())

@app.route('/api/last10days')
def last_10_days_stats():
    return jsonify(db_utils.get_last_10_days_stats())

@app.route('/api/month')
def month_stats():
    return jsonify(db_utils.get_current_month_stats())

@app.route('/api/hourly_today')
def hourly_today():
    conn = db_utils.sqlite3.connect(db_utils.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            strftime('%H', start_datetime) as hour,
            COUNT(*) as count,
            SUM(CASE 
                WHEN end_datetime IS NOT NULL 
                THEN strftime('%s', end_datetime) - strftime('%s', start_datetime)
                ELSE 0 
            END) as total_seconds,
            SUM(CASE WHEN end_datetime IS NULL THEN 1 ELSE 0 END) as in_progress
        FROM compilation_windows
        WHERE date(start_datetime) = date('now')
        GROUP BY strftime('%H', start_datetime)
        ORDER BY hour
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Fill in missing hours with zeros
    hours_data = {str(h).zfill(2): {"count": 0, "total_seconds": 0, "in_progress": 0} for h in range(24)}
    
    for row in results:
        hour = row[0]
        hours_data[hour] = {
            "count": row[1],
            "total_seconds": row[2] or 0,
            "in_progress": row[3] or 0
        }
    
    return jsonify({
        "hours": list(hours_data.keys()),
        "counts": [d["count"] for d in hours_data.values()],
        "durations": [d["total_seconds"] / 60 for d in hours_data.values()],  # Convert to minutes
        "in_progress": [d["in_progress"] for d in hours_data.values()]
    })

@app.route('/api/daily_trend')
def daily_trend():
    # Get the last 30 days of data
    conn = db_utils.sqlite3.connect(db_utils.DB_PATH)
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
        FROM compilation_windows
        WHERE start_datetime >= date('now', '-30 days')
        GROUP BY date(start_datetime)
        ORDER BY date
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Fill in missing days with zeros
    today = datetime.now().date()
    days_data = {}
    
    for i in range(30, -1, -1):
        day = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        days_data[day] = {"count": 0, "total_seconds": 0, "in_progress": 0}
    
    for row in results:
        date_str = row[0]
        days_data[date_str] = {
            "count": row[1],
            "total_seconds": row[2] or 0,
            "in_progress": row[3] or 0
        }
    
    return jsonify({
        "dates": list(days_data.keys()),
        "counts": [d["count"] for d in days_data.values()],
        "durations": [d["total_seconds"] / 60 for d in days_data.values()],  # Convert to minutes
        "in_progress": [d["in_progress"] for d in days_data.values()]
    })

def open_browser():
    """Open the browser after a short delay"""
    def _open_browser():
        webbrowser.open('http://localhost:5000')
        print("Web dashboard is available at http://localhost:5000")
    
    thread = threading.Timer(1.5, _open_browser)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    # Initialize the database if needed
    db_utils.init_db()
    
    # Make sure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Open browser automatically
    open_browser()
    
    # Start the Flask app
    print("Starting web dashboard...")
    app.run(debug=False, host='0.0.0.0', port=5000) 