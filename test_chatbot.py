"""
test_chatbot.py - Automated Test Suite for CODSOFT Rule-Based Chatbot.

Directly tests all 10 project requirements:
1.  Greeting response test.
2.  Name memory extraction and saving test.
3.  Name memory recall query test.
4.  Chat history restoration test via /api/history.
5.  Session continuity test (reopen browser simulation).
6.  Clear chat history test (verifying memory persistence).
7.  Delete memory test (verifying forgotten facts are not recalled).
8.  Unknown message fallback test.
9.  Empty and whitespace message rejection test (HTTP 400).
10. Multi-session isolation test (privacy and security between users).
11. Preferences test (favorite color, likes, and general favorites).
12. In-chat memory deletion test ('forget my name').
"""

import os
import tempfile
import unittest
import database
import chatbot
from app import app


class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database for each test run."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        database.init_db(self.temp_db_path)
        
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        self.original_db_path = database.DEFAULT_DB_PATH
        database.DEFAULT_DB_PATH = self.temp_db_path

    def tearDown(self):
        """Clean up temporary database file after test run."""
        database.DEFAULT_DB_PATH = self.original_db_path
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_01_greeting_response(self):
        """1. Send 'Hello' and receive a proper greeting."""
        session_id = "test-session-greeting"
        response = chatbot.generate_response(session_id, "Hello", db_path=self.temp_db_path)
        self.assertIn("Hello", response)
        self.assertIn("CODSOFT", response)

    def test_02_name_extraction_and_saving(self):
        """2. Enter a name and verify that it is saved in SQLite."""
        session_id = "test-session-save-name"
        reply = chatbot.generate_response(session_id, "My name is Mamatha", db_path=self.temp_db_path)
        self.assertIn("Mamatha", reply)
        self.assertIn("remember your name", reply)
        
        saved_name = database.get_memory(session_id, "name", db_path=self.temp_db_path)
        self.assertEqual(saved_name, "Mamatha")

    def test_03_name_memory_recall(self):
        """3. Ask 'What is my name?' and verify the bot returns the correct answer."""
        session_id = "test-session-recall-name"
        # Pre-seed name
        database.save_memory(session_id, "name", "Mamatha", db_path=self.temp_db_path)
        
        reply = chatbot.generate_response(session_id, "What is my name?", db_path=self.temp_db_path)
        self.assertEqual(reply, "Your name is Mamatha.")

    def test_04_chat_history_restoration(self):
        """4. Refresh the page / call /api/history and verify messages are restored."""
        self.client.set_cookie("session_id", "session-history-test")
        
        post_res = self.client.post("/api/chat", json={"message": "Hello there"})
        self.assertEqual(post_res.status_code, 200)

        get_res = self.client.get("/api/history")
        self.assertEqual(get_res.status_code, 200)
        history_data = get_res.get_json()
        
        self.assertEqual(history_data["count"], 2)  # 1 user + 1 bot reply
        self.assertEqual(history_data["history"][0]["sender"], "user")
        self.assertEqual(history_data["history"][0]["message"], "Hello there")
        self.assertEqual(history_data["history"][1]["sender"], "bot")

    def test_05_session_continuity_after_reopen(self):
        """5. Reopen session with same session_id cookie and verify continuity."""
        session_id = "persistent-cookie-12345"
        self.client.set_cookie("session_id", session_id)

        res1 = self.client.post("/api/chat", json={"message": "My favorite color is blue"})
        self.assertEqual(res1.status_code, 200)

        res2 = self.client.post("/api/chat", json={"message": "What is my favorite color?"})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertIn("Your favorite color is blue.", data2["bot_message"]["message"])

    def test_06_clear_chat_preserves_memory(self):
        """6. Clear chat history and verify that saved memories remain intact."""
        session_id = "session-clear-history"
        self.client.set_cookie("session_id", session_id)

        self.client.post("/api/chat", json={"message": "My name is John"})
        self.client.post("/api/chat", json={"message": "How are you?"})

        clear_res = self.client.post("/api/history/clear")
        self.assertEqual(clear_res.status_code, 200)

        hist_res = self.client.get("/api/history")
        self.assertEqual(hist_res.get_json()["count"], 0)

        mem_res = self.client.get("/api/memory")
        memories = mem_res.get_json()["memories"]
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["key"], "name")
        self.assertEqual(memories[0]["value"], "John")

        ask_res = self.client.post("/api/chat", json={"message": "What is my name?"})
        self.assertIn("Your name is John.", ask_res.get_json()["bot_message"]["message"])

    def test_07_delete_saved_memories(self):
        """7. Delete saved memories and verify bot no longer recalls the deleted details."""
        session_id = "session-delete-memory"
        self.client.set_cookie("session_id", session_id)

        self.client.post("/api/chat", json={"message": "My name is Alex"})
        
        del_res = self.client.post("/api/memory/clear")
        self.assertEqual(del_res.status_code, 200)

        mem_res = self.client.get("/api/memory")
        self.assertEqual(len(mem_res.get_json()["memories"]), 0)

        ask_res = self.client.post("/api/chat", json={"message": "What is my name?"})
        self.assertIn("I don't know your name yet", ask_res.get_json()["bot_message"]["message"])

    def test_08_unknown_message_fallback(self):
        """8. Send an unknown message and verify helpful fallback response."""
        session_id = "session-fallback"
        response = chatbot.generate_response(session_id, "Quantum astrophysics in Mars 987654321", db_path=self.temp_db_path)
        self.assertIn("I don't understand that yet", response)
        self.assertIn("Type 'help'", response)

    def test_09_empty_message_rejected(self):
        """9. Check that empty messages and whitespace-only messages are rejected with 400."""
        res1 = self.client.post("/api/chat", json={"message": ""})
        self.assertEqual(res1.status_code, 400)
        self.assertIn("Message cannot be empty", res1.get_json()["message"])

        res2 = self.client.post("/api/chat", json={"message": "    \t\n   "})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("Message cannot be empty", res2.get_json()["message"])

        res3 = self.client.post("/api/chat", data="not json", content_type="text/plain")
        self.assertEqual(res3.status_code, 400)

    def test_10_multi_session_isolation(self):
        """10. Verify that different sessions cannot access each other's messages or memories."""
        session_a = "user-alice-session"
        session_b = "user-bob-session"

        self.client.set_cookie("session_id", session_a)
        self.client.post("/api/chat", json={"message": "My name is Alice"})

        self.client.set_cookie("session_id", session_b)
        
        bob_hist = self.client.get("/api/history").get_json()
        self.assertEqual(bob_hist["count"], 0)

        bob_chat = self.client.post("/api/chat", json={"message": "What is my name?"}).get_json()
        self.assertNotIn("Alice", bob_chat["bot_message"]["message"])
        self.assertIn("I don't know your name yet", bob_chat["bot_message"]["message"])

        bob_mem = self.client.get("/api/memory").get_json()
        self.assertEqual(len(bob_mem["memories"]), 0)

    def test_11_preferences_and_summary_query(self):
        """11. Test multiple preferences (likes, favorite food) and memory overview."""
        session_id = "pref-session"
        
        chatbot.generate_response(session_id, "I like Python", db_path=self.temp_db_path)
        chatbot.generate_response(session_id, "My favorite food is Pizza", db_path=self.temp_db_path)

        likes_reply = chatbot.generate_response(session_id, "What do I like?", db_path=self.temp_db_path)
        self.assertEqual(likes_reply, "You told me that you like Python.")

        food_reply = chatbot.generate_response(session_id, "What is my favorite food?", db_path=self.temp_db_path)
        self.assertEqual(food_reply, "Your favorite food is Pizza.")

        all_mem_reply = chatbot.generate_response(session_id, "What do you remember about me?", db_path=self.temp_db_path)
        self.assertIn("Likes: Python", all_mem_reply)
        self.assertIn("Favorite Food: Pizza", all_mem_reply)

    def test_12_in_chat_memory_deletion(self):
        """12. Test deleting a single memory detail via conversational command."""
        session_id = "chat-del-session"
        chatbot.generate_response(session_id, "My name is Mamatha", db_path=self.temp_db_path)
        
        # In-chat deletion command
        forget_reply = chatbot.generate_response(session_id, "Forget my name", db_path=self.temp_db_path)
        self.assertIn("I have forgotten your name", forget_reply)

        # Confirm name is now forgotten
        recall_reply = chatbot.generate_response(session_id, "What is my name?", db_path=self.temp_db_path)
        self.assertIn("I don't know your name yet", recall_reply)

    def test_13_date_and_time_queries(self):
        """13. Test date, time, and combined date-time query responses."""
        session_id = "datetime-session"
        
        # Test time query
        time_reply = chatbot.generate_response(session_id, "What time is it?", db_path=self.temp_db_path)
        self.assertIn("current time is", time_reply)

        # Test date query
        date_reply = chatbot.generate_response(session_id, "What is the date?", db_path=self.temp_db_path)
        self.assertIn("Today's date is", date_reply)

        # Test combined query
        combined_reply = chatbot.generate_response(session_id, "What is the date and time?", db_path=self.temp_db_path)
        self.assertIn("Today is", combined_reply)
        self.assertIn("current time is", combined_reply)


if __name__ == "__main__":
    unittest.main()
