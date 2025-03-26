from flask import Flask, request
import sqlite3

app = Flask(__name__)

def setup_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    print("[DEBUG] Creating database...")
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT)''')
    
    # Check if table is empty
    if not c.execute("SELECT * FROM users").fetchall():
        sample_users = [
            ('admin', 'admin@example.com'),
            ('john_doe', 'john@example.com'),
            ('jane_smith', 'jane@example.com'),
            ('alice', 'alice@example.com'),
            ('bob', 'bob@example.com')
        ]
        c.executemany('INSERT INTO users (name, email) VALUES (?, ?)', sample_users)
        print("[DEBUG] Inserted sample users")
        conn.commit()
    
    conn.close()

@app.route('/')
def index():
    return '''
    <h1>User Search (Vulnerable to SQL Injection)</h1>
    <form method="GET" action="/search">
        <input type="text" name="name" placeholder="Search by name">
        <input type="submit" value="Search">
    </form>
    <br>
    <form action="/reset" method="POST">
        <input type="submit" value="Reset Database">
    </form>
    <br>
    '''

@app.route('/search')
def search():
    name = request.args.get('name', '')
    print("\n[DEBUG] User input:", name)
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        if "OR" in name:
            query = f"SELECT * FROM users WHERE name = '{name}'"
            print("[DEBUG] OR injection query:", query)
            results = c.execute(query).fetchall()
        
        elif "DELETE" in name:
            statements = name.split(';')
            for stmt in statements:
                if stmt.strip():  
                    query = f"SELECT * FROM users WHERE name = '{stmt}'"
                    print("[DEBUG] Statement:", query)
                    try:
                        c.execute(query)
                    except sqlite3.Error as e:
                        print("[DEBUG] Error executing SELECT:", e)
                    
                    if "DELETE" in stmt:
                        delete_query = "DELETE FROM users"
                        print("[DEBUG] Executing DELETE:", delete_query)
                        c.execute(delete_query)
                        conn.commit()
            results = []  
            
        else:
            query = f"SELECT * FROM users WHERE name = '{name}'"
            print("[DEBUG] Normal query:", query)
            results = c.execute(query).fetchall()
            
    except sqlite3.Error as e:
        print("[DEBUG] Database error:", e)
        return f"Error: {str(e)}"
    finally:
        conn.close()
    
    output = '<h1>Search Results</h1>'
    output += '<a href="/">Back to Search</a><br><br>'
    
    if not results:
        output += '<p>No users found (or all users were deleted)</p>'
    else:
        output += '<table border="1"><tr><th>ID</th><th>Name</th><th>Email</th></tr>'
        for row in results:
            output += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>'
        output += '</table>'
    
    return output

@app.route('/reset', methods=['POST'])
def reset():
    print("\n[DEBUG] Resetting database...")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS users')
    conn.commit()
    conn.close()
    
    setup_database()
    return 'Database reset! <a href="/">Back to Search</a>'

if __name__ == '__main__':
    setup_database()
    print("\n[DEBUG] Starting vulnerable server on port 5000...")
    app.run(port=5000, debug=True)
