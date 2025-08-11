// ✅ Detect environment: local dev vs production
const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:5000"
    : "https://varadar.pythonanywhere.com"; // ← change to your Flask backend URL

let recognition;

// ✅ Voice Recognition Setup
if ("webkitSpeechRecognition" in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  const originalStart = recognition.start;
  recognition.start = function () {
    document.getElementById("input-text").value = "";
    document.getElementById("input-language").value = "";
    recognition.lang = "en-US";
    originalStart.call(this);
  };

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("input-text").value = transcript;
    detectLanguage(transcript);
  };

  recognition.onerror = function (event) {
    alert("Voice recognition error: " + event.error);
  };
} else {
  alert("Your browser does not support voice recognition.");
}

// ✅ Load languages from backend
async function loadLanguages() {
  try {
    const response = await fetch(`${API_BASE}/languages`);
    const languages = await response.json();

    const inputLangSelect = document.getElementById("input-language");
    const outputLangSelect = document.getElementById("output-language");

    inputLangSelect.innerHTML = "";
    outputLangSelect.innerHTML = "";

    for (const [code, name] of Object.entries(languages)) {
      const optionInput = document.createElement("option");
      optionInput.value = code;
      optionInput.textContent = name;
      inputLangSelect.appendChild(optionInput);

      const optionOutput = document.createElement("option");
      optionOutput.value = code;
      optionOutput.textContent = name;
      outputLangSelect.appendChild(optionOutput);
    }

    outputLangSelect.value = "en";
  } catch (error) {
    alert("Failed to load languages: " + error.message);
  }
}

// ✅ Add chat bubble to chat UI
function addChatBubble(text, type) {
  const chatBody = document.getElementById("chat-body");

  // Remove placeholder if present
  const placeholder = document.getElementById("chat-placeholder");
  if (placeholder) placeholder.remove();

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${type}`;
  bubble.textContent = text;
  chatBody.appendChild(bubble);
  chatBody.scrollTop = chatBody.scrollHeight;
}

// ✅ Add placeholder when chat is empty
function showChatPlaceholder() {
  const chatBody = document.getElementById("chat-body");
  chatBody.innerHTML = `<div id="chat-placeholder" style="text-align:center; color:gray; margin-top:20px;">
    Start typing or speaking to begin...
  </div>`;
}

// ✅ Translate text
async function translateText() {
  const inputText = document.getElementById("input-text").value;
  const inputLang = document.getElementById("input-language").value;
  const outputLang = document.getElementById("output-language").value;

  if (!inputText || !inputLang || !outputLang) {
    alert("Please fill all fields.");
    return;
  }

  addChatBubble(inputText, "user-msg");
  document.getElementById("loading").textContent = "Translating...";
  document.getElementById("input-text").value = "";

  try {
    const response = await fetch(`${API_BASE}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: inputText, input_lang: inputLang, output_lang: outputLang }),
    });

    const result = await response.json();
    document.getElementById("loading").textContent = "";

    if (result.error) {
      alert(result.error);
    } else {
      addChatBubble(result.translated_text, "bot-msg");

      if (result.audio_url) {
        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = result.audio_url.startsWith("http")
          ? result.audio_url
          : `${API_BASE}${result.audio_url}`;
        document.getElementById("chat-body").appendChild(audio);
        document.getElementById("chat-body").scrollTop = document.getElementById("chat-body").scrollHeight;
      }
    }
  } catch (error) {
    alert("Translation failed: " + error.message);
    document.getElementById("loading").textContent = "";
  }
}

// ✅ Detect language automatically
async function detectLanguage(text) {
  try {
    const response = await fetch(`${API_BASE}/detect_language`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    });

    const data = await response.json();
    const inputLangSelect = document.getElementById("input-language");

    if (data.detected_language) {
      const langCode = data.detected_language;
      if ([...inputLangSelect.options].some(opt => opt.value === langCode)) {
        inputLangSelect.value = langCode;
      }
      console.log("Detected language:", langCode, "Confidence:", data.confidence);
    } else {
      console.error("Language detection failed:", data.error);
    }
  } catch (error) {
    console.error("Language detection error:", error);
  }
}

// ✅ On page load
window.onload = () => {
  showChatPlaceholder();
  loadLanguages();
};
