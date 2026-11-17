#!/usr/bin/env python3
import json
import subprocess
import sys


def run(cmd):
    return json.loads(subprocess.check_output(cmd, stderr=subprocess.DEVNULL))


def parent(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return int(f.read().rsplit(")", 1)[1].split()[1])
    except Exception:
        return 0


def emit(text="", tooltip=""):
    print(json.dumps({
        "text": text,
        "tooltip": tooltip,
        "class": "playing" if text else "idle",
    }), flush=True)


try:
    streams = run(["pactl", "--format=json", "list", "sink-inputs"])
    clients = run(["hyprctl", "clients", "-j"])
except Exception:
    emit()
    sys.exit(0)

by_pid = {c["pid"]: c for c in clients}
playing = {}

for s in streams:
    if s.get("corked"):  # paused streams don't count
        continue
    try:
        pid = int(s.get("properties", {}).get("application.process.id", 0))
    except ValueError:
        continue
    # Browsers play audio from a child process, so walk up to the window's PID
    while pid > 1:
        c = by_pid.get(pid)
        if c:
            playing.setdefault(c["workspace"]["id"], set()).add(c["class"])
            break
        pid = parent(pid)

if not playing:
    emit()
else:
    ids = sorted(playing)
    text = "\uf001 " + " ".join(str(i) for i in ids)
    tip = "\n".join(f"WS {i}: {', '.join(sorted(playing[i]))}" for i in ids)
    emit(text, tip)
