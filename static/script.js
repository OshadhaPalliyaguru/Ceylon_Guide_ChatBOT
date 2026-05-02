// --- Chat Widget Toggle Logic ---
function toggleChat() {
    const chatContainer = document.getElementById("chat-container");

    if (chatContainer.classList.contains("hidden")) {
        chatContainer.classList.remove("hidden");
        setTimeout(() => {
            chatContainer.classList.add("show");
        }, 10);
    } else {
        chatContainer.classList.remove("show");
        setTimeout(() => {
            chatContainer.classList.add("hidden");
        }, 300);
    }
}


let isLearningMode = false;

// --- Messaging Logic ---
function sendMessage() {
    let textInput = document.getElementById("textInput");
    let rawText = textInput.value.trim();

    if (rawText === "") return;

    let chatBox = document.getElementById("chat-box");

   
    appendMessage(chatBox, rawText, "user-msg");
    textInput.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

 
    let typingDiv = showTyping(chatBox);

   
    fetch('/get?msg=' + encodeURIComponent(rawText))
        .then(response => response.text())
        .then(data => {
            typingDiv.remove();

            
            if (data.includes("What should I say in response")) {
                isLearningMode = true;
                appendMessage(chatBox, data, "bot-msg learning-msg");
             
                textInput.placeholder = "Type your suggested answer...";
            } else {
                isLearningMode = false;
                textInput.placeholder = "Type a message...";

              
                if (data.includes("submitted for admin review")) {
                    appendMessage(chatBox, data, "bot-msg review-msg");
                } else {
                    appendMessage(chatBox, data, "bot-msg");
                }
            }

            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            typingDiv.remove();
            console.error('Error connecting to AI:', error);
            appendMessage(chatBox, "Sorry, I'm having trouble connecting to the server. 😔", "bot-msg");
        });
}

function appendMessage(chatBox, text, className) {
    let div = document.createElement("div");
    div.className = "msg " + className + " slide-in";
    div.innerText = text;
    chatBox.appendChild(div);
    return div;
}

function showTyping(chatBox) {
    let div = document.createElement("div");
    div.className = "msg bot-msg typing-indicator";
    div.innerHTML = '<span></span><span></span><span></span>';
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function handleEnter(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}