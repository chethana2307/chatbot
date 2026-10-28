/**
 * script.js - Vanilla JavaScript Frontend for CODSOFT Chatbot.
 * 
 * Handles:
 * 1. Restoring chat history on page load / reopen.
 * 2. Sending messages to Flask API (/api/chat).
 * 3. Real-time typing indicators and auto-scrolling.
 * 4. Viewing and managing persistent user memories in SQLite.
 * 5. Safe DOM rendering (preventing XSS).
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const sendBtn = document.getElementById("send-btn");
    const charCounter = document.getElementById("char-counter");
    const typingIndicator = document.getElementById("typing-indicator");
    const welcomeBanner = document.getElementById("welcome-banner");
    
    // Header Buttons
    const btnReloadHistory = document.getElementById("btn-reload-history");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const btnOpenMemory = document.getElementById("btn-open-memory");
    const memoryCounter = document.getElementById("memory-counter");
    
    // Memory Modal Elements
    const memoryModal = document.getElementById("memory-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const memoryList = document.getElementById("memory-list");
    const btnClearAllMemory = document.getElementById("btn-clear-all-memory");
    const displaySessionId = document.getElementById("display-session-id");
    
    // Toast Container
    const toastContainer = document.getElementById("toast-container");
    
    // Quick Prompt Chips
    const chips = document.querySelectorAll(".chip");

    // State
    let isSending = false;

    // =========================================================================
    // Utilities: Formatting & Security
    // =========================================================================

    /** Format date/time strings for message timestamps */
    function formatTime(dateString) {
        if (!dateString) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const date = new Date(dateString.replace(" ", "T") + "Z");
        // Fallback if parsing fails
        if (isNaN(date.getTime())) {
            return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /** Display temporary toast message */
    function showToast(message, type = "info", duration = 3500) {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /** Scroll messages container to the bottom */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // =========================================================================
    // Message Rendering (XSS-Safe DOM Creation)
    // =========================================================================

    /**
     * Create and append a message row into the chat window safely.
     * @param {'user'|'bot'} sender 
     * @param {string} text 
     * @param {string} timestamp 
     */
    function appendMessage(sender, text, timestamp) {
        // Hide welcome banner once we have messages
        if (welcomeBanner) {
            welcomeBanner.style.display = "none";
        }

        const row = document.createElement("div");
        row.className = `message-row ${sender}`;

        // Avatar
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = sender === "user" ? "👤" : "🤖";

        // Body
        const body = document.createElement("div");
        body.className = "message-body";

        // Bubble
        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = text; // Safe textContent to prevent XSS

        // Timestamp
        const timeSpan = document.createElement("span");
        timeSpan.className = "message-timestamp";
        timeSpan.textContent = formatTime(timestamp);

        body.appendChild(bubble);
        body.appendChild(timeSpan);

        row.appendChild(avatar);
        row.appendChild(body);

        chatMessages.appendChild(row);
        scrollToBottom();
    }

    // =========================================================================
    // Backend API Interaction
    // =========================================================================

    /**
     * Load chat history from SQLite and render on screen.
     */
    async function loadChatHistory(showNotification = false) {
        try {
            const response = await fetch("/api/history");
            if (!response.ok) throw new Error("Failed to load chat history.");
            const data = await response.json();

            // Clear current message rows
            chatMessages.querySelectorAll(".message-row").forEach(el => el.remove());

            if (data.history && data.history.length > 0) {
                if (welcomeBanner) welcomeBanner.style.display = "none";
                data.history.forEach(msg => {
                    appendMessage(msg.sender, msg.message, msg.timestamp);
                });
                if (showNotification) {
                    showToast(`Restored ${data.history.length} messages from database.`, "success");
                }
            } else {
                if (welcomeBanner) welcomeBanner.style.display = "block";
                if (showNotification) {
                    showToast("No previous messages found in database.", "info");
                }
            }

            // Update session code display if available
            if (data.session_id) {
                displaySessionId.textContent = data.session_id;
            }

            // Sync memory counter
            fetchSavedMemories(false);
        } catch (error) {
            console.error("Error loading chat history:", error);
            showToast("Could not restore chat history from database.", "error");
        }
    }

    /**
     * Send user message to the Flask chatbot endpoint.
     */
    async function sendMessage(text) {
        const message = text.trim();
        if (!message || isSending) return;

        isSending = true;
        sendBtn.disabled = true;

        // Render user message immediately
        appendMessage("user", message, new Date().toISOString());

        // Clear input field and reset counter
        messageInput.value = "";
        charCounter.textContent = "0/1000";

        // Show typing indicator
        typingIndicator.classList.remove("hidden");
        scrollToBottom();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "Error processing your request.");
            }

            // Update session id if returned
            if (data.session_id) {
                displaySessionId.textContent = data.session_id;
            }

            // Render bot reply
            appendMessage("bot", data.bot_message.message, data.bot_message.timestamp);

            // Refresh memory count in background
            fetchSavedMemories(false);
        } catch (error) {
            console.error("Chat error:", error);
            appendMessage("bot", `⚠️ Error: ${error.message || "Unable to reach server."}`, new Date().toISOString());
            showToast(error.message || "Failed to send message.", "error");
        } finally {
            typingIndicator.classList.add("hidden");
            isSending = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    /**
     * Clear all chat history in SQLite (preserves user memory).
     */
    async function clearChatHistory() {
        if (!confirm("Are you sure you want to clear your chat history?\n\nNote: Your saved personal memories (name & preferences) will remain safe.")) {
            return;
        }

        try {
            const response = await fetch("/api/history/clear", { method: "POST" });
            const data = await response.json();

            if (!response.ok) throw new Error(data.message || "Failed to clear chat history.");

            // Clear messages from UI
            chatMessages.querySelectorAll(".message-row").forEach(el => el.remove());
            if (welcomeBanner) welcomeBanner.style.display = "block";

            showToast(data.message, "success");
        } catch (error) {
            console.error("Clear error:", error);
            showToast("Failed to clear chat history.", "error");
        }
    }

    /**
     * Fetch saved memories for the current session.
     */
    async function fetchSavedMemories(renderInModal = true) {
        try {
            const response = await fetch("/api/memory");
            if (!response.ok) throw new Error("Failed to fetch memories.");
            const data = await response.json();

            const count = data.memories ? data.memories.length : 0;
            memoryCounter.textContent = count;

            if (data.session_id) {
                displaySessionId.textContent = data.session_id;
            }

            if (!renderInModal) return;

            // Render memories into modal list
            memoryList.innerHTML = "";

            if (count === 0) {
                memoryList.innerHTML = `
                    <div class="empty-memory-state">
                        <div class="empty-icon">📭</div>
                        <p>No saved memories found yet.</p>
                        <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                            Try telling the bot: <em>"My name is Mamatha"</em> or <em>"My favorite color is blue"</em>.
                        </p>
                    </div>
                `;
                return;
            }

            data.memories.forEach(mem => {
                const item = document.createElement("div");
                item.className = "memory-item";

                const info = document.createElement("div");
                info.className = "memory-info";

                const keyTag = document.createElement("span");
                keyTag.className = "memory-key-tag";
                keyTag.textContent = mem.key.replace("_", " ");

                const valText = document.createElement("span");
                valText.className = "memory-val-text";
                valText.textContent = mem.value;

                const dateText = document.createElement("span");
                dateText.className = "memory-date";
                dateText.textContent = `Saved: ${formatTime(mem.timestamp)}`;

                info.appendChild(keyTag);
                info.appendChild(valText);
                info.appendChild(dateText);

                const delBtn = document.createElement("button");
                delBtn.className = "btn-del-memory";
                delBtn.textContent = "Delete";
                delBtn.title = `Delete memory: ${mem.key}`;
                delBtn.addEventListener("click", () => deleteSingleMemory(mem.key));

                item.appendChild(info);
                item.appendChild(delBtn);

                memoryList.appendChild(item);
            });
        } catch (error) {
            console.error("Memory fetch error:", error);
            if (renderInModal) {
                memoryList.innerHTML = `<div class="empty-memory-state"><p>Error loading memories.</p></div>`;
            }
        }
    }

    /**
     * Delete a single memory key.
     */
    async function deleteSingleMemory(key) {
        try {
            const response = await fetch("/api/memory/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ key: key }),
            });
            const data = await response.json();

            if (!response.ok) throw new Error(data.message || "Failed to delete memory.");

            showToast(`Deleted '${key}' from memory.`, "success");
            fetchSavedMemories(true);
        } catch (error) {
            console.error("Delete memory error:", error);
            showToast("Failed to delete memory.", "error");
        }
    }

    /**
     * Delete all saved memories for the session.
     */
    async function clearAllMemories() {
        if (!confirm("Are you sure you want to delete ALL saved memories?\n\nThe chatbot will forget your name and all stored preferences.")) {
            return;
        }

        try {
            const response = await fetch("/api/memory/clear", { method: "POST" });
            const data = await response.json();

            if (!response.ok) throw new Error(data.message || "Failed to clear memories.");

            showToast(data.message, "success");
            fetchSavedMemories(true);
        } catch (error) {
            console.error("Clear all memories error:", error);
            showToast("Failed to delete memories.", "error");
        }
    }

    // =========================================================================
    // Event Listeners
    // =========================================================================

    // Chat form submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(messageInput.value);
    });

    // Character counter
    messageInput.addEventListener("input", () => {
        const len = messageInput.value.length;
        charCounter.textContent = `${len}/1000`;
    });

    // Header buttons
    btnReloadHistory.addEventListener("click", () => loadChatHistory(true));
    btnClearChat.addEventListener("click", clearChatHistory);

    // Memory Modal open & close
    btnOpenMemory.addEventListener("click", () => {
        fetchSavedMemories(true);
        memoryModal.classList.remove("hidden");
    });

    btnCloseModal.addEventListener("click", () => {
        memoryModal.classList.add("hidden");
    });

    // Close modal on clicking backdrop
    memoryModal.addEventListener("click", (e) => {
        if (e.target === memoryModal) {
            memoryModal.classList.add("hidden");
        }
    });

    // Close modal on Escape key
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !memoryModal.classList.contains("hidden")) {
            memoryModal.classList.add("hidden");
        }
    });

    // Clear all memory button
    btnClearAllMemory.addEventListener("click", clearAllMemories);

    // Quick prompt chips
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            const prompt = chip.getAttribute("data-prompt");
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // Initial chat history and memory count restoration
    loadChatHistory(false);
});
