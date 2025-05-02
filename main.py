from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    VideoUnavailable,
    NoTranscriptFound,
    TooManyRequests,
)

app = Flask(__name__)

def extract_video_id(url):
    try:
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
    except Exception:
        return None

def fetch_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        return None, f"Invalid YouTube URL: {video_url}"

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript]), None
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound, TooManyRequests) as e:
        return None, f"{video_url} - {str(e)}"
    except Exception as e:
        return None, f"{video_url} - Unexpected error: {str(e)}"

def summarize_transcripts(transcripts):
    # Dummy summarizer: join them and truncate
    combined = " ".join(transcripts)
    return (
        f"🧠 Rich Note:\n\nThis note combines insights from the videos:\n\n"
        + combined[:1000]
        + "..."
    )

def generate_youtube_script(transcripts):
    combined = " ".join(transcripts)
    return (
        f"🎬 Video Script:\n\nWelcome back to the channel! Today we explore:\n\n"
        + combined[:1200]
        + "...\n\nIf you found this interesting, like and subscribe!"
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    video_urls = [data.get(f"video{i}") for i in range(1, 6) if data.get(f"video{i}")]

    transcripts = []
    errors = []

    for url in video_urls:
        transcript, err = fetch_transcript(url)
        if transcript:
            transcripts.append(transcript)
        else:
            errors.append(err)

    if not transcripts:
        return jsonify({
            "rich_note": "❌ No transcripts could be retrieved.",
            "video_script": "❌ Cannot generate script without transcripts.",
            "errors": errors
        }), 400

    rich_note = summarize_transcripts(transcripts)
    video_script = generate_youtube_script(transcripts)

    return jsonify({
        "rich_note": rich_note,
        "video_script": video_script,
        "errors": errors
    })
