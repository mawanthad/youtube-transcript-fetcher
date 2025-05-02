from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI
import os
import re

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Extract video ID from YouTube URL
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# Get transcript from YouTube
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Transcript not available."
    except Exception as e:
        return f"Error: {str(e)}"

# Use OpenAI to summarize
def summarize_text(text, tone="brief"):
    try:
        prompt = f"Summarize the following merged YouTube transcript in a {'professional and informative tone' if tone == 'brief' else 'creative and engaging video script style'}:\n\n{text}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Homepage check
@app.route("/")
def index():
    return "✅ YouTube Transcript Summarizer API is live."

# Main webhook handler
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "No valid JSON received"}), 400

        full_transcript = ""
        failed_videos = []

        for key, url in data.items():
            print(f"Processing {key}: {url}")
            video_id = extract_video_id(url)
            if not video_id:
                failed_videos.append(f"{key}: Invalid URL")
                continue

            transcript = fetch_transcript(video_id)
            if "Error" in transcript or "Transcript not available" in transcript:
                failed_videos.append(f"{key}: {transcript}")
                continue

            full_transcript += transcript + " "

        if not full_transcript.strip():
            return jsonify({
                "rich_note": "❌ No usable transcripts found.",
                "video_script": "❌ Cannot generate script.",
                "failures": failed_videos
            }), 200

        # Generate unified content
        rich_note = summarize_text(full_transcript, tone="brief")
        script = summarize_text(full_transcript, tone="creative")

        return jsonify({
            "rich_note": "📘 Rich Content Note:\n\n" + rich_note.strip(),
            "video_script": "🎬 Video Script:\n\n" + script.strip(),
            "failures": failed_videos
        }), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
