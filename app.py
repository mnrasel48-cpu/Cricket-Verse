import os
import subprocess
import time
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)
proc = None
OUTPUT_FILE = "recorded_video.mp4"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Stream Recorder</title>
  <style>
    body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; }
    input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: none; }
    button { padding: 12px 18px; margin: 6px 4px 0 0; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
    .start { background: #16a34a; color: #fff; }
    .stop { background: #dc2626; color: #fff; }
    .box { background: #1e1e1e; padding: 15px; border-radius: 8px; margin-top: 15px; word-break: break-all; }
  </style>
</head>
<body>
  <h2>Stream Recorder</h2>
  <form method="POST">
    <input type="text" name="m3u8_url" placeholder="Paste .m3u8 stream link here" value="{{ url or '' }}" required>
    <button class="start" name="action" value="start" type="submit">Start Recording</button>
    <button class="stop" name="action" value="stop" type="submit">Stop & Upload Gofile</button>
  </form>
  {% if message %}
    <div class="box">{{ message|safe }}</div>
  {% endif %}
</body>
</html>
"""

def upload_to_gofile(filepath):
    if not os.path.exists(filepath):
        return "কোনো রেকর্ড করা ফাইল পাওয়া যায়নি।"
    try:
        srv = requests.get("https://api.gofile.io/servers", timeout=15).json()
        server = srv["data"]["servers"][0]["name"]
        url = f"https://{server}.gofile.io/uploadFile"
        with open(filepath, "rb") as f:
            res = requests.post(url, files={"file": f}, timeout=120).json()
        if res.get("status") == "ok":
            link = res["data"]["downloadPage"]
            return f"আপলোড সফল! <br>Gofile লিংক: <a href='{link}' target='_blank' style='color:#4ade80;'>{link}</a>"
        return f"Gofile আপলোড ব্যর্থ: {res}"
    except Exception as e:
        return f"আপলোড করতে সমস্যা হয়েছে: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    global proc
    message = ""
    stream_url = ""

    if request.method == "POST":
        action = request.form.get("action")
        stream_url = request.form.get("m3u8_url", "").strip()

        if action == "start":
            if proc and proc.poll() is None:
                message = "আগে থেকেই একটি রেকর্ডিং চলছে।"
            else:
                if os.path.exists(OUTPUT_FILE):
                    os.remove(OUTPUT_FILE)
                cmd = ["ffmpeg", "-y", "-i", stream_url, "-c", "copy", OUTPUT_FILE]
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                message = "রেকর্ডিং শুরু হয়েছে..."

        elif action == "stop":
            if proc and proc.poll() is None:
                proc.terminate()
                time.sleep(2)
                proc = None
                message = "রেকর্ডিং বন্ধ হয়েছে।<br>" + upload_to_gofile(OUTPUT_FILE)
            else:
                message = "বর্তমানে কোনো রেকর্ডিং চালু নেই।<br>" + upload_to_gofile(OUTPUT_FILE)

    return render_template_string(HTML_PAGE, message=message, url=stream_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
