"""Etap 0: sprawdzenie wersji MuJoCo i kilku założeń SPEC, zanim zbudujemy rybę.

Uruchom: .venv/bin/python scripts/check_api.py
Każdy test wypisuje PASS/FAIL. Kod wyjścia != 0, gdy coś nie przeszło.
"""

import inspect
import sys

import mujoco
import mujoco.viewer

# Kula o gęstości wody: masa = ρ·V. Gdyby MuJoCo samo liczyło wypór,
# taka kula byłaby w wodzie neutralna i nie tonęłaby.
XML = """
<mujoco>
  <option timestep="0.002" integrator="implicitfast" density="1000" viscosity="0.0009"/>
  <worldbody>
    <body name="ball" pos="0 0 0">
      <freejoint/>
      <geom type="sphere" size="0.05" density="1000" fluidshape="ellipsoid"/>
    </body>
  </worldbody>
</mujoco>
"""

T_SIM = 1.0  # [s] czas każdej próby
results = []


def check(name, ok, detail):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def drop_test(model, buoyancy_force):
    """Symuluje T_SIM sekund i zwraca zmianę wysokości kuli [m].

    buoyancy_force – siła w górę [N] przykładana ręcznie przez xfrc_applied
    (układ świata, w środku masy ciała – tak to zdefiniowane w MuJoCo).
    """
    data = mujoco.MjData(model)
    body = model.body("ball").id
    z0 = data.qpos[2]
    for _ in range(int(T_SIM / model.opt.timestep)):
        # xfrc_applied: [Fx, Fy, Fz, Mx, My, Mz]; MuJoCo nie zeruje go po kroku,
        # ale ustawiamy co krok, tak jak będzie w docelowej pętli symulacji.
        data.xfrc_applied[body, 2] = buoyancy_force
        mujoco.mj_step(model, data)
    return data.qpos[2] - z0


print(f"mujoco {mujoco.__version__}, Python {sys.version.split()[0]}")
model = mujoco.MjModel.from_xml_string(XML)
mass = model.body_mass[model.body("ball").id]
weight = mass * abs(model.opt.gravity[2])
print(f"kula: m = {mass:.4f} kg, ciężar = {weight:.3f} N")

# (a) Model płynu daje tylko opór/nośność, nie wypór -> kula o gęstości wody tonie.
dz = drop_test(model, buoyancy_force=0.0)
check("(a) brak wyporu w modelu płynu", dz < -0.1,
      f"Δz = {dz:+.3f} m po {T_SIM} s (tonie => wypór trzeba liczyć samemu)")

# (b) Ręczny wypór ρ·g·V przez xfrc_applied równoważy ciężar -> kula stoi.
# Dla kuli o gęstości wody ρ·g·V = m·g dokładnie.
dz = drop_test(model, buoyancy_force=weight)
check("(b) xfrc_applied jako wypór", abs(dz) < 1e-6,
      f"Δz = {dz:+.2e} m (siła w górę = m·g w COM)")

# (c) API viewera pasywnego, którego użyjemy w etapie 7 (bez otwierania okna).
params = inspect.signature(mujoco.viewer.launch_passive).parameters
check("(c1) launch_passive(key_callback=...)", "key_callback" in params,
      f"parametry: {', '.join(params)}")
handle_cls = getattr(mujoco.viewer, "Handle", None)
has_texts = handle_cls is not None and hasattr(handle_cls, "set_texts")
check("(c2) Handle.set_texts (nakładka tekstowa)", has_texts,
      "dostępne" if has_texts else "brak – w etapie 7 zostaje print w konsoli")

# (d) Brak subtree_linvel bez jawnego wywołania mj_subtreeVel (liczone na żądanie).
data = mujoco.MjData(model)
data.qvel[0] = 1.0  # kula leci w +X z prędkością 1 m/s
mujoco.mj_forward(model, data)
before = data.subtree_linvel[1, 0]
mujoco.mj_subtreeVel(model, data)
after = data.subtree_linvel[1, 0]
check("(d) subtree_linvel po mj_subtreeVel", abs(after - 1.0) < 1e-9,
      f"przed wywołaniem: {before:.3f}, po: {after:.3f} m/s")

sys.exit(0 if all(results) else 1)
