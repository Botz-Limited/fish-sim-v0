#!/bin/bash
S=/tmp/claude-1000/-home-kslabolepszy-Dokumenty-GitHub-fish-sim-v0/5d5a578f-cf4a-46f8-b15b-ca9d4f529d38/scratchpad/rec
M=/home/kslabolepszy/Dokumenty/GitHub/fish-sim-v0/MuJoCo
cd "$M"
WAYLAND_DISPLAY=none-xx XDG_SESSION_TYPE=x11 DISPLAY=:99 ../.venv/bin/python "$S/mj_record.py" "$M" "$1" no 0.5 200 > "$S/mj_run.log" 2>&1 &
for i in $(seq 40); do grep -q READY "$S/mj_run.log" && break; sleep 0.5; done
"$S/xvenv/bin/python" "$S/xact.py" resize 2560 1440
sleep 0.3
ffmpeg -nostdin -loglevel error -y -f x11grab -draw_mouse 0 -framerate 30 -video_size 2560x1440 -i :99 -c:v libx264 -preset ultrafast -crf 16 "$2" > "$S/mj_ff.log" 2>&1 &
FF=$!
for i in $(seq 200); do grep -q DONE "$S/mj_run.log" && break; sleep 1; done
kill -INT $FF; wait $FF
ls -la "$2"
