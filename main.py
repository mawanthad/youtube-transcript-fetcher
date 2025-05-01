import os
import openai
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Set your OpenAI API key via environment variable for security
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return "✅ Server is running."

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    """
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    return query.get("v", [None])[0]

def get_transcript(video_url):
    """
    Fetches the transcript text from a YouTube video.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry["text"] for entry in transcript])
        return full_text
    except Exception as e:
        print(f"Transcript error for {video_url}: {e}")
        return None

def summarize_text(text):
    """
    Summarizes text using OpenAI.
    """
    try:
        prompt = (
            "Summarize the following YouTube transcript into key points:\n\n" + text[:3000]
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        summary = response.choices[0].message["content"]
        return summary
    except Exception as e:
        print(f"OpenAI summarization error: {e}")
        return "Summarization failed."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        summaries = {}

        for key, url in data.items():
            print(f"Processing {key}: {url}")
            transcript = get_transcript(url)
            if transcript:
                summary = summarize_text(transcript)
            else:
                summary = "Transcript not available."
            summaries[key] = summary

        return jsonify({"status": "success", "summaries": summaries}), 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
