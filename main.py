from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Server is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        print("Received video links:")
        for key, url in data.items():
            print(f"{key}: {url}")

        return jsonify({"status": "success", "message": "Video links received."}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
