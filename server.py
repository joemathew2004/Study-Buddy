from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import sqlite3
import json
import hashlib
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_ENDPOINT = os.getenv("API_ENDPOINT")

# Database setup
DB_PATH = 'study_buddy.db'

def hash_password(password):
    """Simple password hashing using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Create users table with password field
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    else:
        # Check if password_hash column exists
        try:
            cursor.execute("SELECT password_hash FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Add password_hash column to existing table
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            # Set default password for existing users
            cursor.execute("UPDATE users SET password_hash = ?", (hash_password("password"),))
    
    # Create queries table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        topic TEXT NOT NULL,
        notes TEXT,
        qa TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/api/user/register', methods=['POST'])
def register_user():
    data = request.json
    name = data.get('name')
    user_class = data.get('class')
    password = data.get('password')
    
    if not name or not user_class or not password:
        return jsonify({"error": "Name, class, and password are required"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE name = ? AND class = ?", (name, user_class))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({"error": "A user with this name and class already exists"}), 409
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Create new user
    cursor.execute(
        "INSERT INTO users (name, class, password_hash) VALUES (?, ?, ?)", 
        (name, user_class, password_hash)
    )
    conn.commit()
    user_id = cursor.lastrowid
    
    conn.close()
    
    return jsonify({
        "user_id": user_id,
        "name": name,
        "class": user_class,
        "message": "User registered successfully"
    })

@app.route('/api/user/login', methods=['POST'])
def login_user():
    data = request.json
    name = data.get('name')
    user_class = data.get('class')
    password = data.get('password')
    
    if not name or not user_class or not password:
        return jsonify({"error": "Name, class, and password are required"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Check if user exists with matching password
    cursor.execute(
        "SELECT id FROM users WHERE name = ? AND class = ? AND password_hash = ?", 
        (name, user_class, password_hash)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401
    
    user_id = user[0]
    
    # Get user's previous queries
    cursor.execute("""
        SELECT id, topic, notes, qa, created_at 
        FROM queries 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    
    queries = []
    for row in cursor.fetchall():
        queries.append({
            "id": row[0],
            "topic": row[1],
            "notes": row[2],
            "qa": row[3],
            "created_at": row[4]
        })
    
    conn.close()
    
    return jsonify({
        "user_id": user_id,
        "name": name,
        "class": user_class,
        "previous_queries": queries
    })

@app.route('/api/generate', methods=['POST'])
def generate_study_material():
    # Get the topic and user_id from the request
    data = request.json
    print("Received generate request:", data)
    topic = data.get('topic')
    user_id = data.get('user_id')
    
    print(f"Processing topic: {topic}, user_id: {user_id}")
    
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
        
    # Enhanced inappropriate content filtering
    inappropriate_keywords = [
        'porn', 'sex', 'nude', 'naked', 'adult', 'xxx', 'erotic', 'sexual', 'intercourse',
        'kill', 'murder', 'suicide', 'death', 'die', 'terrorist', 'bomb', 'explosion', 'attack',
        'racism', 'nazi', 'hitler', 'hate', 'discrimination', 'supremacy',
        'drugs', 'cocaine', 'heroin', 'meth', 'marijuana', 'weed', 'cannabis', 'addiction',
        'weapon', 'gun', 'rifle', 'pistol', 'knife', 'sword', 'violence', 'fight', 'war',
        'torture', 'abuse', 'rape', 'assault', 'harassment', 'bullying',
        'gambling', 'casino', 'betting', 'alcohol', 'beer', 'wine', 'drunk',
        'curse', 'damn', 'hell', 'shit', 'fuck', 'bitch', 'ass', 'stupid', 'idiot'
    ]
    
    # Convert to lowercase for case-insensitive matching
    topic_lower = topic.lower()
    
    # Check if any inappropriate keywords are in the topic
    for keyword in inappropriate_keywords:
        if keyword in topic_lower:
            return jsonify({
                "error": "Inappropriate content",
                "message": "⚠️ This topic contains inappropriate content. I can only help with educational topics suitable for students.",
                "notes": "I cannot provide study material on topics with inappropriate language or content.",
                "qa": "Please use appropriate language and choose educational topics like science, history, literature, or mathematics."
            }), 403
    
    # Enhanced person checking with stricter validation
    import re
    person_patterns = [
        r'^who is ', r'^who was ', r'^about ', r'^biography of ', r'^tell me about ',
        r'^information about ', r'^facts about ', r'^history of ', r'^life of '
    ]
    
    is_person_query = any(re.match(pattern, topic_lower) for pattern in person_patterns)
    
    # Also check if it's just a name (common pattern for person queries)
    words = topic_lower.split()
    if len(words) <= 3 and all(word.isalpha() and word.istitle() for word in topic.split()):
        is_person_query = True
    
    if is_person_query:
        # List of definitely known historical/famous people
        famous_people = [
            'albert einstein', 'isaac newton', 'leonardo da vinci', 'shakespeare', 'napoleon',
            'abraham lincoln', 'george washington', 'martin luther king', 'gandhi', 'nelson mandela',
            'winston churchill', 'franklin roosevelt', 'john kennedy', 'thomas edison', 'nikola tesla',
            'marie curie', 'charles darwin', 'galileo galilei', 'aristotle', 'plato', 'socrates',
            'mozart', 'beethoven', 'bach', 'picasso', 'van gogh', 'michelangelo',
            'cleopatra', 'julius caesar', 'alexander the great', 'genghis khan',
            'steve jobs', 'bill gates', 'mark twain', 'charles dickens', 'jane austen'
        ]
        
        # Check if the topic contains any famous person's name
        topic_clean = re.sub(r'^(who is |who was |about |biography of |tell me about |information about |facts about |history of |life of )', '', topic_lower).strip()
        
        is_famous = any(famous_name in topic_clean for famous_name in famous_people)
        
        if not is_famous:
            return jsonify({
                "error": "Unknown person",
                "message": "🤔 I don't have reliable information about this person.",
                "notes": "I can only provide information about widely recognized historical personalities, scientists, artists, and world leaders.",
                "qa": "Try asking about: Albert Einstein, Mahatma Gandhi, William Shakespeare, Marie Curie, Leonardo da Vinci, or other famous historical figures."
            }), 403
    
    # Prepare the request to Groq API
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a strict educational assistant for students in grades 1-12. CRITICAL RULES:\n\n1. ONLY provide information you are 100% certain about. If you have ANY doubt, refuse to answer.\n2. NEVER generate content about inappropriate, violent, adult, or harmful topics.\n3. For people: ONLY discuss widely known historical figures, scientists, world leaders, or artists. If unsure about a person, refuse.\n4. Keep all content age-appropriate and educational.\n5. If a topic seems inappropriate or you're uncertain, respond with 'I cannot provide reliable information on this topic.'\n\nWhen you do provide content, structure it as:\n\nNotes:\n[Clear, factual paragraphs with single blank lines between them]\n\nQuestions & Answers:\n1. Question?\nAnswer: The answer.\n\n2. Next question?\nAnswer: The next answer.\n\nEnsure all content is factual, educational, and appropriate for students. When in doubt, don't provide the information."
            },
            {
                "role": "user",
                "content": f'Generate study material on the topic of "{topic}".'
            }
        ],
        "model": "llama3-8b-8192",
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        # Make the request to Groq API
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        result = response.json()
        generated_text = result["choices"][0]["message"]["content"]
        
        # Extract notes and Q&A
        notes_match = re.search(r'Notes:([\s\S]*?)(?=Questions & Answers:|$)', generated_text, re.IGNORECASE)
        qa_match = re.search(r'Questions & Answers:([\s\S]*)', generated_text, re.IGNORECASE)
        
        notes = notes_match.group(1).strip() if notes_match else ""
        qa = qa_match.group(1).strip() if qa_match else ""
        
        # Remove asterisks from beginning and end
        notes = re.sub(r'^\*\*|\*\*$', '', notes)
        qa = re.sub(r'^\*\*|\*\*$', '', qa)
        
        # Clean up the notes formatting - remove leading/trailing whitespace and ensure proper paragraph spacing
        notes = notes.strip()
        # Ensure paragraphs are properly separated with a single blank line
        notes = re.sub(r'\n{3,}', '\n\n', notes)
        # Remove any leading spaces at the beginning of paragraphs
        notes = re.sub(r'(?<=\n)\s+', '', notes)
        
        # Format Q&A with proper spacing between each Q&A pair
        # First, identify question-answer pairs
        qa_pairs = re.findall(r'(\d+\.\s.*?)(?=\d+\.|$)', qa, re.DOTALL)
        
        if qa_pairs:
            # Process each pair to ensure proper formatting
            formatted_qa = []
            for pair in qa_pairs:
                # Clean up the pair and ensure it ends with a blank line
                cleaned_pair = pair.strip()
                if not cleaned_pair.endswith('\n'):
                    cleaned_pair += '\n'
                formatted_qa.append(cleaned_pair + '\n')
            
            # Join all formatted pairs
            qa = ''.join(formatted_qa).strip()
        
        # Check if AI refused to generate content
        if "I cannot provide reliable information" in generated_text or "I don't have enough reliable information" in generated_text or len(notes.strip()) < 50:
            return jsonify({
                "error": "Content not available",
                "message": "I cannot provide reliable study material on this topic. Please choose a well-known educational topic.",
                "notes": "Unable to generate reliable educational content for this topic.",
                "qa": "Please try a different educational topic that I can provide accurate information about."
            }), 403
        
        # Save to database ONLY if content was successfully generated
        if user_id and len(notes.strip()) > 50 and len(qa.strip()) > 50:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if this exact topic already exists for this user (to prevent duplicates)
            cursor.execute(
                "SELECT id FROM queries WHERE user_id = ? AND topic = ? ORDER BY created_at DESC LIMIT 1",
                (user_id, topic)
            )
            existing_query = cursor.fetchone()
            
            if existing_query:
                # Use the existing query ID
                query_id = existing_query[0]
                # Update the existing entry with new content
                cursor.execute(
                    "UPDATE queries SET notes = ?, qa = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (notes, qa, query_id)
                )
            else:
                # Create a new entry
                cursor.execute(
                    "INSERT INTO queries (user_id, topic, notes, qa) VALUES (?, ?, ?, ?)",
                    (user_id, topic, notes, qa)
                )
                query_id = cursor.lastrowid
                
            conn.commit()
            conn.close()
        else:
            query_id = None
        
        # Generate an interesting fact ONLY if content was successfully generated and saved
        fact = ""
        if query_id is not None:  # Only generate fact if content was saved to database
            fact_prompt = f"""
            Generate ONE interesting fact about {topic} that is not directly mentioned in the study notes.
            The fact should be surprising, memorable, or fascinating.
            Keep it to 1-2 sentences maximum and make sure it's appropriate for students.
            Start with "Did you know that" and end with a period.
            
            If you don't have enough reliable information about this topic or person, respond with "NO_FACT_AVAILABLE".
            """
            
            try:
                fact_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {GROQ_API_KEY}'
                }
                
                fact_payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful educational assistant. Only provide facts that you are confident are accurate. If you're unsure about the topic or don't have reliable information, respond with NO_FACT_AVAILABLE."
                        },
                        {
                            "role": "user",
                            "content": fact_prompt
                        }
                    ],
                    "model": "llama3-8b-8192",
                    "temperature": 0.7,
                    "max_tokens": 100
                }
                
                fact_response = requests.post(API_ENDPOINT, headers=fact_headers, json=fact_payload)
                fact_response.raise_for_status()
                
                fact_result = fact_response.json()
                fact = fact_result["choices"][0]["message"]["content"].strip()
                
                # Check if we have a valid fact
                if "NO_FACT_AVAILABLE" in fact.upper() or "I APOLOGIZE" in fact.upper() or "I'M SORRY" in fact.upper() or "I DON'T HAVE" in fact.upper():
                    fact = ""
                else:
                    # Ensure it starts with "Did you know that"
                    if not fact.lower().startswith("did you know that"):
                        fact = "Did you know that " + fact
                    
                    # Ensure it ends with a period
                    if not fact.endswith("."):
                        fact += "."
                    
            except Exception as e:
                print(f"Error generating fact: {e}")
                fact = ""
        
        return jsonify({
            "id": query_id,
            "choices": result["choices"],
            "notes": notes,
            "qa": qa,
            "fact": fact
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_user_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user's previous queries
    cursor.execute("""
        SELECT id, topic, notes, qa, created_at 
        FROM queries 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    
    queries = []
    for row in cursor.fetchall():
        queries.append({
            "id": row[0],
            "topic": row[1],
            "notes": row[2],
            "qa": row[3],
            "created_at": row[4]
        })
    
    conn.close()
    
    return jsonify({"queries": queries})

if __name__ == '__main__':
    # Use environment variable for port if available (for Heroku)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)