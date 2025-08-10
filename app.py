from flask import Flask, request, jsonify, send_from_directory
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import uuid
import time
import glob
from flask import Flask
from flask_cors import CORS

# ✅ Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Paths for frontend and static
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

print("Frontend dir:", FRONTEND_DIR)
print("Index exists:", os.path.exists(os.path.join(FRONTEND_DIR, "index.html")))

# ✅ Create Flask app
app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)
# CORS(app, resources={r"/*": {"origins": "*"}})

# Translator
translator = Translator()

def clean_old_audio_files():
    folder = app.static_folder
    now = time.time()
    for pattern in ["output_*.mp3", "input_audio_*.mp3"]:
        for file_path in glob.glob(os.path.join(folder, pattern)):
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > 300:  # 5 minutes
                    try:
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {str(e)}")




@app.route("/")
def index():
    """Serve the index.html file."""
    # return send_from_directory(app.static_folder, "index.html")
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/languages", methods=["GET"])
def get_languages():
    """
    Fetch all available languages from Google Translate.
    Returns a dictionary of language codes and names.
    """
    return jsonify(LANGUAGES)

@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    input_text = data.get("text")
    input_lang = data.get("input_lang")
    target_lang = data.get("output_lang")

    # 🧹 Call cleanup before generating new audio
    clean_old_audio_files()

    if not input_text or not target_lang:
        return jsonify({"error": "Invalid input. Text, input language, and target language are required."}), 400

    if input_lang not in LANGUAGES or target_lang not in LANGUAGES:
        return jsonify({"error": "Unsupported language code."}), 400

    try:
        # Translate text
        translation = translator.translate(input_text, src=input_lang, dest=target_lang)
        translated_text = translation.text

        # Subtitles
        subtitles_translation = translator.translate(input_text, src=input_lang, dest='en')
        subtitles = subtitles_translation.text

        # Generate unique audio filename
        unique_id = str(uuid.uuid4())
        audio_filename = f"output_{unique_id}.mp3"
        audio_path = os.path.join(app.static_folder, audio_filename)

        # Generate audio
        tts = gTTS(text=translated_text, lang=target_lang, slow=False)
        tts.save(audio_path)

        return jsonify({
            "translated_text": translated_text,
            "subtitles": subtitles,
            "audio_url": f"/static/{audio_filename}"
        })

    except Exception as e:
        return jsonify({"error": f"Translation or audio generation failed: {str(e)}"}), 500
    
    
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
    clean_old_audio_files()  # 🧹 Clean up before saving new one

    data = request.json
    text = data.get("text")
    lang = data.get("lang")

    if not text or not lang:
        return jsonify({"error": "Text and language are required."}), 400

    try:
        unique_id = str(uuid.uuid4())
        input_audio_file = f"input_audio_{unique_id}.mp3"
        audio_path = os.path.join(app.static_folder, input_audio_file)

        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(audio_path)

        return jsonify({ "audio_url": f"/static/{input_audio_file}" })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files like the generated audio."""
    return send_from_directory(app.static_folder, filename)

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    # Ensure the static directory exists
    os.makedirs(app.static_folder, exist_ok=True)
    
    # Run the application
    # app.run(debug=True)
