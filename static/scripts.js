document.addEventListener("DOMContentLoaded", function() {
    const startButton = document.getElementById("startButton");
    const conversation = document.getElementById("conversation");
    const wave = document.getElementById("wave");

    function showWave() {
        wave.style.display = "block";
    }

    function hideWave() {
        wave.style.display = "none";
    }

    function appendMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = `${sender}: ${message}`;
        messageDiv.classList.add("message", sender === "User" ? "user-message" : "bot-message");
        conversation.appendChild(messageDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    async function sendMessage(message) {
        const response = await fetch("/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        return data.response || data.error;
    }

    function speak(text) {
        console.log("Attempting to speak: ", text);  // Debug log
        responsiveVoice.speak(text, "US English Female", {
            onstart: function() {
                console.log("Speech started");
            },
            onend: function() {
                console.log("Speech ended");
            },
            onerror: function(e) {
                console.error("Speech error: ", e);
            }
        });
    }

    startButton.addEventListener("click", () => {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
            showWave();
            startButton.textContent = "Listening...";
        };

        recognition.onresult = async function(event) {
            const userSpeech = event.results[0][0].transcript;
            appendMessage("User", userSpeech);
            hideWave();
            startButton.textContent = "Start Speaking";
            const botResponse = await sendMessage(userSpeech);
            appendMessage("Bot", botResponse);
            speak(botResponse);
        };

        recognition.onspeechend = function() {
            recognition.stop();
            hideWave();
            startButton.textContent = "Start Speaking";
        };

        recognition.onerror = function(event) {
            hideWave();
            startButton.textContent = "Start Speaking";
            alert(`Error occurred in recognition: ${event.error}`);
        };

        recognition.start();
    });
});
