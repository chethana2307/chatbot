"""
chatbot.py - Core Rule-Based Logic for the CODSOFT Chatbot.

This module implements a deterministic rule-based chatbot using:
1. Input normalization (lowercasing, trimming, punctuation stripping).
2. Pattern matching with regular expressions and keyword checks.
3. Persistent memory extraction and retrieval via SQLite.
4. Helpful fallback responses for unknown inputs.
"""

import datetime
import re
import string
from typing import Dict, List, Optional, Tuple
import database


def clean_text(user_input: str) -> str:
    """
    Normalize user input:
    - Strips leading and trailing whitespace.
    - Strips trailing punctuation (.,!?:;).
    - Converts to lowercase for uniform pattern matching.
    """
    trimmed = user_input.strip()
    # Remove trailing punctuation marks common in chat
    cleaned = trimmed.rstrip(".!?:;")
    return cleaned.lower()


def is_greeting(cleaned: str) -> bool:
    """Check if the input matches common greetings."""
    greetings = {
        "hello", "hi", "hey", "greetings", "good morning",
        "good afternoon", "good evening", "howdy", "hiya",
        "what's up", "whats up", "yo"
    }
    if cleaned in greetings:
        return True
    # Matches starting phrases like "hello bot", "hi there"
    return any(cleaned.startswith(f"{g} ") for g in ["hello", "hi", "hey", "greetings"])


def is_goodbye(cleaned: str) -> bool:
    """Check if the input matches goodbye phrases."""
    farewells = {
        "bye", "goodbye", "see you", "see ya", "farewell",
        "talk to you later", "ttyl", "good night", "exit", "quit"
    }
    if cleaned in farewells:
        return True
    return any(cleaned.startswith(f"{f} ") for f in ["bye", "goodbye", "see you"])


def is_bot_identity(cleaned: str) -> bool:
    """Check if user is asking who/what the chatbot is."""
    queries = {
        "what is your name", "whats your name", "what's your name",
        "who are you", "what are you", "tell me about yourself",
        "who created you", "who made you"
    }
    return cleaned in queries


def is_how_are_you(cleaned: str) -> bool:
    """Check if user is asking how the bot is doing."""
    queries = {
        "how are you", "how are you doing", "how's it going",
        "hows it going", "how do you do", "how have you been"
    }
    return cleaned in queries


def is_help_query(cleaned: str) -> bool:
    """Check if user is asking for available commands or capabilities."""
    help_words = {"help", "what can you do", "commands", "menu", "options", "features", "help me"}
    return cleaned in help_words


def handle_datetime_query(cleaned: str) -> Optional[str]:
    """
    Check if the user is asking for the current date or time using Python's datetime.
    Returns formatted date/time string or None.
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    # 1. Combined Date and Time
    date_time_queries = {
        "what is the date and time", "what's the date and time", "whats the date and time",
        "date and time", "tell me the date and time", "time and date", "current date and time"
    }
    if cleaned in date_time_queries:
        return f"Today is {date_str}, and the current time is {time_str}."

    # 2. Date queries
    date_queries = {
        "what is the date", "what's the date", "whats the date",
        "what is today's date", "whats todays date", "today's date", "todays date",
        "tell me the date", "current date", "what date is it", "date",
        "what day is today", "what day is it", "which day is today"
    }
    if cleaned in date_queries:
        return f"Today's date is {date_str}."

    # 3. Time queries
    time_queries = {
        "what is the time", "what's the time", "whats the time",
        "what time is it", "tell me the time", "current time",
        "time please", "time", "clock"
    }
    if cleaned in time_queries:
        return f"The current time is {time_str}."

    return None


def check_and_extract_memory(raw_text: str, session_id: str, db_path: Optional[str] = None) -> Optional[str]:
    """
    Attempt to extract personal details (e.g., name, favorite color, likes)
    from the user's message and save them to SQLite.
    Returns a confirmation response if a detail was extracted, or None.
    """
    # 1. User providing their name
    # e.g., "My name is Mamatha", "Call me Alex", "I am called Sarah"
    name_patterns = [
        r"^(?:my name is|call me|i am called|i'm called)\s+([a-zA-Z\s'-]+)$",
        r"^i am\s+([a-zA-Z'-]+)$",
    ]
    # Common adjectives to avoid falsely treating as a name for "I am ..."
    non_name_words = {
        "fine", "good", "great", "ok", "okay", "well", "happy", "sad",
        "tired", "bored", "hungry", "ready", "back", "here", "doing",
        "awesome", "sorry", "curious", "testing", "new", "a"
    }

    for pattern in name_patterns:
        match = re.match(pattern, raw_text.strip(), re.IGNORECASE)
        if match:
            extracted_name = match.group(1).strip()
            # Verify extracted name is not an adjective or empty
            first_word = extracted_name.split()[0].lower()
            if first_word not in non_name_words and len(extracted_name) >= 2:
                # Format to Title Case
                formatted_name = extracted_name.title()
                database.save_memory(session_id, "name", formatted_name, db_path=db_path)
                return f"Nice to meet you, {formatted_name}! I'll remember your name."

    # 2. User providing their favorite color
    # e.g., "My favorite color is blue", "favorite color: emerald green"
    color_pattern = r"^(?:my\s+)?favorite\s+color\s+(?:is|:)\s+([a-zA-Z\s]+)$"
    color_match = re.match(color_pattern, raw_text.strip(), re.IGNORECASE)
    if color_match:
        color = color_match.group(1).strip().lower()
        database.save_memory(session_id, "favorite_color", color, db_path=db_path)
        return f"Got it! I've noted that your favorite color is {color}."

    # 3. User providing a general favorite (food, movie, hobby, language, etc.)
    # e.g., "My favorite language is Python", "My favorite food is Pizza"
    general_fav_pattern = r"^(?:my\s+)?favorite\s+([a-zA-Z]+)\s+(?:is|:)\s+(.+)$"
    fav_match = re.match(general_fav_pattern, raw_text.strip(), re.IGNORECASE)
    if fav_match:
        topic = fav_match.group(1).strip().lower()
        value = fav_match.group(2).strip()
        # Avoid overriding color if color pattern caught it
        if topic != "color":
            key_name = f"favorite_{topic}"
            database.save_memory(session_id, key_name, value, db_path=db_path)
            return f"Great choice! I will remember that your favorite {topic} is {value}."

    # 4. User stating what they like
    # e.g., "I like Python programming", "I really love coffee"
    likes_pattern = r"^i\s+(?:really\s+)?(?:like|love)\s+(.+)$"
    likes_match = re.match(likes_pattern, raw_text.strip(), re.IGNORECASE)
    if likes_match:
        item = likes_match.group(1).strip()
        # Don't capture generic pronouns like "it", "this", "you"
        if item.lower() not in {"it", "this", "that", "you", "your answers", "chatting"}:
            database.save_memory(session_id, "likes", item, db_path=db_path)
            return f"That's awesome! I'll remember that you like {item}."

    return None


def handle_memory_queries(cleaned: str, session_id: str, db_path: Optional[str] = None) -> Optional[str]:
    """
    Handle questions where the user asks the chatbot what it remembers.
    Returns the answer if matched, or None.
    """
    # 1. Asking for user's name
    if cleaned in {
        "what is my name", "whats my name", "what's my name",
        "do you know my name", "who am i", "tell me my name"
    }:
        name = database.get_memory(session_id, "name", db_path=db_path)
        if name:
            return f"Your name is {name}."
        return "I don't know your name yet. You can tell me by saying 'My name is [Your Name]'."

    # 2. Asking for favorite color
    if cleaned in {
        "what is my favorite color", "whats my favorite color",
        "what's my favorite color", "do you know my favorite color"
    }:
        color = database.get_memory(session_id, "favorite_color", db_path=db_path)
        if color:
            return f"Your favorite color is {color}."
        return "I don't know your favorite color yet. Tell me by saying 'My favorite color is [color]'."

    # 3. Asking for what user likes
    if cleaned in {
        "what do i like", "what do you know i like",
        "what do i love", "do you know what i like"
    }:
        likes = database.get_memory(session_id, "likes", db_path=db_path)
        if likes:
            return f"You told me that you like {likes}."
        return "You haven't told me what you like yet. Try saying 'I like Python' or 'I like [anything]'."

    # 4. Asking for any other specific favorite (e.g., "what is my favorite food?")
    fav_query_match = re.match(r"^what\s+(?:is|'s)\s+my\s+favorite\s+([a-zA-Z]+)$", cleaned)
    if fav_query_match:
        topic = fav_query_match.group(1).lower()
        key_name = f"favorite_{topic}"
        val = database.get_memory(session_id, key_name, db_path=db_path)
        if val:
            return f"Your favorite {topic} is {val}."
        return f"I don't know your favorite {topic} yet. You can teach me by saying 'My favorite {topic} is [value]'."

    # 5. Asking what the chatbot remembers overall
    if cleaned in {
        "what do you remember", "what do you remember about me",
        "what do you know about me", "show my memory", "show memories",
        "show memory", "what do you know", "list memories"
    }:
        memories = database.get_all_memories(session_id, db_path=db_path)
        if not memories:
            return "I don't have any saved memories for you yet. Try telling me your name or favorite things (e.g., 'My name is Alex', 'My favorite color is navy')."

        # Format saved memories clearly
        lines = ["Here is what I currently remember about you:"]
        for m in memories:
            # Format keys like 'favorite_color' -> 'Favorite Color'
            formatted_key = m["key"].replace("_", " ").title()
            lines.append(f"• {formatted_key}: {m['value']}")
        lines.append("\nYou can view or delete individual details anytime from the Memory Management panel.")
        return "\n".join(lines)

    return None


def handle_memory_deletion(cleaned: str, session_id: str, db_path: Optional[str] = None) -> Optional[str]:
    """
    Handle in-chat requests to forget or delete saved memories.
    """
    if cleaned in {"forget my name", "delete my name", "remove my name"}:
        deleted = database.delete_memory(session_id, "name", db_path=db_path)
        if deleted:
            return "I have forgotten your name as requested."
        return "I didn't have your name saved in my memory."

    if cleaned in {"forget my favorite color", "delete my favorite color"}:
        deleted = database.delete_memory(session_id, "favorite_color", db_path=db_path)
        if deleted:
            return "I have forgotten your favorite color as requested."
        return "I didn't have your favorite color saved."

    if cleaned in {
        "forget everything", "delete all memories", "clear my memories",
        "clear memory", "delete my memory", "reset memory"
    }:
        count = database.clear_all_memories(session_id, db_path=db_path)
        return f"I have wiped all saved personal memories ({count} item{'s' if count != 1 else ''} cleared)."

    return None


def generate_response(session_id: str, user_message: str, db_path: Optional[str] = None) -> str:
    """
    Main rule-based routing function:
    1. Sanitizes and normalizes the incoming text.
    2. Checks for in-chat memory deletion commands.
    3. Checks for new memory extraction (storing name, preferences).
    4. Checks for memory retrieval questions.
    5. Checks predefined rule sets (greetings, identity, how-are-you, help, bye, small talk).
    6. Returns a friendly fallback for unrecognized messages.
    """
    # Guard against empty/whitespace input
    if not user_message or not user_message.strip():
        return "Please type a message! I'm here and ready to help."

    raw = user_message.strip()
    cleaned = clean_text(raw)

    # Fetch user's name if previously remembered, to personalize responses
    user_name = database.get_memory(session_id, "name", db_path=db_path)
    name_suffix = f", {user_name}" if user_name else ""

    # Rule 1: Memory Deletion commands via chat
    deletion_response = handle_memory_deletion(cleaned, session_id, db_path=db_path)
    if deletion_response:
        return deletion_response

    # Rule 2: Memory Extraction (storing facts into database)
    memory_store_response = check_and_extract_memory(raw, session_id, db_path=db_path)
    if memory_store_response:
        return memory_store_response

    # Rule 3: Memory Queries (recalling saved facts)
    memory_query_response = handle_memory_queries(cleaned, session_id, db_path=db_path)
    if memory_query_response:
        return memory_query_response

    # Rule 4: Date and Time queries (using Python's datetime)
    datetime_response = handle_datetime_query(cleaned)
    if datetime_response:
        return datetime_response

    # Rule 5: Greetings
    if is_greeting(cleaned):
        if user_name:
            return f"Hello, {user_name}! Great to see you again. How can I help you today?"
        return "Hello there! I am your CODSOFT rule-based assistant. How can I help you today?"

    # Rule 6: Bot Identity
    if is_bot_identity(cleaned):
        return (
            "I am a Rule-Based Chatbot built with Python, Flask, and SQLite for the CODSOFT AI internship. "
            "I operate strictly using deterministic Python rules and pattern matching (no external AI APIs). "
            "I can remember details you share with me and restore our conversation history across browser refreshes!"
        )

    # Rule 7: How the bot is doing
    if is_how_are_you(cleaned):
        return f"I'm running smoothly and ready to assist{name_suffix}! How are you doing today?"

    # Rule 8: User small talk ('I am fine', 'doing well', etc.)
    if cleaned in {"i am fine", "i am good", "i'm good", "doing well", "im fine", "all good"}:
        return f"I'm glad to hear that{name_suffix}! Feel free to tell me your preferences, ask what I remember, or type 'help'."

    # Rule 9: Gratitude
    if cleaned in {"thank you", "thanks", "thank you so much", "thx"}:
        return f"You're very welcome{name_suffix}! Let me know if there is anything else I can do for you."

    # Rule 10: Help & Instructions
    if is_help_query(cleaned):
        return (
            "Here is what I can do for you:\n"
            "• Greetings: Say 'Hello', 'Hi', or 'Hey'\n"
            "• Identity: Ask 'Who are you?' or 'What is your name?'\n"
            "• Status: Ask 'How are you?'\n"
            "• Date & Time: Ask 'What is the date?' or 'What time is it?'\n"
            "• Teach me your name: Say 'My name is [Your Name]'\n"
            "• Recall your name: Ask 'What is my name?'\n"
            "• Teach me preferences: Say 'My favorite color is [color]' or 'I like [hobby]'\n"
            "• Recall preferences: Ask 'What is my favorite color?' or 'What do I like?'\n"
            "• View memory: Ask 'What do you remember about me?'\n"
            "• Forget details: Say 'Forget my name' or 'Clear my memories'\n"
            "• Goodbye: Say 'Bye' or 'Goodbye'"
        )

    # Rule 11: Farewell
    if is_goodbye(cleaned):
        return f"Goodbye{name_suffix}! Have a wonderful day ahead. Your conversation history and preferences are safely saved in SQLite."

    # Rule 12: Helpful Fallback Response
    return (
        "I'm sorry, I don't understand that yet. As a rule-based assistant, I respond to specific phrases and keywords. "
        "Type 'help' to see what I can do, or try telling me your name by saying 'My name is [Your Name]'!"
    )
