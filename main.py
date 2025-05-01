from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import openai
import os

app = Flask(__name__)

# 🔐 Load OpenAI key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return "✅ Server is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        summaries = {}
        for key, url in data.items():
            try:
                video_id = extract_video_id(url)
                transcript = fetch_transcript(video_id)
                summary = summarize_text(transcript)
                summaries[key] = summary
                print(f"✅ Processed {key}")
            except Exception as e:
                summaries[key] = f"Error: {str(e)}"
                print(f"❌ Failed to process {key}: {str(e)}")

        return jsonify({"status": "success", "summaries": summaries}), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

def extract_video_id(url):
    """Extract the YouTube video ID from the URL."""
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    return query["v"][0]

def fetch_transcript(video_id):
    """Fetch transcript using youtube-transcript-api."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return transcript
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return "Transcript not available."

def summarize_text(text):
    """Summarize transcript using OpenAI."""
    if "Transcript not available." in text:
        return text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize this YouTube transcript in a short paragraph."},
            {"role": "user", "content": text}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
