import os, json
import time
from flask import Flask, jsonify, send_file
from google.cloud import texttospeech
import sqlite3
from google.oauth2 import service_account
from dotenv import load_dotenv

app = Flask(__name__)

# === Ρύθμιση Google Cloud TTS credentials ===
if os.getenv("GOOGLE_CREDENTIALS"):
    # Production: Περιμένει τη μεταβλητή περιβάλλοντος ως JSON string
    credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
else:
    # Τοπικά: Διαβάζει από αρχείο credentials.json (excluded from git)
    with open("tts_key.json") as f:
        credentials_dict = json.load(f)

credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# === 1. Δημιουργία ή επαναχρήση .mp3 ===
def generate_tts_audio_if_needed(text, filename):
    path = f"static/sounds/questions/{filename}.mp3"
    if not os.path.exists(path):
        print(f"Δημιουργία ήχου για: {filename}")
        client = texttospeech.TextToSpeechClient(credentials=credentials)

        ssml_text = f"""
        <speak>
            {text}
        </speak>
        """

        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open(path, "wb") as out:
            out.write(response.audio_content)

    return path


# === 2. Ανάκτηση ερώτησης από βάση δεδομένων ===
def get_question_text(question_id):
    connection = sqlite3.connect("your_database.db")
    cursor = connection.cursor()
    cursor.execute("SELECT question_text FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else "Unknown question."


# === 3. Flask route που παρέχει ερώτηση και ήχο ===
@app.route("/tts_question/<int:question_id>")
def tts_question(question_id):
    text = get_question_text(question_id)
    filename = f"question_{question_id}"
    path = generate_tts_audio_if_needed(text, filename)

    return jsonify({"question": text, "audio_url": "/" + path})


# === 4. Script καθαρισμού παλιών αρχείων ===
def clean_old_audio(folder="static/sounds/questions", days=30):
    now = time.time()
    cutoff = now - days * 86400

    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath) and fpath.endswith(".mp3"):
            if os.path.getmtime(fpath) < cutoff:
                print(f"Διαγραφή παλιού αρχείου: {fname}")
                os.remove(fpath)
