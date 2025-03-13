import window_utils

def main():
    print("Listing all visible windows sorted by name:")
    print("-" * 80)
    
    windows = window_utils.get_all_windows()
    
    # Sort windows by title
    sorted_windows = sorted(windows, key=lambda w: w['title'].lower())
    
    # Print the sorted list
    for i, window in enumerate(sorted_windows, 1):
        print(f"{i}. HWND: {window['hwnd']}")
        print(f"   Title: {window['title']}")
        print(f"   Position: {window['rect']}")
        print(f"   Size: {window['size'][0]}x{window['size'][1]}")
        print("-" * 80)
    
    print(f"Total windows found: {len(sorted_windows)}")

if __name__ == "__main__":
    main() 