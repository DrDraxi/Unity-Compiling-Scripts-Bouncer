# Unity Time Waste Statistics

This Python script finds Unity loading windows (containing "Compiling scripts" in their title) and makes them bounce around the screen like the classic DVD screensaver logo. It also tracks loading statistics, including frequency and duration.

When making this I said to myself *"Why fix the long loading issue when it can bounce instead?"*

## GIF

![Unity Window Bouncer in action](assets/images/bouncer.gif)

## Features

- Automatically detects Unity loading windows
- Makes the windows bounce around the screen like the DVD logo
- Detects collisions with screen edges
- Works with multiple monitors
- Runs indefinitely until manually stopped
- Tracks loading frequency and duration
- Provides a web dashboard with statistics and graphs

## Requirements

- Windows operating system
- Python 3.6+
- pywin32 package
- Flask (for the web dashboard)

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```
   .\venv\Scripts\activate
   ```
4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Window Bouncer

1. Make sure you have Unity open with a loading window
2. Run the script:
   ```
   python main.py
   ```
3. Press Ctrl+C to stop the script

### Statistics Dashboard

1. Run the statistics web dashboard in a separate terminal:
   ```
   python stats_web.py
   ```
2. A browser window will automatically open with the dashboard at http://localhost:5000
3. The dashboard automatically refreshes every minute

## Dashboard Features

- Summary cards showing today's and monthly loading statistics
- Hourly distribution chart for today's loadings
- Daily trend chart for the last 30 days
- Table of recent loading history

## How it Works

The main script detects Unity loading windows and:
1. Makes them bounce around the screen
2. Tracks when each loading starts and ends
3. Stores the data in a SQLite database

The stats_web.py script provides a web interface that:
1. Displays loading statistics with interactive charts
2. Auto-refreshes every minute to show the latest data

All data is stored locally in a unity_time_waste.db file.