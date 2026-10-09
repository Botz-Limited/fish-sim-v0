"""Etap 7: interaktywny podgląd ryby w viewerze MuJoCo.

  .venv/bin/python scripts/run_viewer.py             # okno viewera
  .venv/bin/python scripts/run_viewer.py --selftest  # bez okna: skrypt klawiszy, wydruk stanu
  .venv/bin/python scripts/run_viewer.py --speed 0.5 --font 200   # zwolnione 2×, większy tekst (ekran 2K)

Nakładka: lewy górny róg – stan (czas, prędkość, głębokość, ciśnienia), napęd (moment
hydrauliki, pompa, kąty ogona) i siły wody (na całą rybę, ogon+płetwę, kadłub; mN, w układzie
ryby: fwd = naprzód, side = w bok). Strzałki w scenie: magenta = siła wody na każde ciało,
cyan = wypór − ciężar przy środku masy (fishsim/readouts.py).

Klawisze:
  ← / →        skręt (V_bias −/+ 0.5 ml; → = skręt w prawo)
  ↑ / ↓        częstotliwość machania ±0.25 Hz
  PgUp / PgDn  głębokość zadana ±0.25 m (PgUp = płycej, max −0.3 m)
  Spacja       zatrzymanie/wznowienie ogona (pompa stoi, ryba dryfuje)
  Backspace    reset (wbudowany w viewer; resetujemy też hydraulikę i regulatory)

Uwagi:
- PageUp ma wbudowaną funkcję viewera (wybór rodzica zaznaczonego ciała), ale tylko
  gdy jakieś ciało jest zaznaczone (podwójny klik). Nie zaznaczaj ciał – albo Esc.
- macOS: passive viewer wymaga uruchomienia przez `mjpython scripts/run_viewer.py`.
"""

import argparse
import time

import mujoco
import mujoco.viewer
import numpy as np

from fishsim.config import FishConfig
from fishsim.controllers import DepthController, TailRhythm
from fishsim.readouts import FluidForces, draw_arrows, drive_rows, force_arrows, force_rows
from fishsim.sim import FishSim

# Kody klawiszy przekazywane do key_callback (te same liczby co w GLFW)
KEY_SPACE, KEY_RIGHT, KEY_LEFT, KEY_DOWN, KEY_UP, KEY_PAGE_UP, KEY_PAGE_DOWN = 32, 262, 263, 264, 265, 266, 267


class ViewerControls:
    """Stan sterowania z klawiatury. Bez zależności od okna – da się testować.

    key_callback działa w WĄTKU VIEWERA, więc on_key tylko zmienia liczby w Pythonie.
    Do symulacji trafiają one w apply(), wołanym w pętli głównej pod viewer.lock().
    """

    BIAS_STEP, BIAS_MAX = 0.5e-6, 4e-6     # [m³]
    FREQ_STEP, FREQ_MIN, FREQ_MAX = 0.25, 0.25, 3.5   # [Hz]
    DEPTH_STEP = 0.25                      # [m]

    def __init__(self, cfg: FishConfig):
        self.cfg = cfg
        self.bias = cfg.tail_volume_bias
        self.freq = cfg.tail_freq
        self.z_ref = cfg.start_depth
        self.paused = False
        self.changed = True

    def on_key(self, key: int):
        c = self.cfg
        if key == KEY_RIGHT:
            self.bias = min(self.bias + self.BIAS_STEP, self.BIAS_MAX)
        elif key == KEY_LEFT:
            self.bias = max(self.bias - self.BIAS_STEP, -self.BIAS_MAX)
        elif key == KEY_UP:
            self.freq = min(self.freq + self.FREQ_STEP, self.FREQ_MAX)
        elif key == KEY_DOWN:
            self.freq = max(self.freq - self.FREQ_STEP, self.FREQ_MIN)
        elif key == KEY_PAGE_UP:
            self.z_ref = min(self.z_ref + self.DEPTH_STEP, c.z_ref_max)
        elif key == KEY_PAGE_DOWN:
            self.z_ref = max(self.z_ref - self.DEPTH_STEP, c.floor_z + 0.3)
        elif key == KEY_SPACE:
            self.paused = not self.paused
        else:
            return
        self.bias = round(self.bias / self.BIAS_STEP) * self.BIAS_STEP  # bez błędów zaokrągleń
        self.changed = True

    def apply(self, sim: FishSim):
        if not self.changed:
            return
        sim.rhythm.bias = self.bias
        sim.rhythm.set_freq(self.freq, sim.time)   # bez skoku fazy
        sim.rhythm.amp = 0.0 if self.paused else self.cfg.tail_volume_amp
        sim.depth.set_reference(self.z_ref)
        self.changed = False


class SpeedMeter:
    """Prędkość postępowa COM wygładzona filtrem I rzędu (stała czasowa ~1 cykl ogona)."""

    def __init__(self, tau=0.5):
        self.tau = tau
        self.value = 0.0

    def update(self, sim: FishSim, dt: float) -> float:
        mujoco.mj_subtreeVel(sim.model, sim.data)   # subtree_linvel liczone tylko na żądanie
        v = sim.data.subtree_linvel[sim.hull, :2] @ sim.heading()
        self.value += dt / self.tau * (v - self.value)
        return self.value


# Teksty nakładki są PO ANGIELSKU i tylko ASCII: wbudowana czcionka bitmapowa MuJoCo
# ma znaki 32–126, więc polskie litery i strzałki (←, ↑) renderują się źle.
HELP_TEXT = ("Left/Right\nUp/Down\nPgUp/PgDn\nSpace\nBackspace\n\narrows\n",
             "turn\ntail frequency\ndepth\nstop/start tail\nreset\n\n"
             "magenta = water force per body (1 N = 15 cm)\ncyan = buoyancy - weight (10 mN = 2 cm)")
FONTS = {100: mujoco.mjtFontScale.mjFONTSCALE_100, 150: mujoco.mjtFontScale.mjFONTSCALE_150,
         200: mujoco.mjtFontScale.mjFONTSCALE_200, 250: mujoco.mjtFontScale.mjFONTSCALE_250,
         300: mujoco.mjtFontScale.mjFONTSCALE_300}


def status_lines(sim: FishSim, controls: ViewerControls, speed: float):
    L = sim.tail_length()
    p_L, p_R = sim.hydraulics.pressures(L)
    rows = [
        ("time", f"{sim.time:6.1f} s"),
        ("speed", f"{speed * 100:6.1f} cm/s"),
        ("depth / target", f"{sim.com()[2]:+.2f} / {sim.depth.z_ref:+.2f} m"),
        ("tail frequency", f"{controls.freq:.2f} Hz" + ("  (STOP)" if controls.paused else "")),
        ("V_bias (turn)", f"{controls.bias * 1e6:+.1f} ml"),
        ("p_L / p_R", f"{p_L / 1e3:+5.1f} / {p_R / 1e3:+5.1f} kPa"),
        ("bladder volume", f"{sim.bladder.volume * 1e6:5.1f} ml"),
    ]
    return rows


def show_overlay(viewer, sim: FishSim, controls: ViewerControls, speed: float, fluid: FluidForces,
                 font: int = 150):
    """Tekst stanu, napędu i sił + strzałki sił. Woła się pod viewer.lock() (liczy siły na data)."""
    forces = fluid.compute(sim.data)
    draw_arrows(viewer.user_scn, force_arrows(sim, forces))
    rows = status_lines(sim, controls, speed) + [("", "")] + drive_rows(sim) + [("", "")] + force_rows(sim, forces, fluid.total)
    small = FONTS[max(100, font - 50)]
    viewer.set_texts([
        (FONTS[font], mujoco.mjtGridPos.mjGRID_TOPLEFT,
         "\n".join(r[0] for r in rows), "\n".join(r[1] for r in rows)),
        (small, mujoco.mjtGridPos.mjGRID_BOTTOMLEFT, *HELP_TEXT),
    ])
    return rows


def make_sim(cfg: FishConfig) -> FishSim:
    return FishSim(cfg, rhythm=TailRhythm(cfg), depth=DepthController(cfg, cfg.start_depth))


def run_window(cfg: FishConfig, speed_factor: float = 1.0, font: int = 150):
    sim = make_sim(cfg)
    controls = ViewerControls(cfg)
    meter = SpeedMeter()
    fluid = FluidForces(sim.model)
    dt = sim.model.opt.timestep
    fps = 60
    steps_per_frame = max(1, round(1.0 / fps / dt))
    last_print = -1.0
    last_time = sim.time
    with mujoco.viewer.launch_passive(sim.model, sim.data, key_callback=controls.on_key) as viewer:
        # kamera śledząca kadłub
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        viewer.cam.trackbodyid = sim.hull
        viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 1.4, 135.0, -20.0
        viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_TRANSPARENT] = True   # strzałki sił widać przez ciała
        while viewer.is_running():
            frame_start = time.perf_counter()
            with viewer.lock():
                if sim.data.time < last_time:      # Backspace w viewerze zresetował data
                    sim.reset(z=cfg.start_depth)
                    controls.__init__(cfg)
                    meter.value = 0.0
                controls.apply(sim)
                for _ in range(steps_per_frame):
                    sim.step()
                speed = meter.update(sim, steps_per_frame * dt)
                last_time = sim.time
                rows = show_overlay(viewer, sim, controls, speed, fluid, font)
            viewer.sync()
            if sim.time - last_print >= 1.0:       # zapas: stan w konsoli co 1 s
                print(" | ".join(f"{k}: {v}" for k, v in rows if k))
                last_print = sim.time
            # czas rzeczywisty (× speed_factor): śpij resztę klatki
            frame = steps_per_frame * dt / speed_factor
            time.sleep(max(0.0, frame - (time.perf_counter() - frame_start)))


def run_selftest(cfg: FishConfig):
    """Bez okna: te same klasy, skrypt klawiszy, wydruk stanu co 5 s."""
    sim = make_sim(cfg)
    controls = ViewerControls(cfg)
    meter = SpeedMeter()
    dt = sim.model.opt.timestep
    script = {10.0: [KEY_RIGHT] * 4, 25.0: [KEY_LEFT] * 4, 30.0: [KEY_PAGE_DOWN] * 2,
              50.0: [KEY_DOWN] * 2, 60.0: [KEY_SPACE]}
    for t_key, keys in script.items():
        print(f"t = {t_key:4.0f} s: klawisze {keys}")
    done = set()
    while sim.time < 70.0:
        for t_key, keys in script.items():
            if sim.time >= t_key and t_key not in done:
                for k in keys:
                    controls.on_key(k)
                done.add(t_key)
        controls.apply(sim)
        sim.step()
        speed = meter.update(sim, dt)
        if abs(sim.time / 5.0 - round(sim.time / 5.0)) < dt / 10:
            print(" | ".join(f"{k}: {v}" for k, v in status_lines(sim, controls, speed)))
    return sim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="bez okna, skrypt klawiszy")
    ap.add_argument("--speed", type=float, default=1.0, help="tempo względem czasu rzeczywistego (0.5 = 2× wolniej)")
    ap.add_argument("--font", type=int, default=150, choices=sorted(FONTS), help="skala tekstu nakładki [%%]")
    args = ap.parse_args()
    cfg = FishConfig()
    if args.selftest:
        run_selftest(cfg)
    else:
        run_window(cfg, args.speed, args.font)


if __name__ == "__main__":
    main()
