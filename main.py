from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import openai
import os
import re

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item["text"] for item in transcript_list])
        return full_text
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
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        summaries = {}
        scripts = {}
        
        for key, url in data.items():
            print(f"Processing {key}: {url}")
            video_id = extract_video_id(url)
            if not video_id:
                summaries[key] = "Error: Could not extract video ID"
                scripts[key] = "Error: Could not extract video ID"
                continue

            transcript = fetch_transcript(video_id)
            brief_summary = summarize_text(transcript, style="brief")
            creative_script = summarize_text(transcript, style="creative")

            summaries[key] = brief_summary
            scripts[key] = creative_script

        rich_note = "📘 Rich Content Note:\n" + "\n\n".join(
            [f"{k}: {v}" for k, v in summaries.items()]
        )
        video_script = "🎬 Video Script:\n" + "\n\n".join(
            [f"{k}: {v}" for k, v in scripts.items()]
        )

        return jsonify({
            "status": "success",
            "rich_note": rich_note,
            "video_script": video_script
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
