import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('study_buddy.db')
conn.row_factory = sqlite3.Row  # This enables column access by name
cursor = conn.cursor()

# Get all users
print("=== USERS ===")
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
for user in users:
    # Check if password_hash exists in the user row
    password_info = f", Password Hash: {user['password_hash'][:10]}..." if 'password_hash' in user.keys() else ""
    print(f"ID: {user['id']}, Name: {user['name']}, Class: {user['class']}{password_info}, Created: {user['created_at']}")

# Get all queries
print("\n=== QUERIES ===")
cursor.execute("""
    SELECT q.id, q.user_id, q.topic, u.name, q.created_at 
    FROM queries q
    JOIN users u ON q.user_id = u.id
    ORDER BY q.created_at DESC
""")
queries = cursor.fetchall()
for query in queries:
    print(f"ID: {query['id']}, Topic: {query['topic']}, User: {query['name']}, Created: {query['created_at']}")

# Close the connection
conn.close()

print("\nDatabase check complete.")