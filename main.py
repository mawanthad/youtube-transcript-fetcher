from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import openai
import os
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Load OpenAI API key from environment
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
                # Ensure URL is a string
                if not isinstance(url, str):
                    raise ValueError("Invalid URL type")

                video_id = extract_video_id(url)
                if not video_id:
                    raise ValueError("Could not extract video ID")

                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                full_text = " ".join([t["text"] for t in transcript])

                prompt = f"Summarize this YouTube video transcript clearly and concisely:\n{full_text}\n\nSummary:"
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )

                summary = response['choices'][0]['message']['content'].strip()
                summaries[key] = summary

            except (VideoUnavailable, TranscriptsDisabled, NoTranscriptFound):
                summaries[key] = "Transcript not available."
            except Exception as e:
                summaries[key] = f"Error: {str(e)}"

        return jsonify({"status": "success", "summaries": summaries}), 200

    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_video_id(url):
    """
    Extract YouTube video ID from a URL.
    Supports both short and long formats.
    """
    parsed_url = urlparse(url)
    if 'youtube' in parsed_url.netloc:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path[1:]
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
