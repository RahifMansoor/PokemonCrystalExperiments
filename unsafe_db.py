from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

# Basic HTML template with a form and results display
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SQL Injection Demo</title>
</head>
<body>
    <h1>SQL Injection Demonstration</h1>
    <!-- Unsafe Form -->
    <h2>Unsafe Query</h2>
    <form action="/unsafe/users" method="get">
        <input type="text" name="username" placeholder="Enter username">
        <input type="submit" value="Search">
    </form>
    <!-- Display Results -->
    {% if users %}
        <h3>Results:</h3>
        <pre>{{ users }}</pre>
    {% endif %}
    <!-- SQL Injection Examples -->
    <h3>Try these SQL injection examples:</h3>
    <ul>
        <li>Normal query: <code>admin</code></li>
        <li>Get all users: <code>admin' OR '1'='1</code></li>
        <li>Attempt table drop: <code>admin'; DROP TABLE users;--</code></li>
    </ul>
</body>
</html>
"""

def init_db():
    # Initialize database with sample users
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'secretpass123')")
    c.execute("INSERT OR IGNORE INTO users VALUES (2, 'user', 'password123')")
    conn.commit()
    conn.close()

@app.route('/')
def home():
    # Render the main page without any results
    return render_template_string(HTML_TEMPLATE, users=None)

@app.route('/unsafe/users')
@app.route('/unsafe/users')
def unsafe_query():
    username = request.args.get('username', '')
    # VULNERABILITY: Direct string interpolation in SQL query
    # This allows attackers to modify the query structure
    query = f"SELECT * FROM users WHERE username = '{username}'"

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        # Using executescript to allow multiple SQL statements (like DROP TABLE)
        if "DROP" in query or "DELETE" in query or "--" in query:
            c.executescript(query)  # Allows multiple SQL statements to run
            results = "Table dropped or modified successfully."
        else:
            results = c.execute(query).fetchall()

        return render_template_string(HTML_TEMPLATE, users=results)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, users=f"Error: {str(e)}")
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    # Run on port 5000 in debug mode to see errors
    app.run(port=5000, debug=True)
