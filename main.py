from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import openai
import os
import re

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript_list])
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Transcript not available."
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_text(text, style="brief"):
    try:
        prompt = (
            "Summarize the following YouTube transcript in a "
            f"{'professional tone' if style == 'brief' else 'creative script-like'} format:\n\n{text}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
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
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        summaries = {}
        rich_note = "📘 Rich Content Note:\n"
        video_script = "🎬 Video Script:\n"

        for key, url in data.items():
            video_id = extract_video_id(url)
            print(f"Processing {key}: {url} → Video ID: {video_id}")

            if not video_id:
                summary = "Error: Could not extract video ID"
            else:
                transcript = fetch_transcript(video_id)
                summary = summarize_text(transcript, style="brief")

            summaries[key] = summary
            rich_note += f"- {key}: {summary}\n"
            video_script += f"- {key}: {summary}\n"

        # Send structured and readable output
        return jsonify({
            "status": "success",
            "summaries": summaries,
            "formatted": f"{rich_note}\n\n{video_script}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
