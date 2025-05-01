from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import os
import re

app = Flask(__name__)

def extract_video_id(url):
    """Extracts YouTube video ID from a URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    """Fetches transcript from YouTube if available."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript_list])
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Transcript not available."
    except Exception as e:
        return f"Error: {str(e)}"

def create_summary(transcript):
    """Creates a basic summary (placeholder for now)."""
    return transcript[:500] + "..." if len(transcript) > 500 else transcript

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
            summary = create_summary(transcript)
            summaries[key] = summary

        rich_note = "📘 Rich Content Note:\n\n"
        script = "🎬 Video Script:\n\n"

        for key, summary in summaries.items():
            rich_note += f"🔹 {key}: {summary}\n\n"
            script += f"🎞️ {key}: {summary}\n\n"

        return jsonify({
            "rich_note": rich_note.strip(),
            "video_script": script.strip()
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
