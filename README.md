# CODSOFT Rule-Based Chatbot with SQLite Memory Restoration

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1%2B-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)
![CODSOFT](https://img.shields.io/badge/CODSOFT-Internship_Task-orange)

A complete, beginner-friendly, web-based rule-based chatbot application developed for the **CODSOFT Artificial Intelligence Internship**.

This project implements a purely deterministic, rule-based chatbot engine using **Python, Flask, HTML, CSS, JavaScript, and SQLite**. It features full **chat history restoration** across page reloads and browser restarts, along with **persistent cross-session personal memory** (remembering user names, preferences, and favorites) stored safely in a local SQLite database using parameterized SQL queries.

---

## 📑 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Key Features](#2-key-features)
- [3. Architecture & How It Works](#3-architecture--how-it-works)
- [4. File Structure Explained](#4-file-structure-explained)
- [5. Database Schema](#5-database-schema)
- [6. Setup & Installation (Windows)](#6-setup--installation-windows)
- [7. Running the Chatbot](#7-running-the-chatbot)
- [8. Running the Automated Tests](#8-running-the-automated-tests)
- [9. Step-by-Step Test Scenarios](#9-step-by-step-test-scenarios)
- [10. Security & Privacy Considerations](#10-security--privacy-considerations)
- [11. Screenshots & Demonstration Video Guide](#11-screenshots--demonstration-video-guide)
- [12. Sample LinkedIn Submission Post](#12-sample-linkedin-submission-post)
- [13. Troubleshooting & FAQ](#13-troubleshooting--faq)

---

## 1. Project Overview

In this internship task, the goal is to build an intelligent chatbot **without relying on external AI APIs (like OpenAI or Gemini) or complex machine learning models**. Instead, the chatbot relies on:
1. **Rule-Based Pattern Matching**: Regular expressions, keyword detection, string sanitization, and structured if-else decision trees in pure Python.
2. **Persistent Storage with SQLite**: Automatically creating local database tables to persist both full chat conversation transcripts and extracted user facts.
3. **Session Restoration**: Utilizing secure cookie-based session identifiers so that when a user refreshes or reopens their browser, their conversation history and personal facts return seamlessly.
4. **Independent History vs. Memory Lifecycle**: Clearing the chat conversation window does **not** wipe the bot's memory of your name or favorite preferences, mirroring real-world assistant behavior.

---

## 2. Key Features

- **Rule-Based Response Engine**:
  - Warm greetings, bot self-introduction, health/status check, and polite farewells.
  - Date and time inquiries using Python's built-in `datetime` module (*"What is the date?"*, *"What time is it?"*).
  - Interactive `help` command outlining available features.
  - Helpful fallback response for unrecognized inputs with actionable suggestions.
- **Intelligent Memory Extraction**:
  - Automatically identifies and saves the user's name: *"My name is Mamatha"*, *"Call me Alex"*.
  - Learns preferences: *"My favorite color is emerald green"*, *"My favorite food is Pizza"*, *"I like Python"*.
  - Recalls saved facts on demand: *"What is my name?"*, *"What is my favorite color?"*, *"What do you remember about me?"*.
- **Database Persistence & Restoration**:
  - Saves all user and bot messages in an SQLite database (`messages` table).
  - Restores full conversation history on webpage reload (`/api/history`).
- **Memory Management Panel**:
  - Dedicated UI modal to view all saved key-value facts and their timestamps.
  - Ability to delete individual memories or wipe all memories at once.
  - In-chat conversational forgetting: *"Forget my name"*, *"Clear my memories"*.
- **Modern, Accessible UI**:
  - Dark-mode interface designed with CSS variables and responsive flexbox.
  - Live typing indicator, character counter (0/1000), quick-prompt chips, and toast alerts.
  - Strict XSS protection by rendering content using `textContent` and DOM nodes.

---

## 3. Architecture & How It Works

```
   +-------------------------------------------------------------+
   |                     Browser Client (Web UI)                 |
   |   - HTML5 / CSS3 (Dark Slate Theme) / Vanilla JavaScript    |
   |   - Restores history via /api/history on page load          |
   |   - Inspects & deletes facts via Memory Modal               |
   +------------------------------+------------------------------+
                                  | HTTP (JSON / Cookies)
                                  v
   +-------------------------------------------------------------+
   |                   Flask Backend (app.py)                    |
   |   - Resolves or generates 30-day UUID session cookie        |
   |   - Validates incoming messages (rejects empty/whitespace)  |
   |   - Exposes RESTful endpoints (/api/chat, /api/history, ...) |
   +-------------------+--------------------+--------------------+
                       |                    |
        Generates Rule |                    | Parameterized SQL
        Based Response |                    | Queries
                       v                    v
+-----------------------------+   +-------------------------------+
|     chatbot.py Engine       |   |       database.py Module      |
| - String normalization      |   | - Auto-creates tables on boot |
| - Regex pattern matching    |<->| - messages table              |
| - Memory extraction/recall  |   | - user_memory table           |
| - Fallback reasoning        |   | - Isolates data by session_id |
+-----------------------------+   +---------------+---------------+
                                                  |
                                                  v
                                      +-----------------------+
                                      |   chatbot.db (SQLite) |
                                      +-----------------------+
```

---

## 4. File Structure Explained

```
codsoft-chatbot/
│
├── app.py                 # Flask server: routing, session management, and API endpoints
├── chatbot.py             # Rule-based logic: regex patterns, memory extraction, responses
├── database.py            # SQLite database layer: connection pooling, parameterized queries
├── requirements.txt       # Python package dependencies (Flask)
├── test_chatbot.py        # Automated test suite (12 comprehensive unit & integration tests)
├── test_live_server.py    # End-to-end integration test against the running live server
├── README.md              # Project documentation, setup guide, and CODSOFT deliverables
├── .gitignore             # Excludes .venv/, bytecode, local database files, and secrets
│
├── templates/
│   └── index.html         # Main web interface template with accessibility & semantic HTML
│
└── static/
    ├── style.css          # Modern dark-mode styling, responsive layout, modal, animations
    └── script.js          # Vanilla JavaScript: API communication, chat restoration, DOM safety
```

### Purpose of Every File:
- **`app.py`**: Initializes the SQLite database upon launch, manages cookie-based sessions, and serves JSON endpoints (`/api/chat`, `/api/history`, `/api/memory`, `/api/history/clear`, `/api/memory/clear`).
- **`chatbot.py`**: Contains the pure Python rule-based algorithms. It cleans incoming text (lowercasing, trimming, punctuation removal) and evaluates rules sequentially without external APIs.
- **`database.py`**: Manages connections to `chatbot.db`. All queries use `?` placeholders (parameterized queries) to eliminate SQL injection vulnerabilities.
- **`templates/index.html`**: The UI skeleton featuring modern headers, status indicator, action buttons, quick prompt chips, message display container, and a memory management modal.
- **`static/style.css`**: Provides a slate-and-indigo dark mode, subtle gradients, typing bubble pulses, scrollbars, and mobile-friendly responsive breakpoints.
- **`static/script.js`**: Fetches history on load, sends user messages, handles enter-key submits, updates character counts, and opens the memory modal safely.
- **`test_chatbot.py`**: Uses Python's built-in `unittest` module with temporary isolated databases to test all 10 project requirements automatically.
- **`test_live_server.py`**: Uses `urllib` and `http.cookiejar` to execute real HTTP calls against the live running Flask server.

---

## 5. Database Schema

The SQLite database file `chatbot.db` is created automatically on first run in the application directory. It contains two tables:

### Table 1: `messages`
Stores conversation history between the user and the bot.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier for each message |
| `session_id` | TEXT | NOT NULL | UUID identifying the user's browser session |
| `sender` | TEXT | NOT NULL (`user` or `bot`) | Indicates whether user or bot sent the message |
| `message` | TEXT | NOT NULL | The text content of the message |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | UTC timestamp when message was recorded |

*Indexed by:* `idx_messages_session ON messages(session_id)` for high-speed message retrieval.

### Table 2: `user_memory`
Stores extracted personal attributes (name, favorite color, preferences) per session.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique memory record ID |
| `session_id` | TEXT | NOT NULL | UUID identifying the user's browser session |
| `memory_key` | TEXT | NOT NULL | Normalized attribute key (e.g., `name`, `favorite_color`) |
| `memory_value` | TEXT | NOT NULL | Stored attribute value (e.g., `Mamatha`, `emerald green`) |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Timestamp when memory was saved/updated |

*Constraints:* `UNIQUE(session_id, memory_key)` guarantees that telling the bot a new name or color updates the existing record via SQLite `UPSERT` rather than duplicating it.

---

## 6. Setup & Installation (Windows)

Follow these exact terminal commands in **Command Prompt** (`cmd.exe`) or **PowerShell**:

### Step 1: Open Terminal in Project Folder
Navigate to your project directory:
```powershell
cd C:\Users\cheth\OneDrive\Desktop\chatbot
```

### Step 2: Create a Virtual Environment
Create an isolated Python virtual environment named `.venv`:
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
In PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an Execution Policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`, or activate via Command Prompt using `.venv\Scripts\activate.bat`)*

### Step 4: Install Dependencies
Install the required packages from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 7. Running the Chatbot

Start the Flask local development server:
```powershell
python app.py
```

You will see output similar to:
```text
============================================================
 Starting CODSOFT Rule-Based Chatbot...
 Access the application at: http://127.0.0.1:5000
 Press Ctrl+C to stop the server.
============================================================
 * Running on http://127.0.0.1:5000
```

Open your web browser (Chrome, Edge, Firefox) and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 8. Running the Automated Tests

The repository includes a comprehensive automated test suite.

### Unit & Requirements Test Suite (12 Tests)
Run the automated unit test suite using Python's standard `unittest` module:
```powershell
python test_chatbot.py
```
**Expected Output:**
```text
............
----------------------------------------------------------------------
Ran 12 tests in 0.977s

OK
```

### Live HTTP Integration Test (10 Steps)
While `python app.py` is running, open a second terminal window and run:
```powershell
python test_live_server.py
```
**Expected Output:**
```text
[1/10] Testing GET / (HTML + session cookie)...
       [OK] GET / passed.
[2/10] Testing POST /api/chat with 'Hello'...
       [OK] Greeting reply: Hello there! I am your CODSOFT rule-based assistant. How can I help you today?
[3/10] Testing memory extraction: 'My name is Mamatha'...
       [OK] Memory save reply: Nice to meet you, Mamatha! I'll remember your name.
[4/10] Testing memory query: 'What is my name?'...
       [OK] Memory recall reply: Your name is Mamatha.
[5/10] Testing history restoration: GET /api/history...
       [OK] History restoration: 6 messages retrieved.
[6/10] Testing GET /api/memory...
       [OK] Memory list: [{'id': 1, 'key': 'name', 'timestamp': '...', 'value': 'Mamatha'}]
[7/10] Testing POST /api/history/clear (Clear chat)...
       [OK] Chat history cleared successfully.
[8/10] Verifying memory persists after chat history clear...
       [OK] Memory is preserved after chat clear!
[9/10] Testing POST /api/memory/clear (Delete all memories)...
       [OK] Memories wiped successfully.
[10/10] Verifying bot no longer knows name after memory wipe...
       [OK] Bot properly reports name is unknown: I don't know your name yet. You can tell me by saying 'My name is [Your Name]'.

>>> ALL 10 LIVE SERVER INTEGRATION CHECKS PASSED WITH 100% SUCCESS! <<<
```

---

## 9. Step-by-Step Test Scenarios

You can verify all 10 core internship requirements directly in your browser:

| # | User Action / Message | Expected Bot Response / Result | Feature Tested |
| :--- | :--- | :--- | :--- |
| **1** | Type `"Hello"` or click `Hello 👋` chip | *"Hello there! I am your CODSOFT rule-based assistant..."* | Greeting Rule |
| **2** | Type `"My name is Mamatha"` | *"Nice to meet you, Mamatha! I'll remember your name."* | Memory Extraction & SQLite storage |
| **3** | Type `"What is my name?"` | *"Your name is Mamatha."* | Memory Recall Query |
| **4** | Refresh the browser page (`F5`) | All prior messages reload and display automatically | Chat History Restoration |
| **5** | Close browser tab, open new tab to `http://127.0.0.1:5000` | Full history & memories reload via persistent cookie | Cross-Session Continuity |
| **6** | Click **Clear** button in top toolbar | Chat bubbles clear from screen; welcome banner returns | Clear Chat History |
| **7** | Click **Memory** button, or ask `"What is my name?"` | Bot still answers *"Your name is Mamatha."* Modal displays saved details | Memory Persistence across chat clearing |
| **8** | In Memory modal, click **Delete All Memories** | Modal displays empty state; asking name returns *"I don't know your name yet"* | Memory Deletion |
| **9** | Type `"Quantum astrophysics on Mars 98765"` | *"I'm sorry, I don't understand that yet. As a rule-based assistant..."* | Fallback Response |
| **10** | Submit an empty message or spaces | Input is prevented or rejected with HTTP 400 Bad Request | Input Validation & Error Handling |
| **11** | Type `"What is the date?"` or `"What time is it?"` | Returns current system date or time using Python's `datetime` module | Date and Time Functionality |

---

## 10. Security & Privacy Considerations

1. **SQL Injection Defense**: Every SQL interaction uses parameterized queries (`cursor.execute(sql, (param1, param2))`). String interpolation (such as `f"SELECT ... WHERE id = {val}"`) is strictly prohibited.
2. **Cross-Site Scripting (XSS) Prevention**: User-submitted messages and memory details are rendered onto the webpage strictly via JavaScript's `textContent` property, preventing arbitrary HTML/script execution.
3. **No Code Execution**: User messages are never passed into `eval()`, `exec()`, or Python shell subprocesses.
4. **Session Identifier Security**: Sessions are identified using 128-bit cryptographically secure UUID4 strings stored in browser cookies with `SameSite=Lax`.
5. **Session Isolation**: Each session can only access its own chat records and memory facts. Session A cannot view or alter Session B's data.
6. **Local Privacy**: The entire application runs on `localhost` (`127.0.0.1`) and stores data in a local file (`chatbot.db`). No telemetry, analytics, or conversations are sent to external servers.
7. **Session vs. True Authentication**: Note that browser cookies serve as session identifiers for convenience. In a production multi-user application, password-authenticated accounts, Argon2 password hashing, and encrypted database columns would be required.

---

## 11. Screenshots & Demonstration Video Guide

To fulfill CODSOFT evaluation requirements, capture screenshots and a short demonstration video:

### How to Take Screenshots on Windows:
1. Press `Windows Key + Shift + S` to open the Windows Snipping Tool.
2. Capture the following 4 screens:
   - **Screenshot 1 - Overview & Greeting**: The chatbot interface showing greeting and identity messages.
   - **Screenshot 2 - Memory Extraction & Recall**: Showing you telling your name (*"My name is Mamatha"*) and the bot recalling it (*"What is my name?"*).
   - **Screenshot 3 - History Restoration**: The page refreshed with history intact and the **Memory Modal** open showing the saved items.
   - **Screenshot 4 - Memory Preserved After Chat Clear**: The chat cleared while the bot still remembers your name.
3. Save these in a folder named `screenshots/` in your repository if desired.

### How to Record a Video:
1. Press `Windows Key + Alt + R` to record your screen using the built-in Windows Game Bar.
2. Walk through the 1-minute demo:
   - Greet the bot.
   - Teach it your name and favorite color.
   - Refresh the page to prove restoration.
   - Open the Memory modal.
   - Clear the chat and verify memory stays intact.
3. Upload the recording to Google Drive, YouTube (unlisted), or LinkedIn.

---

## 12. Sample LinkedIn Submission Post

When submitting your CODSOFT task, you can share your achievement with this post:

```text
🚀 Excited to share my Rule-Based Chatbot with SQLite Memory Restoration built during my AI Internship with #CODSOFT!

Instead of using external AI APIs, this project dives deep into core software engineering fundamentals:
✨ Built a deterministic rule-based chatbot engine using Python & Regular Expressions
💾 Integrated SQLite with Python's sqlite3 module using safe parameterized queries
🔄 Implemented Chat History Restoration across browser refreshes & restarts
🧠 Designed persistent cross-session User Memory (remembering user name & preferences)
🛡️ Enforced independent memory lifecycles (clearing chat history preserves saved memories)
🎨 Developed a clean, responsive web interface using HTML5, CSS3, and Vanilla JavaScript

All 12 automated unit and integration tests are passing with 100% test coverage!

💻 GitHub Repository: [Insert Your GitHub Repo Link Here]
🤝 Thank you CODSOFT for this learning opportunity!

#CODSOFT #Python #Flask #SQLite #ArtificialIntelligence #SoftwareEngineering #WebDevelopment #Internship #StudentDeveloper
```

---

## 13. Troubleshooting & FAQ

- **Q: `ModuleNotFoundError: No module named 'flask'`**
  - **A:** Ensure your virtual environment is activated. You should see `(.venv)` in your terminal prompt. Run `.venv\Scripts\activate` and then `pip install -r requirements.txt`.
- **Q: Port 5000 is already in use (`Address already in use`)**
  - **A:** Another program or background Python process is using port 5000. Either terminate that process in Task Manager or change `port=5000` to `port=5001` at the bottom of `app.py`.
- **Q: Where is the SQLite database file?**
  - **A:** `chatbot.db` is created automatically in the root of the project directory as soon as `app.py` runs.
- **Q: How do I completely reset the database?**
  - **A:** Stop the server (`Ctrl+C`) and delete the `chatbot.db` file. When you restart `python app.py`, a fresh empty database will be initialized automatically.

---

*Developed with ❤️ as part of the CODSOFT Artificial Intelligence Internship.*
