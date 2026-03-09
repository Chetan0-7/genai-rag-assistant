document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    sendBtn.addEventListener("click", sendMessage);

    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Clear input
        userInput.value = "";

        // Add user message to UI
        addMessage(text, "user-message");

        // Add loading indicator
        const loadingId = addLoadingIndicator();

        try {
            // Call Flask backend API
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            // Remove loading indicator
            removeLoadingIndicator(loadingId);

            if (response.ok && data.response) {
                // Add AI message to UI
                addMessage(data.response, "assistant-message");
            } else {
                addMessage(data.error || data.response || "Sorry, an error occurred.", "assistant-message");
            }
        } catch (error) {
            removeLoadingIndicator(loadingId);
            addMessage("Network error. Could not connect to the server.", "assistant-message");
            console.error("Error calling /chat endpoint:", error);
        }
    }

    function addMessage(text, className) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function addLoadingIndicator() {
        const id = "loading-" + Date.now();
        const loadingDiv = document.createElement("div");
        loadingDiv.className = "message assistant-message loading";
        loadingDiv.id = id;
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement("div");
            dot.className = "dot";
            loadingDiv.appendChild(dot);
        }
        
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
        return id;
    }

    function removeLoadingIndicator(id) {
        const loadingElement = document.getElementById(id);
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
});
