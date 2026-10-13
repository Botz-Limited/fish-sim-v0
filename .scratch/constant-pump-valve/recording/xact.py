"""Tiny XTEST helper for display :99.  xact.py click X Y | key KEYSYM [n] | move X Y"""
import sys
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

d = display.Display(":99")
cmd = sys.argv[1]
if cmd == "dclick":
    x, y = int(sys.argv[2]), int(sys.argv[3])
    xtest.fake_input(d, X.MotionNotify, x=x, y=y); d.sync(); time.sleep(0.1)
    for _ in range(2):
        xtest.fake_input(d, X.ButtonPress, 1); d.sync(); time.sleep(0.03)
        xtest.fake_input(d, X.ButtonRelease, 1); d.sync(); time.sleep(0.06)
elif cmd in ("click", "move"):
    x, y = int(sys.argv[2]), int(sys.argv[3])
    xtest.fake_input(d, X.MotionNotify, x=x, y=y)
    d.sync()
    if cmd == "click":
        time.sleep(0.05)
        xtest.fake_input(d, X.ButtonPress, 1)
        d.sync()
        time.sleep(0.05)
        xtest.fake_input(d, X.ButtonRelease, 1)
        d.sync()
elif cmd == "key":
    code = d.keysym_to_keycode(XK.string_to_keysym(sys.argv[2]))
    for _ in range(int(sys.argv[3]) if len(sys.argv) > 3 else 1):
        xtest.fake_input(d, X.KeyPress, code)
        d.sync()
        time.sleep(0.05)
        xtest.fake_input(d, X.KeyRelease, code)
        d.sync()
        time.sleep(0.08)

elif cmd == "type":
    for ch in sys.argv[2]:
        ks = XK.string_to_keysym({".": "period", " ": "space", "_": "underscore"}.get(ch, ch))
        code = d.keysym_to_keycode(ks)
        shift = ch.isupper() or ch == "_"
        if shift:
            xtest.fake_input(d, X.KeyPress, d.keysym_to_keycode(XK.string_to_keysym("Shift_L")))
        xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(0.02)
        xtest.fake_input(d, X.KeyRelease, code)
        if shift:
            xtest.fake_input(d, X.KeyRelease, d.keysym_to_keycode(XK.string_to_keysym("Shift_L")))
        d.sync(); time.sleep(0.03)

elif cmd == "resize":
    # resize the largest mapped top-level window to W x H at 0,0
    w, h = int(sys.argv[2]), int(sys.argv[3])
    root = d.screen().root
    best = None
    for c in root.query_tree().children:
        a = c.get_attributes()
        if a.map_state != X.IsViewable:
            continue
        g = c.get_geometry()
        if best is None or g.width * g.height > best[1]:
            best = (c, g.width * g.height)
    best[0].configure(x=0, y=0, width=w, height=h)
    d.sync()

elif cmd == "drag":
    x1, y1, x2, y2 = map(int, sys.argv[2:6])
    xtest.fake_input(d, X.MotionNotify, x=x1, y=y1); d.sync(); time.sleep(0.2)
    xtest.fake_input(d, X.ButtonPress, 1); d.sync(); time.sleep(0.2)
    for i in range(1, 21):
        xtest.fake_input(d, X.MotionNotify, x=x1 + (x2 - x1) * i // 20, y=y1 + (y2 - y1) * i // 20); d.sync(); time.sleep(0.03)
    time.sleep(0.2)
    xtest.fake_input(d, X.ButtonRelease, 1); d.sync()
