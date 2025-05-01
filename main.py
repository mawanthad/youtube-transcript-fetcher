from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import openai
import os

app = Flask(__name__)

# Load OpenAI API Key (make sure to add this in Render as an environment variable)
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
                video_id = url.split("v=")[1].split("&")[0]
                print(f"Processing video ID: {video_id}")

                # Fetch transcript
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                full_transcript = " ".join([entry["text"] for entry in transcript_list])

                # Summarize via OpenAI
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You summarize YouTube transcripts."},
                        {"role": "user", "content": f"Summarize this transcript:\n\n{full_transcript}"}
                    ],
                    max_tokens=300
                )
                summary = response['choices'][0]['message']['content'].strip()
                summaries[key] = summary

            except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
                summaries[key] = "Transcript not available."
            except Exception as e:
                summaries[key] = f"Error: {str(e)}"

        return jsonify({"status": "success", "summaries": summaries}), 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
