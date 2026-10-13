#!/usr/bin/env bash
set -u
S=/tmp/claude-1000/-home-kslabolepszy-Dokumenty-GitHub-fish-sim-v0/5d5a578f-cf4a-46f8-b15b-ca9d4f529d38/scratchpad/rec
X() { "$S/xvenv/bin/python" "$S/xact.py" "$@"; }
cd /home/kslabolepszy/Dokumenty/GitHub/fish-sim-v0-wt/stonefish/Stonefish
env SDL_VIDEODRIVER=x11 WAYLAND_DISPLAY=none-xx DISPLAY=:99 LD_LIBRARY_PATH=$HOME/.local/opt/stonefish/lib   build/fish_gui config/s3_turn.json --window 2560x1440 --speed 0.5 > "$S/sf_video.log" 2>&1 &
sleep 3
X move 2559 1439
ffmpeg -nostdin -hide_banner -loglevel error -y -f x11grab -draw_mouse 0 -framerate 30 -video_size 2560x1440 -i :99 -t 50 -c:v libx264 -preset ultrafast -crf 16 "$S/media/stonefish_raw.mp4" &
FF=$!
sleep 30; X click 27 196; X move 2559 1439
sleep 10; X click 27 196; X move 2559 1439
wait $FF
pkill -x fish_gui
ls -la "$S/media/stonefish_raw.mp4"
