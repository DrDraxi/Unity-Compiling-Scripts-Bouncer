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
            SUM(strftime('%s', COALESCE(end_datetime, datetime('now'))) - strftime('%s', start_datetime)) as total_seconds
        FROM compilation_windows
        WHERE date(start_datetime) = date('now')
        GROUP BY strftime('%H', start_datetime)
        ORDER BY hour
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    # Fill in missing hours with zeros
    hours_data = {str(h).zfill(2): {"count": 0, "total_seconds": 0} for h in range(24)}
    
    for row in results:
        hour = row[0]
        hours_data[hour] = {
            "count": row[1],
            "total_seconds": row[2] or 0
        }
    
    return jsonify({
        "hours": list(hours_data.keys()),
        "counts": [d["count"] for d in hours_data.values()],
        "durations": [d["total_seconds"] / 60 for d in hours_data.values()]  # Convert to minutes
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
            SUM(strftime('%s', COALESCE(end_datetime, datetime('now'))) - strftime('%s', start_datetime)) as total_seconds
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
        days_data[day] = {"count": 0, "total_seconds": 0}
    
    for row in results:
        date_str = row[0]
        days_data[date_str] = {
            "count": row[1],
            "total_seconds": row[2] or 0
        }
    
    return jsonify({
        "dates": list(days_data.keys()),
        "counts": [d["count"] for d in days_data.values()],
        "durations": [d["total_seconds"] / 60 for d in days_data.values()]  # Convert to minutes
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
    
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Create templates if they don't exist
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unity Compilation Stats</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            background-color: #f8f9fa;
            padding-top: 20px;
        }
        .card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .card-header {
            background-color: #6c757d;
            color: white;
            border-radius: 10px 10px 0 0 !important;
            padding: 10px 15px;
            font-weight: bold;
        }
        .summary-value {
            font-size: 24px;
            font-weight: bold;
            color: #495057;
        }
        .summary-label {
            color: #6c757d;
            font-size: 14px;
        }
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Unity Compilation Statistics</h1>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Today's Stats</div>
                    <div class="card-body text-center">
                        <div class="summary-value" id="today-count">-</div>
                        <div class="summary-label">Compilations Today</div>
                        <hr>
                        <div class="summary-value" id="today-time">-</div>
                        <div class="summary-label">Total Time</div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Monthly Stats</div>
                    <div class="card-body text-center">
                        <div class="summary-value" id="month-count">-</div>
                        <div class="summary-label">Compilations This Month</div>
                        <hr>
                        <div class="summary-value" id="month-time">-</div>
                        <div class="summary-label">Total Time</div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Average</div>
                    <div class="card-body text-center">
                        <div class="summary-value" id="avg-daily">-</div>
                        <div class="summary-label">Average Daily Compilations</div>
                        <hr>
                        <div class="summary-value" id="avg-duration">-</div>
                        <div class="summary-label">Average Compilation Duration</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Hourly Distribution (Today)</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="hourlyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Daily Trend (Last 30 Days)</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="dailyTrendChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Recent Compilations</div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Compilations</th>
                                        <th>Total Time</th>
                                        <th>Avg Time</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-days">
                                    <!-- Data will be filled by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="mt-4 mb-4 text-center text-muted">
            <small>Last updated: <span id="last-updated">-</span></small>
        </footer>
    </div>

    <script>
        // Chart objects
        let hourlyChart = null;
        let dailyTrendChart = null;
        
        // Format time function
        function formatTime(seconds) {
            if (seconds === 0) return '0s';
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            let result = '';
            if (hours > 0) result += hours + 'h ';
            if (minutes > 0) result += minutes + 'm ';
            if (secs > 0 && hours === 0) result += secs + 's';
            
            return result.trim();
        }
        
        // Load all data
        function loadData() {
            // Update timestamp
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
            
            // Fetch today's stats
            fetch('/api/today')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('today-count').textContent = data.count;
                    document.getElementById('today-time').textContent = formatTime(data.total_seconds);
                });
                
            // Fetch monthly stats
            fetch('/api/month')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('month-count').textContent = data.count;
                    document.getElementById('month-time').textContent = formatTime(data.total_seconds);
                    
                    // Calculate averages (assuming 30 days in a month for simplicity)
                    const now = new Date();
                    const daysIntoMonth = now.getDate();
                    const avgDaily = data.count / daysIntoMonth;
                    document.getElementById('avg-daily').textContent = avgDaily.toFixed(1);
                    
                    if (data.count > 0) {
                        const avgDuration = data.total_seconds / data.count;
                        document.getElementById('avg-duration').textContent = formatTime(avgDuration);
                    } else {
                        document.getElementById('avg-duration').textContent = '-';
                    }
                });
                
            // Fetch hourly data and update chart
            fetch('/api/hourly_today')
                .then(response => response.json())
                .then(data => {
                    updateHourlyChart(data);
                });
                
            // Fetch daily trend and update chart
            fetch('/api/daily_trend')
                .then(response => response.json())
                .then(data => {
                    updateDailyTrendChart(data);
                });
                
            // Fetch last 10 days for table
            fetch('/api/last10days')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('recent-days');
                    tableBody.innerHTML = '';
                    
                    data.forEach(day => {
                        const row = document.createElement('tr');
                        
                        const dateCell = document.createElement('td');
                        dateCell.textContent = new Date(day.date).toLocaleDateString();
                        row.appendChild(dateCell);
                        
                        const countCell = document.createElement('td');
                        countCell.textContent = day.count;
                        row.appendChild(countCell);
                        
                        const timeCell = document.createElement('td');
                        timeCell.textContent = formatTime(day.total_seconds);
                        row.appendChild(timeCell);
                        
                        const avgCell = document.createElement('td');
                        if (day.count > 0) {
                            avgCell.textContent = formatTime(day.total_seconds / day.count);
                        } else {
                            avgCell.textContent = '-';
                        }
                        row.appendChild(avgCell);
                        
                        tableBody.appendChild(row);
                    });
                });
        }
        
        // Update hourly chart
        function updateHourlyChart(data) {
            const ctx = document.getElementById('hourlyChart').getContext('2d');
            
            if (hourlyChart) {
                hourlyChart.destroy();
            }
            
            hourlyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.hours,
                    datasets: [
                        {
                            label: 'Number of Compilations',
                            data: data.counts,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Compilation Time (minutes)',
                            data: data.durations,
                            backgroundColor: 'rgba(255, 99, 132, 0.5)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1,
                            type: 'line',
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Count'
                            }
                        },
                        y1: {
                            beginAtZero: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false
                            },
                            title: {
                                display: true,
                                text: 'Minutes'
                            }
                        }
                    }
                }
            });
        }
        
        // Update daily trend chart
        function updateDailyTrendChart(data) {
            const ctx = document.getElementById('dailyTrendChart').getContext('2d');
            
            // Format dates to be more readable
            const formattedDates = data.dates.map(d => {
                const date = new Date(d);
                return date.getMonth() + 1 + '/' + date.getDate();
            });
            
            if (dailyTrendChart) {
                dailyTrendChart.destroy();
            }
            
            dailyTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: formattedDates,
                    datasets: [
                        {
                            label: 'Compilations',
                            data: data.counts,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            tension: 0.1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Duration (minutes)',
                            data: data.durations,
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            borderColor: 'rgba(153, 102, 255, 1)',
                            tension: 0.1,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Count'
                            }
                        },
                        y1: {
                            beginAtZero: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false
                            },
                            title: {
                                display: true,
                                text: 'Minutes'
                            }
                        }
                    }
                }
            });
        }
        
        // Initial load
        loadData();
        
        // Auto-refresh every minute
        setInterval(loadData, 60000);
    </script>
</body>
</html>''')
    
    # Open browser automatically
    open_browser()
    
    # Start the Flask app
    print("Starting web dashboard...")
    app.run(debug=True, host='0.0.0.0', port=5000) 