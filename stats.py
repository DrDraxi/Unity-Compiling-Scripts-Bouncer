from db_utils import get_today_stats, get_last_10_days_stats, get_current_month_stats

def display_today_stats():
    stats = get_today_stats()
    print("\nToday's Compilation Stats:")
    print(f"Total compilations: {stats['count']}")
    print(f"Total compilation time: {stats['formatted_time']}")

def display_last_10_days():
    stats = get_last_10_days_stats()
    print("\nLast 10 Days Compilation Stats:")
    print("-" * 50)
    for day in stats:
        print(f"Date: {day['date']}")
        print(f"Compilations: {day['count']}")
        print(f"Total time: {day['formatted_time']}")
        print("-" * 50)

def display_current_month():
    stats = get_current_month_stats()
    print("\nCurrent Month Compilation Stats:")
    print(f"Total compilations: {stats['count']}")
    print(f"Total compilation time: {stats['formatted_time']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "today":
            display_today_stats()
        elif command == "last10":
            display_last_10_days()
        elif command == "month":
            display_current_month()
        else:
            print("Invalid command. Use: today, last10, or month")
    else:
        print("Please specify a command: today, last10, or month") 