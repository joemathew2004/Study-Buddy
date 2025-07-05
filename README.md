# Study Buddy

An AI-powered educational app that generates safe, factual study materials and Q&A for any topic, with user accounts and history tracking.

---

## Images

Below are some screenshots of Study Buddy in action:

![Home Page](images/homepage.png)
![Q&A Example](images/qa-example.png)
![Study History](images/history.png)

---

## Features

- 🔐 User registration & login
- 📚 AI-generated study notes and Q&A
- 📝 Study history tracking
- 💡 Interesting facts for each topic
- 🛡️ Content safety & inappropriate content blocking
- ✅ Famous person validation
- 🎨 Colorful, interactive UI

---

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/study-buddy.git
   cd study-buddy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ API key
   ```

4. **Run the application:**
   ```bash
   # Start the backend server
   python server.py
   
   # Start the frontend server (in another terminal)
   python -m http.server 8000
   ```

5. **Open your browser:**
   [http://localhost:8000/app.html](http://localhost:8000/app.html)

---

## Project Structure

```
├── app.html           # Main frontend HTML
├── app.py             # (Optional) Additional backend logic
├── check_db.py        # Script to inspect the database
├── config.js          # Frontend API config
├── config.py          # (Optional) Backend config
├── index.html         # Landing page
├── qa-styles.css      # Q&A section styles
├── requirements.txt   # Python dependencies
├── script.js          # Main frontend JS
├── server.py          # Flask backend
├── study_buddy.db     # SQLite database (auto-created)
├── style.css          # General styles
└── ...
```

---

## Usage

1. Register or log in with your credentials
2. Enter any educational topic in the search box
3. Get AI-generated notes and Q&A
4. View your study history in the sidebar
5. Enjoy interesting facts about your topics

---

## Safety Features

- Blocks inappropriate content and bad language
- Only allows famous historical figures and educational topics
- Prevents saving failed or inappropriate queries to history
- Shows helpful error messages with topic suggestions

---

## Technologies Used

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript
- **AI:** Groq API (Llama 3)
- **Styling:** Font Awesome, Google Fonts

---

## API Key

You need a GROQ API key to run this application. Get one from [Groq Console](https://console.groq.com/) and add it to your `.env` file.

---

## License

This project is for educational purposes only.
