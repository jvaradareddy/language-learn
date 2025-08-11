import os
import uuid
import time
import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from googletrans import Translator, LANGUAGES
from gtts import gTTS

# ✅ Backend base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Backend static directory (writable)
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# ✅ Frontend directory (read-only for serving HTML)
# FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

FRONTEND_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=FRONTEND_DIR)

print("Backend static dir:", STATIC_DIR)
print("Frontend dir:", FRONTEND_DIR)

# ✅ Create Flask app
# app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

translator = Translator()

def clean_old_audio_files():
    now = time.time()
    for pattern in ["output_*.mp3", "input_audio_*.mp3"]:
        for file_path in glob.glob(os.path.join(STATIC_DIR, pattern)):
            if os.path.isfile(file_path):
                if now - os.path.getmtime(file_path) > 300:  # 5 min
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/languages", methods=["GET"])
def get_languages():
    print("LANGUAGES:", LANGUAGES)
    return jsonify(LANGUAGES)

@app.route("/translate", methods=["POST"])
def translate_text():
    data = request.json
    input_text = data.get("text")
    input_lang = data.get("input_lang")
    target_lang = data.get("output_lang")

    clean_old_audio_files()

    if not input_text or not target_lang:
        return jsonify({"error": "Missing text or target language"}), 400

    try:
        translation = translator.translate(input_text, src=input_lang, dest=target_lang)
        translated_text = translation.text

        subtitles = translator.translate(input_text, src=input_lang, dest='en').text

        unique_id = str(uuid.uuid4())
        audio_filename = f"output_{unique_id}.mp3"
        audio_path = os.path.join(STATIC_DIR, audio_filename)

        tts = gTTS(text=translated_text, lang=target_lang, slow=False)
        tts.save(audio_path)

        return jsonify({
            "translated_text": translated_text,
            "subtitles": subtitles,
            "audio_url": f"/static/{audio_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/detect_language", methods=["POST"])
def detect_language():
    """
    Detect the language of the input text using Google Translate.
    """
    data = request.json
    input_text = data.get("text")

    if not input_text:
        return jsonify({"error": "Text is required for language detection."}), 400

    try:
        detection = translator.detect(input_text)
        detected_lang = detection.lang
        confidence = detection.confidence

        return jsonify({
            "detected_language": detected_lang,
            "confidence": confidence
        })
    except Exception as e:
        return jsonify({"error": f"Language detection failed: {str(e)}"}), 500


@app.route("/speak_input", methods=["POST"])
def speak_input():
    clean_old_audio_files()
    data = request.json
    text = data.get("text")
    lang = data.get("lang")

    if not text or not lang:
        return jsonify({"error": "Missing text or language"}), 400

    try:
        unique_id = str(uuid.uuid4())
        audio_filename = f"input_audio_{unique_id}.mp3"
        audio_path = os.path.join(STATIC_DIR, audio_filename)

        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(audio_path)

        return jsonify({"audio_url": f"/static/{audio_filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    os.makedirs(STATIC_DIR, exist_ok=True)


    app.run(debug=True)
