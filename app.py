from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import tempfile
import threading
import uuid
import time

app = Flask(__name__)

# Store job status
jobs = {}

def download_job(job_id, url, mode):
    jobs[job_id] = {"status": "downloading", "progress": 0, "filename": None, "error": None}
    tmpdir = tempfile.mkdtemp()

    def progress_hook(d):
        if d.get("status") == "downloading":
            import re
            raw = re.sub(r'\x1b\[[0-9;]*m', '', d.get("_percent_str", "0%")).replace("%","").strip()
            try:
                jobs[job_id]["progress"] = int(float(raw))
            except:
                pass
        elif d.get("status") == "finished":
            jobs[job_id]["progress"] = 95

    if mode == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}],
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
        }
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        files = os.listdir(tmpdir)
        if files:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["filename"] = os.path.join(tmpdir, files[0])
            jobs[job_id]["display_name"] = files[0]
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "Dosya oluşturulamadı."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


HTML = '''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0b0b12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Vido Down">
<title>Vido Down — 604 Agency</title>
<link rel="manifest" href="/manifest.json">
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

:root {
  --bg: #0b0b12; --surface: #13131e; --card: #1a1a28;
  --border: #2a2a3e; --accent: #7c3aed; --green: #06d6a0;
  --pink: #f72585; --text: #e8e8f5; --muted: #55556a;
}
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
html,body { height:100%; }
body {
  background: var(--bg); color: var(--text);
  font-family: 'Syne', sans-serif; min-height:100vh;
  display:flex; flex-direction:column; align-items:center;
}
body::before {
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background:
    radial-gradient(ellipse 70% 40% at 20% 0%, rgba(124,58,237,.18) 0%, transparent 60%),
    radial-gradient(ellipse 50% 50% at 80% 90%, rgba(6,214,160,.1) 0%, transparent 60%);
}

.wrap { width:100%; max-width:560px; padding:48px 20px 80px; position:relative; z-index:1; }

/* Header */
.logo { display:flex; flex-direction:column; align-items:center; margin-bottom:48px; }
.logo-icon {
  width:72px; height:72px; background:var(--accent);
  border-radius:20px; display:flex; align-items:center; justify-content:center;
  font-size:32px; margin-bottom:16px;
  box-shadow: 0 0 40px rgba(124,58,237,.4);
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { box-shadow:0 0 40px rgba(124,58,237,.4); }
  50% { box-shadow:0 0 60px rgba(124,58,237,.7); }
}
.logo h1 { font-size:2rem; font-weight:800; background:linear-gradient(135deg,#fff 0%,#a78bfa 60%,#06d6a0 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.logo .agency { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:3px;
  color:var(--muted); text-transform:uppercase; margin-top:4px; }

/* Card */
.card {
  background:var(--card); border:1px solid var(--border); border-radius:20px;
  padding:28px; margin-bottom:16px;
  animation: fadeUp .6s ease both;
}
@keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:none} }

.label { font-size:12px; font-weight:700; color:var(--muted); letter-spacing:1px;
  text-transform:uppercase; margin-bottom:10px; }

input[type=text] {
  width:100%; background:var(--bg); border:1.5px solid var(--border);
  border-radius:12px; padding:14px 16px; color:var(--text);
  font-family:'JetBrains Mono',monospace; font-size:13px;
  outline:none; transition:border-color .2s;
}
input[type=text]:focus { border-color:var(--accent); }
input::placeholder { color:var(--muted); }

/* Mode toggle */
.toggle { display:flex; gap:10px; margin-top:16px; }
.toggle-btn {
  flex:1; padding:12px; border:1.5px solid var(--border); border-radius:12px;
  background:transparent; color:var(--muted); font-family:'Syne',sans-serif;
  font-size:13px; font-weight:700; cursor:pointer; transition:all .2s; text-align:center;
}
.toggle-btn.active { background:var(--accent); border-color:var(--accent); color:#fff; }

/* Download button */
.btn-download {
  width:100%; padding:16px; background:var(--accent); border:none;
  border-radius:14px; color:#fff; font-family:'Syne',sans-serif;
  font-size:16px; font-weight:800; cursor:pointer; letter-spacing:.5px;
  transition:all .2s; margin-top:4px;
  box-shadow:0 4px 24px rgba(124,58,237,.35);
}
.btn-download:hover { background:#6d28d9; transform:translateY(-1px); }
.btn-download:active { transform:translateY(0); }
.btn-download:disabled { background:var(--border); color:var(--muted); box-shadow:none; cursor:not-allowed; transform:none; }

/* Progress */
.progress-wrap { margin-top:16px; display:none; }
.progress-bar {
  height:6px; background:var(--border); border-radius:3px; overflow:hidden; margin-bottom:8px;
}
.progress-fill {
  height:100%; width:0%; border-radius:3px; transition:width .3s ease;
  background:linear-gradient(90deg, var(--accent), var(--green));
}
.progress-text { font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--muted); }

/* Result */
.result {
  background:rgba(6,214,160,.08); border:1px solid rgba(6,214,160,.25);
  border-radius:14px; padding:20px; margin-top:16px; display:none; text-align:center;
}
.result .r-title { color:var(--green); font-weight:800; font-size:1rem; margin-bottom:8px; }
.result .r-sub { color:#6a9a8a; font-size:13px; margin-bottom:16px; font-weight:400; }
.btn-dl-file {
  display:inline-block; background:var(--green); color:#0a2a20; padding:12px 28px;
  border-radius:10px; font-weight:800; font-size:14px; text-decoration:none;
  transition:all .2s;
}
.btn-dl-file:hover { background:#05c490; }

/* Error */
.error-box {
  background:rgba(247,37,133,.08); border:1px solid rgba(247,37,133,.25);
  border-radius:14px; padding:16px; margin-top:16px; display:none;
  color:#f72585; font-size:13px; font-weight:400; line-height:1.6;
}

/* Supported sites */
.sites { display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
.site { background:rgba(255,255,255,.04); border:1px solid var(--border);
  border-radius:999px; padding:4px 12px; font-size:12px; color:var(--muted); }

/* Footer */
footer { text-align:center; margin-top:40px; }
footer p { font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--muted); letter-spacing:1px; }
footer a { color:var(--accent); text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
  <div class="logo">
    <div class="logo-icon">🎬</div>
    <h1>Vido Down</h1>
    <span class="agency">604 Agency</span>
  </div>

  <div class="card">
    <div class="label">Video Linki</div>
    <input type="text" id="urlInput" placeholder="https://youtube.com/watch?v=...">
    <div class="toggle">
      <button class="toggle-btn active" id="btnVideo" onclick="setMode('video')">🎬 Video (MP4)</button>
      <button class="toggle-btn" id="btnAudio" onclick="setMode('audio')">🎵 Ses (MP3)</button>
    </div>
  </div>

  <button class="btn-download" id="dlBtn" onclick="startDownload()">⬇ İNDİR</button>

  <div class="progress-wrap" id="progressWrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <div class="progress-text" id="progressText">Hazırlanıyor...</div>
  </div>

  <div class="result" id="resultBox">
    <div class="r-title">✅ Hazır!</div>
    <div class="r-sub" id="resultName"></div>
    <a class="btn-dl-file" id="resultLink" href="#">⬇ Dosyayı İndir</a>
  </div>

  <div class="error-box" id="errorBox"></div>

  <div class="card" style="margin-top:24px;animation-delay:.15s">
    <div class="label">Desteklenen Siteler</div>
    <div class="sites">
      <span class="site">▶ YouTube</span>
      <span class="site">📸 Instagram</span>
      <span class="site">🐦 Twitter/X</span>
      <span class="site">🎵 TikTok</span>
      <span class="site">📘 Facebook</span>
      <span class="site">🎬 Vimeo</span>
      <span class="site">🎮 Twitch</span>
      <span class="site">🟠 Reddit</span>
      <span class="site">+1000 site</span>
    </div>
  </div>

  <footer>
    <p>Made with ❤️ by <a href="#">604 Agency</a></p>
  </footer>
</div>

<script>
let mode = 'video';
let pollInterval = null;

function setMode(m) {
  mode = m;
  document.getElementById('btnVideo').classList.toggle('active', m === 'video');
  document.getElementById('btnAudio').classList.toggle('active', m === 'audio');
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { showError('Lütfen bir link gir!'); return; }

  hideAll();
  document.getElementById('dlBtn').disabled = true;
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('progressText').textContent = 'Başlatılıyor...';

  const resp = await fetch('/start', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url, mode})
  });
  const data = await resp.json();

  if (data.error) { showError(data.error); return; }
  pollStatus(data.job_id);
}

function pollStatus(jobId) {
  pollInterval = setInterval(async () => {
    const resp = await fetch('/status/' + jobId);
    const data = await resp.json();

    document.getElementById('progressFill').style.width = data.progress + '%';
    document.getElementById('progressText').textContent = data.progress + '% — ' + (data.status === 'done' ? 'Tamamlandı!' : 'İndiriliyor...');

    if (data.status === 'done') {
      clearInterval(pollInterval);
      showResult(jobId, data.display_name);
    } else if (data.status === 'error') {
      clearInterval(pollInterval);
      showError(data.error);
    }
  }, 800);
}

function showResult(jobId, name) {
  document.getElementById('dlBtn').disabled = false;
  document.getElementById('resultName').textContent = name;
  document.getElementById('resultLink').href = '/download/' + jobId;
  document.getElementById('resultBox').style.display = 'block';
}

function showError(msg) {
  document.getElementById('dlBtn').disabled = false;
  document.getElementById('progressWrap').style.display = 'none';
  document.getElementById('errorBox').textContent = '❌ ' + msg;
  document.getElementById('errorBox').style.display = 'block';
}

function hideAll() {
  document.getElementById('resultBox').style.display = 'none';
  document.getElementById('errorBox').style.display = 'none';
}
</script>
</body>
</html>'''


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "Vido Down — 604 Agency",
        "short_name": "Vido Down",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0b12",
        "theme_color": "#7c3aed",
        "icons": [{"src": "/static/icon.png", "sizes": "192x192", "type": "image/png"}]
    })


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    url = data.get("url", "").strip()
    mode = data.get("mode", "video")
    if not url:
        return jsonify({"error": "Link boş olamaz."})
    job_id = str(uuid.uuid4())
    t = threading.Thread(target=download_job, args=(job_id, url, mode), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id, {"status": "not_found", "progress": 0})
    return jsonify({
        "status": job.get("status"),
        "progress": job.get("progress", 0),
        "display_name": job.get("display_name", ""),
        "error": job.get("error", ""),
    })


@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return "Dosya bulunamadı.", 404
    return send_file(job["filename"], as_attachment=True, download_name=job["display_name"])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
