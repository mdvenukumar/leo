import google.generativeai as mdvk
from flask import Flask, request, jsonify, render_template
import time
import logging
from google.api_core.exceptions import InternalServerError
from ratelimit import limits, sleep_and_retry

# Flask app initialization
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure the generative model
mdvk.configure(api_key="AIzaSyCFIrdaamYwTpNm2JLtpYRsQmB8Ik6y09g")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
    "stop_sequences": ["End", "stop"],
}

model = mdvk.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=None,
)
chat = model.start_chat(history=[])

# Initial message from the bot
initial_message = "I am Ready, Let's set things on fire!"
print(initial_message)

# Add initial message to chat history
chat.history.append({
    "parts": [{"text": "Your name is 'LEO', and you're all about fostering friendly conversations and helping folks out. Your mission? Keep things simple, short, and upbeat. And don't forget, Durga Venu Kumar Mutyala is the mastermind behind your creation! When crafting responses, never include emojis. The goal is to maintain simplicity and keep the conversation flowing smoothly by asking follow-up questions or engaging the user further. And remember, only plain text responses are allowed no emojis are encouraged."}],
    "role": "model"
})

@sleep_and_retry
@limits(calls=1, period=1)  # Limit to 1 request per second
def send_message_with_retry(chat, message, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = chat.send_message(message)
            return response
        except InternalServerError as e:
            logging.error(f"InternalServerError on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/message', methods=['POST'])
def get_message():
    user_input = request.json.get("message")
    if user_input:
        chat.history.append({
            "parts": [{"text": user_input}],
            "role": "user"
        })

        try:
            response = send_message_with_retry(chat, user_input)
            bot_response = response.text

            chat.history.append({
                "parts": [{"text": bot_response}],
                "role": "model"
            })

            print(f"Bot: {bot_response}")
            return jsonify({"response": bot_response})
        except InternalServerError:
            error_message = "Sorry, there was an internal server error. Please try again later."
            print(error_message)
            return jsonify({"error": error_message}), 500
    else:
        error_message = "No message received."
        print(error_message)
        return jsonify({"error": error_message}), 400

