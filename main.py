from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI
import logging
import os
import re
import sys

# Setup logging for Render
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Init Flask app
app = Flask(__name__)

# Load OpenAI key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key in environment variables")

openai = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/")
def index():
    return "✅ Server is running."

def extract_video_id(url):
    """Extract video ID from a YouTube URL."""
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript])
        return full_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        return f"[Transcript unavailable: {str(e)}]"
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"

def summarize_text(text):
    try:
        prompt = f"Summarize the following YouTube video transcript:\n\n{text[:3000]}"  # truncate to stay within token limits
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[OpenAI error: {str(e)}]"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid content-type, must be JSON"}), 400

        data = request.get_json(force=True)
        summaries = {}

        for key, url in data.items():
            logging.info(f"Processing {key}: {url}")
            video_id = extract_video_id(url)
            if not video_id:
                summaries[key] = "[Invalid YouTube URL]"
                continue

            transcript = fetch_transcript(video_id)
            summary = summarize_text(transcript)
            summaries[key] = summary

        return jsonify({"status": "success", "summaries": summaries}), 200

    except Exception as e:
        logging.exception("Webhook processing failed")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
