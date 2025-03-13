import win32gui
import win32con
import win32api
import ctypes
import pywintypes
from ctypes import wintypes

def get_window_text(hwnd):
    """Get the text of a window safely with timeout."""
    try:
        # First try the direct method
        try:
            return win32gui.GetWindowText(hwnd)
        except pywintypes.error:
            # If direct method fails, try with timeout
            length, _ = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0, 
                                                  win32con.SMTO_ABORTIFHUNG, 1000)
            if length == 0:
                return ""
                
            length += 1  # Add space for null terminator
            
            # Create buffer and get text with timeout
            buffer = ctypes.create_unicode_buffer(length)
            result, _ = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETTEXT, length, buffer, 
                                                  win32con.SMTO_ABORTIFHUNG, 1000)
            return buffer.value
    except pywintypes.error:
        return "[Unresponsive Window]"
    except Exception as e:
        return f"[Error: {str(e)}]"

def is_window_responsive(hwnd, timeout=0.5):
    """Check if a window is responsive with a timeout."""
    try:
        result, _ = win32gui.SendMessageTimeout(hwnd, win32con.WM_NULL, 0, 0, 
                                              win32con.SMTO_ABORTIFHUNG, int(timeout * 1000))
        return True
    except pywintypes.error:
        return False

def get_all_windows():
    """Get all visible windows with their names."""
    windows = []
    
    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            try:
                window_text = get_window_text(hwnd)
                if window_text:  # Only include windows with text
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'rect': rect,
                        'size': (width, height)
                    })
            except pywintypes.error:
                # Skip windows that cause errors
                pass
    
    win32gui.EnumWindows(enum_callback, None)
    return windows

def find_target_windows(title_contains=None):
    """Find windows that match specific criteria."""
    results = []
    
    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            window_text = get_window_text(hwnd)
            
            # Check if window matches our criteria
            if title_contains and title_contains in window_text:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                
                results.append({
                    'hwnd': hwnd,
                    'title': window_text,
                    'rect': rect,
                    'size': (width, height)
                })
    
    win32gui.EnumWindows(enum_callback, results)
    return results

def get_all_monitors():
    """Get information about all monitors."""
    monitors = []
    
    def callback(monitor, dc, rect, data):
        rct = rect.contents
        monitors.append({
            'handle': monitor,
            'left': rct.left,
            'top': rct.top,
            'right': rct.right,
            'bottom': rct.bottom,
            'width': rct.right - rct.left,
            'height': rct.bottom - rct.top
        })
        return True
    
    # Define callback function type
    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(wintypes.RECT),
        ctypes.c_double
    )
    
    # Enumerate monitors
    ctypes.windll.user32.EnumDisplayMonitors(
        None, None, 
        MONITORENUMPROC(callback), 
        0
    )
    
    return monitors

def is_point_in_monitor(x, y, monitor):
    """Check if a point is within a monitor's bounds."""
    return (monitor['left'] <= x <= monitor['right'] and 
            monitor['top'] <= y <= monitor['bottom'])

def get_monitor_for_point(x, y, monitors):
    """Get the monitor that contains a specific point."""
    for monitor in monitors:
        if is_point_in_monitor(x, y, monitor):
            return monitor
    return monitors[0] if monitors else None  # Default to first monitor

def get_monitor_for_window(hwnd, monitors):
    """Get the monitor that contains a window."""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        # Use the center point of the window
        center_x = (rect[0] + rect[2]) // 2
        center_y = (rect[1] + rect[3]) // 2
        
        return get_monitor_for_point(center_x, center_y, monitors)
    except pywintypes.error:
        return monitors[0] if monitors else None  # Default to first monitor

def safe_move_window(hwnd, x, y, width, height):
    """Move a window safely, handling errors."""
    try:
        # Check if window exists and is responsive
        if win32gui.IsWindow(hwnd) and is_window_responsive(hwnd):
            # Get current position
            current_rect = win32gui.GetWindowRect(hwnd)
            current_width = current_rect[2] - current_rect[0]
            current_height = current_rect[3] - current_rect[1]
            
            # Only move if position or size has changed
            if (current_rect[0] != int(x) or current_rect[1] != int(y) or 
                current_width != width or current_height != height):
                
                # Move the window - ensure coordinates are integers
                win32gui.MoveWindow(hwnd, int(x), int(y), int(width), int(height), True)
                return True
        return False
    except pywintypes.error:
        return False 