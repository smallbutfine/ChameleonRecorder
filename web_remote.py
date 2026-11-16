#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote
from datetime import datetime
import os, subprocess, zipfile, io, json

WAV_DIR = "/media/usb0"
CFG_FILE = "/home/recorder/bin/channels.json"

HTML = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChameleonRecorder</title>
  <style>
    body { font-family: sans-serif; background: #121212; color: #fff; text-align: center; padding: 16px; max-width: 540px; margin: auto; }
    .banner { padding: 14px; border-radius: 10px; font-weight: bold; font-size: 16px; margin-bottom: 14px; }
    .banner.idle { background: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32; }
    .banner.recording { background: #b71c1c; color: #ffffff; border: 1px solid #ff5252; animation: pulse 1.5s infinite; }
    .banner.noaudio { background: #4a3000; color: #ffcc80; border: 1px solid #ffa726; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    button, .btn { width: 100%; padding: 16px; margin: 8px 0; font-size: 19px; border: none; border-radius: 12px;
                   cursor: pointer; display: block; color: white; text-decoration: none; box-sizing: border-box; }
    .rec { background: #d32f2f; } .stop { background: #455a64; } .del { background: #e65100; }
    .rescan { background: #37474f; font-size: 15px; padding: 11px; } .zip { background: #2e7d32; font-size: 17px; }
    .card { text-align: left; margin-top: 20px; background: #1e1e1e; padding: 14px; border-radius: 12px; }
    .dev-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #333; }
    .dev-controls { display: flex; gap: 6px; }
    .mini-btn { width: auto; padding: 6px 10px; margin: 0; font-size: 13px; border-radius: 6px; background: #333; }
    .mini-btn.active { background: #2e7d32; }
    .ch-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); gap: 6px; margin-bottom: 16px; }
    .ch-box { background: #262626; border: 2px solid #444; border-radius: 8px; padding: 6px 4px; text-align: center; cursor: pointer; user-select: none; }
    .ch-box.on { border-color: #4caf50; background: #1b2e1e; }
    .ch-box.off { opacity: 0.45; }
    .ch-num { font-size: 13px; font-weight: bold; margin-bottom: 4px; }
    .meter-bg { width: 100%; height: 8px; background: #111; border-radius: 4px; overflow: hidden; }
    .meter-fill { height: 100%; width: 5%; background: #4caf50; transition: width 0.15s linear; }
    .file-item { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid #333; }
    .file-name { flex: 1; word-break: break-all; font-size: 14px; }
    .file-actions { display: flex; gap: 6px; }
    .dl-link { background: #1976d2; color: white; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 14px; }
    .del-file { background: #c62828; color: white; padding: 8px 12px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; width: auto; margin: 0; }
    #status { color: #90caf9; font-weight: bold; min-height: 22px; font-size: 14px; }
  </style>
</head>
<body>
  <h2>ChameleonRecorder</h2>
  <div id="recBanner" class="banner idle">CHECKING AUDIO...</div>
  <button class="rec" onclick="runCmd('rec')">Record</button>
  <button class="stop" onclick="runCmd('stop')">Stop</button>
  <button class="del" onclick="if(confirm('Delete last recording?')) runCmd('del_last')">Delete Last Recording</button>
  <button class="rescan" onclick="runCmd('rescan')">Re-Scan USB Audio Device</button>
  <p id="status">Ready</p>

  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 style="margin:0;">Inputs & Live Levels</h3>
      <label style="font-size:13px;"><input type="checkbox" id="meterToggle" checked> Live Meter</label>
    </div>
    <p id="chSummary" style="font-size:13px; color:#aaa; margin:6px 0 12px 0;">Loading channels...</p>
    <div id="channels"></div>
  </div>

  <div class="card">
    <h3>Recordings (/media/usb0)</h3>
    <a class="btn zip" href="/download-all">Download All (.zip)</a>
    <div id="files">Loading files...</div>
  </div>

  <script>
    let cfg = { devices: {}, ports: {} };

    function checkStatus() {
      fetch('/status').then(r => r.json()).then(d => {
        const b = document.getElementById('recBanner');
        if (d.recording) { b.className = 'banner recording'; b.innerText = '● RECORDING (' + d.device + ')'; }
        else if (d.jack_ready) { b.className = 'banner idle'; b.innerText = 'READY: ' + d.device; }
        else { b.className = 'banner noaudio'; b.innerText = 'NO USB AUDIO INTERFACE DETECTED'; }
      });
    }

    function runCmd(a) {
      document.getElementById('status').innerText = 'Running ' + a + '...';
      fetch('/' + a, { method: 'POST' }).then(r => r.text()).then(t => {
        document.getElementById('status').innerText = t;
        setTimeout(checkStatus, 600); setTimeout(loadFiles, 1200);
        if (a === 'rescan') setTimeout(loadChannels, 2500);
      });
    }

    function saveCfg() {
      fetch('/channels', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(cfg) });
      updateSummary();
    }

    function toggleDev(dev) {
      cfg.devices[dev] = !(cfg.devices[dev] !== false);
      renderChannels(window.lastPorts || {}); saveCfg();
    }

    function setAllPorts(dev, state) {
      (window.lastPorts[dev] || []).forEach(p => cfg.ports[p] = state);
      renderChannels(window.lastPorts || {}); saveCfg();
    }

    function togglePort(p) {
      cfg.ports[p] = !(cfg.ports[p] !== false);
      renderChannels(window.lastPorts || {}); saveCfg();
    }

    function updateSummary() {
      let active = 0, total = 0;
      const devs = window.lastPorts || {};
      for (const [dev, plist] of Object.entries(devs)) {
        const devOn = cfg.devices[dev] !== false;
        plist.forEach(p => { total++; if (devOn && cfg.ports[p] !== false) active++; });
      }
      document.getElementById('chSummary').innerText = active + ' of ' + total + ' channels armed for recording';
    }

    function renderChannels(portsByDev) {
      window.lastPorts = portsByDev;
      const container = document.getElementById('channels');
      let html = '';
      for (const [dev, plist] of Object.entries(portsByDev)) {
        const devOn = cfg.devices[dev] !== false;
        html += `<div class="dev-header">
          <strong>${dev === 'system' ? 'Primary Interface (system)' : dev}</strong>
          <div class="dev-controls">
            <button class="mini-btn" onclick="setAllPorts('${dev}', true)">All</button>
            <button class="mini-btn" onclick="setAllPorts('${dev}', false)">None</button>
            <button class="mini-btn ${devOn ? 'active' : ''}" onclick="toggleDev('${dev}')">${devOn ? 'ON' : 'OFF'}</button>
          </div>
        </div><div class="ch-grid" style="opacity:${devOn ? '1' : '0.4'}">`;
        plist.forEach((p, idx) => {
          const on = cfg.ports[p] !== false;
          const safeId = 'm_' + p.split(':').join('_');
          html += `<div class="ch-box ${on ? 'on' : 'off'}" onclick="togglePort('${p}')">
            <div class="ch-num">CH ${idx + 1}</div>
            <div class="meter-bg"><div id="${safeId}" class="meter-fill"></div></div>
          </div>`;
        });
        html += '</div>';
      }
      container.innerHTML = html || '<p style="color:#888;">No JACK channels available.</p>';
      updateSummary();
    }

    function loadChannels() {
      fetch('/channels').then(r => r.json()).then(data => {
        cfg = data.config || { devices: {}, ports: {} };
        renderChannels(data.ports || {});
      });
    }

    function pollMeters() {
      if (!document.getElementById('meterToggle').checked) return;
      fetch('/levels').then(r => r.json()).then(levels => {
        for (const [port, db] of Object.entries(levels)) {
          const id = 'm_' + port.split(':').join('_');
          const el = document.getElementById(id);
          if (el) {
            const pct = Math.max(4, Math.min(100, ((db + 75) / 75) * 100));
            el.style.width = pct + '%';
            el.style.backgroundColor = db > -3 ? '#f44336' : (db > -12 ? '#ffeb3b' : '#4caf50');
            el.parentElement.title = db + ' dB';
          }
        }
      }).catch(() => {});
    }

    function deleteFile(name) {
      if (!confirm('Delete ' + name + '?')) return;
      fetch('/delete/' + encodeURIComponent(name), { method: 'POST' })
        .then(r => r.text())
        .then(t => { document.getElementById('status').innerText = t; loadFiles(); });
    }

    function loadFiles() {
      fetch('/files').then(r => r.json()).then(files => {
        const c = document.getElementById('files');
        c.innerHTML = files.length ? files.map(f =>
          `<div class="file-item">
             <span class="file-name">${f.name}<br><small style="color:#aaa;">${f.size}</small></span>
             <div class="file-actions">
               <a class="dl-link" href="/download/${encodeURIComponent(f.name)}">Download</a>
               <button class="del-file" onclick="deleteFile('${f.name}')">Delete</button>
             </div>
           </div>`
        ).join('') : '<p style="color:#888;">No WAV files found.</p>';
      });
    }

    checkStatus(); loadChannels(); loadFiles();
    setInterval(checkStatus, 2500);
    setInterval(pollMeters, 400);
  </script>
</body>
</html>"""

def get_usb_device_name():
    devs = []
    try:
        with open("/proc/asound/cards") as f:
            for line in f:
                if "USB-Audio" in line:
                    devs.append(line.split(" - ", 1)[-1].strip())
    except Exception:
        pass
    return " + ".join(devs) if devs else "USB Audio"

def is_running(proc):
return subprocess.run(["pgrep", "-x", proc], stdout=subprocess.DEVNULL).returncode == 0
def load_cfg():
try:
with open(CFG_FILE) as f: return json.load(f)
except Exception:
return {"devices": {}, "ports": {}}
class Handler(BaseHTTPRequestHandler):
def log_message(self, format, *args): pass
def do_GET(self):
if self.path == "/":
self.send_response(200)
self.send_header("Content-Type", "text/html; charset=utf-8")
self.end_headers()
self.wfile.write(HTML.encode())
elif self.path == "/status":
self.send_response(200)
self.send_header("Content-Type", "application/json")
self.end_headers()
self.wfile.write(json.dumps({"recording": is_running("jack_capture"), "jack_ready": is_running("jackd"), "device": get_usb_device_name()}).encode())
elif self.path == "/channels":
ports_by_dev = {}
try:
out = subprocess.check_output(["jack_lsp"], stderr=subprocess.DEVNULL).decode().splitlines()
for p in out:
if ":capture_" in p:
dev = p.split(":")
ports_by_dev.setdefault(dev, []).append(p)
except Exception:
pass
self.send_response(200)
self.send_header("Content-Type", "application/json")
self.end_headers()
self.wfile.write(json.dumps({"ports": ports_by_dev, "config": load_cfg()}).encode())
elif self.path == "/levels":
try:
data = subprocess.check_output(["python3", "/home/recorder/bin/jack_meter.py"], timeout=2)
except Exception:
data = b"{}"
self.send_response(200)
self.send_header("Content-Type", "application/json")
self.end_headers()
self.wfile.write(data)
elif self.path == "/files":
files = [{"name": f, "size": f"{round(os.path.getsize(os.path.join(WAV_DIR, f)) / 1048576, 1)} MB"}
for f in (sorted(os.listdir(WAV_DIR), reverse=True) if os.path.isdir(WAV_DIR) else []) if f.lower().endswith(".wav")]
self.send_response(200)
self.send_header("Content-Type", "application/json")
self.end_headers()
self.wfile.write(json.dumps(files).encode())
elif self.path.startswith("/download/"):
fname = os.path.basename(unquote(self.path[10:]))
fpath = os.path.join(WAV_DIR, fname)
if os.path.isfile(fpath) and fname.lower().endswith(".wav"):
self.send_response(200)
self.send_header("Content-Type", "audio/wav")
self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
self.send_header("Content-Length", str(os.path.getsize(fpath)))
self.end_headers()
with open(fpath, "rb") as f:
while chunk := f.read(65536): self.wfile.write(chunk)
else:
self.send_response(404); self.end_headers()
elif self.path == "/download-all":
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
if os.path.isdir(WAV_DIR):
for f in sorted(os.listdir(WAV_DIR)):
if f.lower().endswith(".wav"): zf.write(os.path.join(WAV_DIR, f), arcname=f)
data = buf.getvalue()
self.send_response(200)
self.send_header("Content-Type", "application/zip")
self.send_header("Content-Disposition", f'attachment; filename="Recordings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"')
self.send_header("Content-Length", str(len(data)))
self.end_headers()
self.wfile.write(data)
else:
self.send_response(404); self.end_headers()
def do_POST(self):
if self.path == "/channels":
length = int(self.headers.get("Content-Length", 0))
body = self.rfile.read(length).decode()
with open(CFG_FILE, "w") as f: f.write(body)
msg = "Channel selection saved"
elif self.path == "/rec":
if not is_running("jack_capture"): subprocess.Popen(["/home/recorder/bin/rec"]); msg = "Recording started"
else: msg = "Already recording"
elif self.path == "/stop":
if is_running("jack_capture"): subprocess.Popen(["pkill", "-SIGTERM", "-x", "jack_capture"]); msg = "Stopping..."
else: msg = "Not recording"
elif self.path == "/del_last":
if not is_running("jack_capture"): subprocess.Popen(["/home/recorder/bin/del_last"]); msg = "Deleted last recording"
else: msg = "Stop recording before deleting!"
elif self.path == "/rescan":
if not is_running("jack_capture"): subprocess.Popen(["/home/recorder/bin/start_jack"]); msg = "Re-scanning USB audio..."
else: msg = "Stop recording first!"
elif self.path.startswith("/delete/"):
if is_running("jack_capture"): msg = "Stop recording before deleting!"
else:
fname = os.path.basename(unquote(self.path[8:]))
fpath = os.path.join(WAV_DIR, fname)
if os.path.isfile(fpath) and fname.lower().endswith(".wav"):
os.remove(fpath); msg = f"Deleted {fname}"
else: msg = "File not found"
else:
self.send_response(404); self.end_headers(); return
self.send_response(200); self.end_headers(); self.wfile.write(msg.encode())
ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
