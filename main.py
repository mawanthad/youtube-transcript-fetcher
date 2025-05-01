from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI  # for openai>=1.0.0
import os
import re

app = Flask(__name__)

# ✅ Create OpenAI client from API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_video_id(url):
    """Extracts the YouTube video ID from a URL."""
    try:
        # Handles typical YouTube formats and skips fragments/query strings
        pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[?&]|$)"
        match = re.search(pattern, url)
        return match.group(1) if match else None
    except Exception:
        return None

def fetch_transcript(video_id):
    """Fetches transcript for a given YouTube video ID."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Transcript not available."
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_text(text, tone="brief"):
    """Generates a summary using OpenAI ChatCompletion API."""
    try:
        prompt = (
            f"Summarize this YouTube transcript in a "
            f"{'professional brief tone' if tone == 'brief' else 'creative script style'}:\n\n{text}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if available in your plan
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/")
def index():
    return "✅ Server is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "No valid JSON received"}), 400

        summaries = {}
        for key, url in data.items():
            print(f"Processing {key}: {url}")
            video_id = extract_video_id(url)
            if not video_id:
                summaries[key] = "Error: Could not extract video ID"
                continue

            transcript = fetch_transcript(video_id)
            summary = summarize_text(transcript, tone="brief")
            summaries[key] = summary

        # Build content blocks
        rich_note = "📘 Rich Content Note:\n\n"
        video_script = "🎬 Video Script:\n\n"

        for key, content in summaries.items():
            rich_note += f"🔹 {key}: {content}\n\n"
            video_script += f"🎞️ {key}: {content}\n\n"

        return jsonify({
            "rich_note": rich_note.strip(),
            "video_script": video_script.strip()
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
