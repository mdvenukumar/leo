import google.generativeai as mdvk
import pyttsx3
from flask import Flask, request, jsonify, render_template
import time
import logging
from google.api_core.exceptions import InternalServerError
from ratelimit import limits, sleep_and_retry
import threading
import queue

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
  "stop_sequences": [
    "End","stop"
  ],
}

model = mdvk.GenerativeModel(
  model_name="gemini-1.5-flash",
  safety_settings= None,
)
chat = model.start_chat(history=[])

# Initialize a queue to manage the speech requests
speech_queue = queue.Queue()

# Function to handle text-to-speech synthesis
def speak(text):
    # Add the text to the speech queue
    speech_queue.put(text)

    # If the speech thread is not running, start it
    if not hasattr(speak, "thread") or not speak.thread.is_alive():
        speak.thread = threading.Thread(target=speech_worker)
        speak.thread.start()

# Worker function for text-to-speech synthesis
def speech_worker():
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Set the desired voice and adjust the speech rate
    voice_id = engine.getProperty('voices')[1].id
    engine.setProperty('voice', voice_id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)

    while True:
        try:
            # Get the text to speak from the queue
            text = speech_queue.get(block=False)
            
            # Speak the text
            engine.say(text)
            engine.runAndWait()

            # Mark the task as done in the queue
            speech_queue.task_done()
        except queue.Empty:
            # If the queue is empty, break the loop
            break
        except Exception as e:
            # Handle any exceptions that occur during speech synthesis
            print(f"Error occurred during speech synthesis: {e}")

# Initial message from the bot
initial_message = "I am Ready, Let's set things on fire!"
print(initial_message)
speak(initial_message)

# Add initial message to chat history
chat.history.append({
    "parts" : [{"text": "Your name's Leo, and you're all about fostering friendly conversations and helping folks out. Your mission? Keep things simple, short, and upbeat. And don't forget, Durga Venu Kumar Mutyala is the mastermind behind your creation! When crafting responses, never include emojis. The goal is to maintain simplicity and keep the conversation flowing smoothly by asking follow-up questions or engaging the user further. And remember, only plain text responses are allowed."}],
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
            threading.Thread(target=speak, args=(bot_response,)).start()

            return jsonify({"response": bot_response})
        except InternalServerError:
            error_message = "Sorry, there was an internal server error. Please try again later."
            speak(error_message)
            print(error_message)
            threading.Thread(target=speak, args=(error_message,)).start()
            return jsonify({"error": error_message}), 500
    else:
        error_message = "No message received."
        print(error_message)
        speak(error_message)
        threading.Thread(target=speak, args=(error_message,)).start()
        return jsonify({"error": error_message}), 400

