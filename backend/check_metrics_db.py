import sqlite3
import json

def check_metrics():
    conn = sqlite3.connect('workana.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profile_metrics'")
    if not cursor.fetchone():
        print("Table profile_metrics does not exist")
        return

    cursor.execute("SELECT * FROM profile_metrics")
    rows = cursor.fetchall()
    
    columns = [description[0] for description in cursor.description]
    
    results = []
    for row in rows:
        results.append(dict(zip(columns, row)))
        
    print(json.dumps(results, indent=2))
    conn.close()

if __name__ == "__main__":
    check_metrics()
