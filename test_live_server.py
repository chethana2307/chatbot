"""
test_live_server.py - End-to-end integration test against running Flask HTTP server.
"""

import http.cookiejar
import json
import urllib.request

def run_live_tests():
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    print("[1/11] Testing GET / (HTML + session cookie)...")
    res = opener.open("http://127.0.0.1:5000/")
    assert res.status == 200
    html = res.read().decode("utf-8")
    assert "Rule-Based Chatbot" in html
    print("       [OK] GET / passed.")

    print("[2/10] Testing POST /api/chat with 'Hello'...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/chat",
        data=json.dumps({"message": "Hello"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert data["status"] == "success"
    assert "Hello" in data["bot_message"]["message"]
    print("       [OK] Greeting reply:", data["bot_message"]["message"])

    print("[3/10] Testing memory extraction: 'My name is Mamatha'...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/chat",
        data=json.dumps({"message": "My name is Mamatha"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert "Mamatha" in data["bot_message"]["message"]
    print("       [OK] Memory save reply:", data["bot_message"]["message"])

    print("[4/10] Testing memory query: 'What is my name?'...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/chat",
        data=json.dumps({"message": "What is my name?"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert data["bot_message"]["message"] == "Your name is Mamatha."
    print("       [OK] Memory recall reply:", data["bot_message"]["message"])

    print("[5/10] Testing history restoration: GET /api/history...")
    res = opener.open("http://127.0.0.1:5000/api/history")
    data = json.loads(res.read().decode("utf-8"))
    assert data["count"] >= 4
    print(f"       [OK] History restoration: {data['count']} messages retrieved.")

    print("[6/10] Testing GET /api/memory...")
    res = opener.open("http://127.0.0.1:5000/api/memory")
    data = json.loads(res.read().decode("utf-8"))
    assert len(data["memories"]) >= 1
    assert any(m["key"] == "name" and m["value"] == "Mamatha" for m in data["memories"])
    print("       [OK] Memory list:", data["memories"])

    print("[7/10] Testing POST /api/history/clear (Clear chat)...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/history/clear",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert data["status"] == "success"
    
    # Confirm history is now empty
    res = opener.open("http://127.0.0.1:5000/api/history")
    assert json.loads(res.read().decode("utf-8"))["count"] == 0
    print("       [OK] Chat history cleared successfully.")

    print("[8/10] Verifying memory persists after chat history clear...")
    res = opener.open("http://127.0.0.1:5000/api/memory")
    data = json.loads(res.read().decode("utf-8"))
    assert len(data["memories"]) >= 1
    assert any(m["key"] == "name" and m["value"] == "Mamatha" for m in data["memories"])
    print("       [OK] Memory is preserved after chat clear!")

    print("[9/10] Testing POST /api/memory/clear (Delete all memories)...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/memory/clear",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert data["status"] == "success"
    
    res = opener.open("http://127.0.0.1:5000/api/memory")
    assert len(json.loads(res.read().decode("utf-8"))["memories"]) == 0
    print("       [OK] Memories wiped successfully.")

    print("[10/11] Verifying bot no longer knows name after memory wipe...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/chat",
        data=json.dumps({"message": "What is my name?"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert "I don't know your name yet" in data["bot_message"]["message"]
    print("       [OK] Bot properly reports name is unknown:", data["bot_message"]["message"])

    print("[11/11] Testing Date and Time query ('What is the date and time?')...")
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/chat",
        data=json.dumps({"message": "What is the date and time?"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res = opener.open(req)
    data = json.loads(res.read().decode("utf-8"))
    assert "Today is" in data["bot_message"]["message"]
    print("       [OK] Date & Time response:", data["bot_message"]["message"])

    print("\n>>> ALL 11 LIVE SERVER INTEGRATION CHECKS PASSED WITH 100% SUCCESS! <<<")

if __name__ == "__main__":
    run_live_tests()
