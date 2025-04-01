import time
import random
import threading
import window_utils
import db_utils
from datetime import datetime

def main():
    # Initialize database
    db_utils.init_db()
    
    # Base movement speed (pixels per second)
    base_speed_x, base_speed_y = 320, 320  # Pixels per second
    
    # Update interval in seconds
    update_interval = 0.005
    
    # Track windows we've seen to maintain consistent movement
    tracked_windows = {}
    
    print("Looking for Unity compilation windows...")
    print("For statistics dashboard, run 'python stats_web.py' in a separate terminal")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            try:
                # If we don't have any windows to track, search for new ones
                if not tracked_windows:
                    # Get all monitors
                    monitors = window_utils.get_all_monitors()
                    
                    # Find target windows
                    target_windows = []
                    for title in ["Compiling Scripts", "Hold on", "Reloading domain"]:
                        windows = window_utils.find_target_windows(title)
                        if windows:
                            target_windows.extend(windows)
                            break  # Stop searching as soon as we find any matching window
                    
                    if not target_windows:
                        time.sleep(0.5)  # Short sleep when no windows found
                        continue
                    
                    # Add new windows
                    for window_info in target_windows:
                        hwnd = window_info['hwnd']
                        print(f"Found new window: {hwnd} - {window_info['title']}")
                        window_id = db_utils.add_compilation_window(window_info['title'])
                        tracked_windows[hwnd] = {
                            'speed_x': base_speed_x * random.uniform(0.8, 1.2),
                            'speed_y': base_speed_y * random.uniform(0.8, 1.2),
                            'last_move_time': time.time(),
                            'window_id': window_id
                        }
                
                # If we have no windows to track, continue searching
                if not tracked_windows:
                    continue
                
                # Get all monitors (needed for window movement)
                monitors = window_utils.get_all_monitors()
                
                # Move each window
                current_time = time.time()
                for hwnd in list(tracked_windows.keys()):
                    try:
                        # Get window position and size
                        try:
                            rect = window_utils.win32gui.GetWindowRect(hwnd)
                            x, y = rect[0], rect[1]
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                        except window_utils.pywintypes.error:
                            # Window is invalid, remove it and mark as ended
                            window_id = tracked_windows[hwnd]['window_id']
                            db_utils.end_compilation_window(window_id)
                            print(f"Window {hwnd} is invalid, removing")
                            del tracked_windows[hwnd]
                            continue
                        except Exception:
                            # Window is invalid, remove it and mark as ended
                            window_id = tracked_windows[hwnd]['window_id']
                            db_utils.end_compilation_window(window_id)
                            print(f"Window {hwnd} caused an error, removing")
                            del tracked_windows[hwnd]
                            continue
                        
                        # Get current monitor
                        current_monitor = window_utils.get_monitor_for_window(hwnd, monitors)
                        
                        # Get window-specific movement data
                        window_data = tracked_windows[hwnd]
                        
                        # Calculate deltaTime
                        delta_time = current_time - window_data['last_move_time']
                        
                        # Calculate movement distance based on deltaTime
                        move_x = window_data['speed_x'] * delta_time
                        move_y = window_data['speed_y'] * delta_time
                        
                        # Calculate new position
                        new_x = x + move_x
                        new_y = y + move_y
                        
                        # Check for collisions with monitor edges
                        hit_edge = False
                        
                        # Right edge
                        if new_x + width > current_monitor['right']:
                            new_x = current_monitor['right'] - width
                            window_data['speed_x'] = -window_data['speed_x'] * random.uniform(0.9, 1.1)
                            hit_edge = True
                        
                        # Left edge
                        elif new_x < current_monitor['left']:
                            new_x = current_monitor['left']
                            window_data['speed_x'] = -window_data['speed_x'] * random.uniform(0.9, 1.1)
                            hit_edge = True
                        
                        # Bottom edge
                        if new_y + height > current_monitor['bottom']:
                            new_y = current_monitor['bottom'] - height
                            window_data['speed_y'] = -window_data['speed_y'] * random.uniform(0.9, 1.1)
                            hit_edge = True
                        
                        # Top edge
                        elif new_y < current_monitor['top']:
                            new_y = current_monitor['top']
                            window_data['speed_y'] = -window_data['speed_y'] * random.uniform(0.9, 1.1)
                            hit_edge = True

                        # Move the window
                        window_utils.safe_move_window(hwnd, new_x, new_y, width, height)
                        window_data['last_move_time'] = current_time
                    
                    except window_utils.pywintypes.error as e:
                        # Window is invalid, remove it and mark as ended
                        window_id = tracked_windows[hwnd]['window_id']
                        db_utils.end_compilation_window(window_id)
                        print(f"Window {hwnd} caused a pywintypes error, removing: {e}")
                        del tracked_windows[hwnd]
                    except Exception as e:
                        # Window is invalid, remove it and mark as ended
                        window_id = tracked_windows[hwnd]['window_id']
                        db_utils.end_compilation_window(window_id)
                        print(f"Error processing window {hwnd}, removing: {e}")
                        del tracked_windows[hwnd]
                
                # Show today's stats if we have no tracked windows
                if not tracked_windows:
                    stats = db_utils.get_today_stats()
                    print(f"\nToday's compilation stats: {stats['count']} compilations, total time: {stats['formatted_time']}")
                    print("For detailed statistics, run 'python stats_web.py' in a separate terminal")
                
                time.sleep(update_interval)
            
            except window_utils.pywintypes.error as e:
                print(f"Error in main loop (pywintypes): {e}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 