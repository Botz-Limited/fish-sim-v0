"""Run the real MuJoCo viewer (run_viewer.py classes) with a scripted key sequence,
so the window can be screen-recorded. Usage: python mj_record.py <MuJoCo dir> [duration]"""
import sys
import time

sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[1] + "/scripts")

import mujoco
import mujoco.viewer

from fishsim.config import FishConfig
from fishsim.readouts import FluidForces
from run_viewer import (KEY_LEFT, KEY_PAGE_DOWN, KEY_RIGHT, KEY_SPACE,
                        SpeedMeter, ViewerControls, make_sim, show_overlay)

DURATION = float(sys.argv[2]) if len(sys.argv) > 2 else 44.0
UI = len(sys.argv) > 3 and sys.argv[3] == "ui"
SPEED = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
FONT = int(sys.argv[5]) if len(sys.argv) > 5 else 200
SCRIPT = {8.0: [KEY_RIGHT] * 4, 17.0: [KEY_LEFT] * 8, 26.0: [KEY_RIGHT] * 4,
          28.0: [KEY_PAGE_DOWN] * 2, 39.0: [KEY_SPACE]}

cfg = FishConfig()
sim = make_sim(cfg)
controls = ViewerControls(cfg)
meter = SpeedMeter()
fluid = FluidForces(sim.model)
dt = sim.model.opt.timestep
steps_per_frame = max(1, round(1.0 / 60 / dt))
done = set()
with mujoco.viewer.launch_passive(sim.model, sim.data, show_left_ui=UI, show_right_ui=UI) as viewer:
    viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
    viewer.cam.trackbodyid = sim.hull
    viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 0.9, 110.0, -55.0
    viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_TRANSPARENT] = True
    print("READY", flush=True)
    time.sleep(1.0)
    while viewer.is_running() and sim.time < DURATION:
        t0 = time.perf_counter()
        for t_key, keys in SCRIPT.items():
            if sim.time >= t_key and t_key not in done:
                for k in keys:
                    controls.on_key(k)
                done.add(t_key)
        with viewer.lock():
            controls.apply(sim)
            for _ in range(steps_per_frame):
                sim.step()
            speed = meter.update(sim, steps_per_frame * dt)
            show_overlay(viewer, sim, controls, speed, fluid, FONT)
        viewer.sync()
        time.sleep(max(0.0, steps_per_frame * dt / SPEED - (time.perf_counter() - t0)))
print("DONE", flush=True)
