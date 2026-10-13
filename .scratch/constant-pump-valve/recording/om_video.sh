#!/usr/bin/env bash
S=$(cd "$(dirname "$0")" && pwd)
X() { "$S/xvenv/bin/python" "$S/xact.py" "$@"; }
X click 1190 90; X click 1191 90   # clear filter button
X click 1006 702; sleep 1.5; X move 700 500
ffmpeg -nostdin -hide_banner -loglevel error -y -f x11grab -framerate 30 -video_size 1280x720 -i :99+0,0 -t 82 -c:v libx264 -preset slow -crf 24 -pix_fmt yuv420p "$S/media/om_raw.mp4" &
FF=$!
sleep 3; X move 968 40; sleep 1; X click 968 40
sleep 68
X click 1050 90; X type surge.U; sleep 2
X move 969 299; sleep 0.7; X click 969 299; sleep 3
X move 1900 1060
wait $FF
ffmpeg -hide_banner -loglevel error -y -ss 79 -i "$S/media/om_raw.mp4" -frames:v 1 "$S/media/om_plot.png"
