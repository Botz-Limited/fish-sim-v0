#!/usr/bin/env python3
"""Generacja siatek ryby (OBJ) i scenariuszy XML z parametrów w config/default.json.

Uruchomienie (z katalogu Stonefish/):
    .venv/bin/python tools/make_meshes.py

Co robi:
 1. Tworzy siatki elipsoid (ikosfera przeskalowana do półosi):
      *_phy.obj – FIZYCZNE: mało trójkątów, bo Stonefish liczy wypór i opór
                  osobno dla KAŻDEJ ścianki (koszt ~ liczba trójkątów),
      *_vis.obj – WIZUALNE: gładkie, używane tylko do renderingu.
    Każda siatka jest zapisana w układzie swojego ogniwa (link frame):
    początek układu = przegub, oś X do przodu, Z w dół (NED, wymóg Stonefish).
 2. Liczy objętości i masy (tak jak zrobi to Stonefish: masa = gęstość·objętość
    siatki) i wyznacza BALAST (masę i położenie X) z dwóch warunków:
      - neutralna pływalność przy VBS w połowie zakresu,
      - trym wzdłużny: środek masy dokładnie pod środkiem wyporu.
 3. Wypełnia szablony tools/templates/*.scn.in -> data/scenarios/*.scn
    (pola @NAZWA@), bo Stonefish pozwala definiować materiały tylko w głównym
    pliku scenariusza – gęstości muszą trafić do każdego z nich.
 4. Wypisuje raport: masy, objętości, wypadkowa pływalność, położenie CG/CB.
"""

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fishcfg import ROOT, load_config  # noqa: E402

MESH_DIR = ROOT / "data" / "meshes"
SCN_DIR = ROOT / "data" / "scenarios"
TPL_DIR = ROOT / "tools" / "templates"


# ---------------------------------------------------------------- siatki

def ellipsoid(semi_axes, center=(0.0, 0.0, 0.0), subdiv=2) -> trimesh.Trimesh:
    """Elipsoida jako przeskalowana ikosfera (trójkąty o podobnej wielkości)."""
    m = trimesh.creation.icosphere(subdivisions=subdiv, radius=1.0)
    m.apply_scale(semi_axes)
    m.apply_translation(center)
    assert m.is_watertight and m.is_winding_consistent and m.volume > 0, "siatka musi być zamknięta"
    return m


def write_obj(mesh: trimesh.Trimesh, path: Path, comment: str):
    """Zapis OBJ w formacie, który czyta Stonefish: 'v', 'vn', 'f a//a b//b c//c'.

    Normalne w wierzchołkach (uśrednione) -> gładkie cieniowanie w rendererze.
    Kolejność wierzchołków w ściance: przeciwnie do ruchu wskazówek zegara patrząc
    z zewnątrz (normalna na zewnątrz) – od tego zależy znak objętości i wyporu.
    """
    v = mesh.vertices
    n = mesh.vertex_normals
    lines = [f"# {comment}", f"# {len(mesh.faces)} trojkatow, objetosc {mesh.volume * 1e6:.3f} ml",
             "# wygenerowane przez tools/make_meshes.py - nie edytuj recznie"]
    lines += [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in v]
    lines += [f"vn {x:.6f} {y:.6f} {z:.6f}" for x, y, z in n]
    lines += [f"f {a + 1}//{a + 1} {b + 1}//{b + 1} {c + 1}//{c + 1}" for a, b, c in mesh.faces]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


class Part:
    """Jedna bryła ryby: siatka fizyczna + położenie jej układu względem kadłuba."""

    def __init__(self, name, mesh, density, origin_x, buoyant=True, tail=True):
        self.tail = tail              # False = bryła przyspawana do głowy (płetwa grzbietowa)
        self.name = name
        self.mesh = mesh              # w układzie ogniwa
        self.density = density
        self.origin_x = origin_x      # [m] położenie układu ogniwa w układzie kadłuba (ogon prosty)
        self.buoyant = buoyant

    @property
    def volume(self):
        return self.mesh.volume

    @property
    def mass(self):
        return self.density * self.volume

    @property
    def centroid_z(self):
        return self.mesh.center_mass[2]

    @property
    def centroid_x(self):
        """Środek objętości (= środek masy przy stałej gęstości) w układzie kadłuba."""
        return self.origin_x + self.mesh.center_mass[0]


def build_meshes(cfg) -> dict:
    g = cfg["geometry"]
    mat = cfg["materials"]
    vbs = cfg["vbs"]
    sp, sv = g["phys_subdiv"], g["vis_subdiv"]
    MESH_DIR.mkdir(parents=True, exist_ok=True)

    out = {"parts": []}

    # --- kadłub (głowa): środek elipsoidy = początek układu base_link
    hull = ellipsoid(g["hull_semi_axes"], subdiv=sp)
    hull_vis = ellipsoid(g["hull_semi_axes"], subdiv=sv)
    out["parts"].append(Part("Hull", hull, mat["rho_hull"], 0.0, tail=False))
    head_phy, head_vis = hull, hull_vis
    # Płetwa grzbietowa jest częścią SIATKI GŁOWY (suma brył), a nie osobnym ogniwem:
    # Stonefish 1.5 źle liczy prędkości ogniw w rozgałęzionym drzewie kinematycznym
    # (README, "Błędy i pułapki"), więc łańcuch ryby musi być szeregowy.
    if g.get("dorsal_enabled", False):
        dc = tuple(g["dorsal_center"])
        dor = ellipsoid(g["dorsal_semi_axes"], dc, sp)
        dor_out = trimesh.boolean.difference([dor, hull], engine="manifold")   # część wystająca z kadłuba
        head_phy = trimesh.boolean.union([hull, dor], engine="manifold")
        head_vis = trimesh.boolean.union([hull_vis, ellipsoid(g["dorsal_semi_axes"], dc, sv)], engine="manifold")
        for m in (dor_out, head_phy, head_vis):
            assert m.is_watertight and m.volume > 0, "suma/różnica siatek musi być zamknięta"
        out["parts"].append(Part("Dorsal", dor_out, mat["rho_tail"], 0.0, tail=False))
    write_obj(head_phy, MESH_DIR / "head_phy.obj", "glowa (kadlub + pletwa grzbietowa) - siatka fizyczna")
    write_obj(head_vis, MESH_DIR / "head_vis.obj", "glowa (kadlub + pletwa grzbietowa) - siatka wizualna")

    # --- segmenty ogona: układ ogniwa i leży NA przegubie i, segment rozciąga się w −X.
    n = g["n_segments"]
    L = g["segment_length"]
    for i in range(n):
        s = 1.0 if n == 1 else 1.0 + (g["taper_last"] - 1.0) * i / (n - 1)   # liniowe zwężanie
        axes = (L / 2 + g["segment_overlap"], g["segment_ry0"] * s, g["segment_rz0"] * s)
        center = (-L / 2, 0.0, 0.0)
        m = ellipsoid(axes, center, sp)
        write_obj(m, MESH_DIR / f"seg{i + 1}_phy.obj", f"segment ogona {i + 1} - siatka fizyczna (uklad = przegub {i + 1})")
        write_obj(ellipsoid(axes, center, sv), MESH_DIR / f"seg{i + 1}_vis.obj", f"segment ogona {i + 1} - siatka wizualna")
        out["parts"].append(Part(f"Seg{i + 1}", m, mat["rho_tail"], g["tail_attach_x"] - i * L))

    # --- płetwa: osobne ogniwo przyspawane (joint fixed) na końcu ostatniego segmentu.
    # Przednia krawędź płetwy zachodzi o segment_overlap na koniec segmentu (jak w MuJoCo).
    fx = g["fin_semi_axes"][0]
    fin_center = (-fx + g["segment_overlap"], 0.0, 0.0)
    fin = ellipsoid(g["fin_semi_axes"], fin_center, sp)
    write_obj(fin, MESH_DIR / "fin_phy.obj", "pletwa ogonowa - siatka fizyczna (uklad = koniec ostatniego segmentu)")
    write_obj(ellipsoid(g["fin_semi_axes"], fin_center, sv), MESH_DIR / "fin_vis.obj", "pletwa ogonowa - siatka wizualna")
    fin_origin_x = g["tail_attach_x"] - n * L
    out["parts"].append(Part("Fin", fin, mat["rho_tail"], fin_origin_x))

    out["fin_center_x"] = fin_center[0]
    # Powierzchnia płetwy w rzucie bocznym (płaszczyzna XZ) – elipsa o półosiach fx, fz.
    out["fin_area"] = math.pi * g["fin_semi_axes"][0] * g["fin_semi_axes"][2]

    # --- VBS: dwie siatki (pusty / pełny) o wspólnym środku. Stonefish interpoluje
    # objętość wody i jej środek liniowo pomiędzy nimi.
    def vbs_mesh(volume):
        # elipsoida o proporcjach 2:1:1 i zadanej objętości
        a = (volume / (4.0 / 3.0 * math.pi * 0.25)) ** (1.0 / 3.0)
        return ellipsoid((a, a / 2, a / 2), subdiv=sp)

    write_obj(vbs_mesh(vbs["v_min"]), MESH_DIR / "vbs_empty.obj", "VBS - zbiornik pusty (objetosc minimalna)")
    write_obj(vbs_mesh(vbs["v_max"]), MESH_DIR / "vbs_full.obj", "VBS - zbiornik pelny (objetosc maksymalna)")

    return out


# ---------------------------------------------------------------- bilans mas i balast

def solve_ballast(cfg, parts) -> dict:
    """Masa i położenie X balastu z warunku pływalności neutralnej i trymu.

    Oznaczenia (układ kadłuba, ogon prosty):
      V   – objętość wypierana (kadłub + ogon + płetwa); balast jest WEWNĄTRZ
            kadłuba i nie wypiera dodatkowej wody (buoyant="false" w XML),
      V_n – objętość wody w VBS przy neutralności = połowa zakresu.
    (1) Σm + m_bal + ρ·V_n = ρ·V                -> m_bal
    (2) Σ(m·x) + m_bal·x_bal + ρ·V_n·x_vbs = x_CB·(ρ·V)  -> x_bal
    """
    rho = cfg["materials"]["rho_water"]
    vbs = cfg["vbs"]
    mat = cfg["materials"]
    V = sum(p.volume for p in parts)
    x_cb = sum(p.volume * p.centroid_x for p in parts) / V
    V_n = 0.5 * (vbs["v_min"] + vbs["v_max"])
    m_parts = sum(p.mass for p in parts)
    m_bal = rho * V - rho * V_n - m_parts
    if m_bal <= 0:
        raise SystemExit(f"Balast wychodzi ujemny ({m_bal * 1e3:.1f} g): kadłub za ciężki – zmniejsz rho_hull.")
    mx = sum(p.mass * p.centroid_x for p in parts) + rho * V_n * vbs["center"][0]
    x_bal = (x_cb * rho * V - mx) / m_bal
    vol_bal = m_bal / mat["rho_ballast"]
    len_bal = vol_bal / (mat["ballast_width"] * mat["ballast_height"])

    # Czy balast mieści się w kadłubie? Sprawdzamy 8 narożników prostopadłościanu.
    a, b, c = cfg["geometry"]["hull_semi_axes"]
    worst = 0.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                x = x_bal + sx * len_bal / 2
                y = sy * mat["ballast_width"] / 2
                z = mat["ballast_z"] + sz * mat["ballast_height"] / 2
                worst = max(worst, (x / a) ** 2 + (y / b) ** 2 + (z / c) ** 2)
    if worst >= 1.0:
        raise SystemExit(f"Balast ({len_bal * 100:.1f} cm) wystaje poza kadłub (max (x/a)²+... = {worst:.2f}) – zmień przekrój.")
    out = dict(V=V, x_cb=x_cb, V_n=V_n, m_parts=m_parts, m_bal=m_bal, x_bal=x_bal,
               vol_bal=vol_bal, len_bal=len_bal, fit=worst)
    out.update(head_mass_properties(cfg, [p for p in parts if not p.tail], out))
    return out


def head_mass_properties(cfg, head_parts, bal: dict) -> dict:
    """Masa, środek masy i główne momenty bezwładności GŁOWY = kadłub (+ płetwa grzbietowa) + balast.

    Dlaczego nie bryła złożona (compound) w XML: w Stonefish 1.5 Compound::getAugmentedInertia()
    zwraca samą bezwładność, bez masy dołączonej wody (dla zwykłej bryły "model" jest ona
    liczona z elipsoidy zastępczej). Głowa bez dołączonego momentu bezwładności
    odbija się na boki przy każdym machnięciu ogona. Dlatego głowa to zwykła bryła z siatki
    kadłuba (z niej wypór, opór i masa dołączona), a masę, środek masy i bezwładność
    z balastem podajemy jawnie (<mass>, <inertia>, <cg>) – jak dane z CAD.
    """
    mat = cfg["materials"]
    m_b = bal["m_bal"]
    dims = np.array([bal["len_bal"], mat["ballast_width"], mat["ballast_height"]])
    c_b = np.array([bal["x_bal"], 0.0, mat["ballast_z"]])
    I_b = m_b / 12.0 * np.diag([dims[1] ** 2 + dims[2] ** 2, dims[0] ** 2 + dims[2] ** 2, dims[0] ** 2 + dims[1] ** 2])
    M = sum(p.mass for p in head_parts) + m_b
    cg = (sum(p.mass * p.mesh.center_mass for p in head_parts) + m_b * c_b) / M

    def shift(I, m, c):    # twierdzenie Steinera dla tensora: I + m·(|d|²·1 − d·dᵀ)
        d = c - cg
        return I + m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))

    # trimesh: moment_inertia liczony dla gęstości 1 względem środka masy siatki
    I = shift(I_b, m_b, c_b) + sum(shift(p.mesh.moment_inertia * p.density, p.mass, p.mesh.center_mass) for p in head_parts)
    # Osie główne: balast przesunięty w X i Z daje niezerowe I_xz -> osie lekko obrócone wokół Y.
    w, R = np.linalg.eigh(I)
    # kolejność i zwroty osi jak najbliżej osi głowy (x, y, z), układ prawoskrętny
    order = [int(np.argmax(np.abs(R[i, :]))) for i in range(3)]
    R = R[:, order]
    w = w[order]
    for i in range(3):
        if R[i, i] < 0:
            R[:, i] = -R[:, i]
    if np.linalg.det(R) < 0:
        R[:, 2] = -R[:, 2]
    # rpy zgodnie z Stonefish: Quaternion(yaw, pitch, roll) = Rz·Ry·Rx
    pitch = -math.asin(max(-1.0, min(1.0, R[2, 0])))
    roll = math.atan2(R[2, 1], R[2, 2])
    yaw = math.atan2(R[1, 0], R[0, 0])
    return dict(head_mass=M, head_cg=cg, head_inertia=w, head_cg_rpy=(roll, pitch, yaw))


def report(cfg, parts, bal):
    rho = cfg["materials"]["rho_water"]
    g = 9.81
    vbs = cfg["vbs"]
    print("Bryły ryby (siatki fizyczne):")
    print(f"  {'bryła':8s} {'masa [g]':>9s} {'V [ml]':>9s} {'ρ [kg/m³]':>10s} {'x_C [mm]':>9s}")
    for p in parts:
        print(f"  {p.name:8s} {p.mass * 1e3:9.1f} {p.volume * 1e6:9.1f} {p.density:10.0f} {p.centroid_x * 1e3:9.1f}")
    print(f"  {'Ballast':8s} {bal['m_bal'] * 1e3:9.1f} {'(0)':>9s} {cfg['materials']['rho_ballast']:10.0f} {bal['x_bal'] * 1e3:9.1f}"
          f"   <- wyliczony: {bal['len_bal'] * 100:.2f} x {cfg['materials']['ballast_width'] * 100:.1f}"
          f" x {cfg['materials']['ballast_height'] * 100:.1f} cm")
    m_dry = bal["m_parts"] + bal["m_bal"]
    print(f"  SUMA (bez wody w VBS) {m_dry * 1e3:.1f} g, objętość {bal['V'] * 1e6:.1f} ml")
    print("\nPływalność (wypór − ciężar), ryba bez wody w VBS jest lekko DODATNIO pływalna:")
    for label, Vw in (("VBS pusty", vbs["v_min"]), ("VBS neutralny", bal["V_n"]), ("VBS pełny", vbs["v_max"])):
        F = (rho * bal["V"] - m_dry - rho * Vw) * g
        print(f"  {label:14s} {Vw * 1e6:5.1f} ml -> {F:+.4f} N")
    # środek masy w pionie (z, NED: + w dół) przy VBS neutralnym
    M = m_dry + rho * bal["V_n"]
    z_cg = (bal["m_bal"] * cfg["materials"]["ballast_z"] + rho * bal["V_n"] * vbs["center"][2]
            + sum(p.mass * p.centroid_z for p in parts)) / M
    z_cb = sum(p.volume * p.centroid_z for p in parts) / bal["V"]
    print(f"\nCB całej ryby: x = {bal['x_cb'] * 1e3:.2f} mm, z = {z_cb * 1e3:+.2f} mm")
    print(f"CG całej ryby: x = {bal['x_cb'] * 1e3:.2f} mm (trym), z = {z_cg * 1e3:+.2f} mm "
          f"-> CG {(z_cg - z_cb) * 1e3:.2f} mm POD CB (moment prostujący)")
    print(f"Głowa (kadłub + balast): masa {bal['head_mass'] * 1e3:.1f} g, środek masy "
          f"({', '.join(f'{c * 1e3:+.2f}' for c in bal['head_cg'])}) mm, "
          f"I = ({', '.join(f'{i * 1e4:.2f}' for i in bal['head_inertia'])}) kg·cm², "
          f"osie główne obrócone o {math.degrees(bal['head_cg_rpy'][1]):+.2f}° wokół Y")
    print(f"Płetwa: powierzchnia w rzucie bocznym S = {cfg['_fin_area'] * 1e4:.1f} cm² (do modelu siły nośnej w C++)")


# ---------------------------------------------------------------- szablony XML


def fill_templates(cfg, bal, meshes):
    g, mat, j, vbs, s = cfg["geometry"], cfg["materials"], cfg["joints"], cfg["vbs"], cfg["sensors"]
    fmt = lambda x: repr(float(x))                                   # pełna precyzja
    vec = lambda v: " ".join(fmt(x) for x in v)
    lim = math.radians(j["limit_deg"])
    values = {
        "RHO_WATER": fmt(mat["rho_water"]),
        "RHO_HULL": fmt(mat["rho_hull"]),
        "RHO_TAIL": fmt(mat["rho_tail"]),
        "RHO_BALLAST": fmt(mat["rho_ballast"]),
        "BALLAST_DIMS": vec((bal["len_bal"], mat["ballast_width"], mat["ballast_height"])),
        "BALLAST_XYZ": vec((bal["x_bal"], 0.0, mat["ballast_z"])),
        "BALLAST_MASS_G": f"{bal['m_bal'] * 1e3:.1f}",
        "HULL_MASS_G": f"{meshes['parts'][0].mass * 1e3:.1f}",
        "HEAD_MASS": fmt(bal["head_mass"]),
        "HEAD_INERTIA": vec(bal["head_inertia"]),
        "HEAD_CG_XYZ": vec(bal["head_cg"]),
        "HEAD_CG_RPY": vec(bal["head_cg_rpy"]),
        "TAIL_ATTACH_XYZ": vec((g["tail_attach_x"], 0.0, 0.0)),
        "SEG_JOINT_XYZ": vec((-g["segment_length"], 0.0, 0.0)),
        "JOINT_MIN": fmt(-lim),
        "JOINT_MAX": fmt(lim),
        "JOINT_LIMIT_DEG": f"{j['limit_deg']:g}",
        "JOINT_DAMPING": fmt(j["damping"]),
        "VBS_CENTER": vec(vbs["center"]),
        "VBS_NEUTRAL": fmt(bal["V_n"]),
        "VBS_MIN": fmt(vbs["v_min"]),
        "VBS_MAX": fmt(vbs["v_max"]),
        "P_RATE": fmt(s["pressure_rate"]),
        "P_NOISE": fmt(s["pressure_noise"]),
        "IMU_RATE": fmt(s["imu_rate"]),
        "IMU_NOISE_ANGLE": vec(s["imu_noise_angle"]),
        "IMU_NOISE_GYRO": fmt(s["imu_noise_gyro"]),
        "IMU_YAW_DRIFT": fmt(s["imu_yaw_drift"]),
        "IMU_NOISE_ACC": fmt(s["imu_noise_acc"]),
    }
    SCN_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for tpl in sorted(TPL_DIR.glob("*.scn.in")):
        text = tpl.read_text(encoding="utf-8")
        missing = sorted(set(re.findall(r"@([A-Z0-9_]+)@", text)) - set(values))
        if missing:
            raise SystemExit(f"{tpl.name}: brak wartości dla {missing}")
        for k, v in values.items():
            text = text.replace(f"@{k}@", v)
        header = (f"<!-- WYGENEROWANE przez tools/make_meshes.py z tools/templates/{tpl.name}.\n"
                  f"     Zmiany wprowadzaj w szablonie albo w config/default.json i uruchom generator ponownie. -->\n")
        # deklaracja <?xml?> musi zostać w pierwszej linii
        first, rest = text.split("\n", 1)
        out = SCN_DIR / tpl.name[:-3]
        out.write_text(first + "\n" + header + rest, encoding="utf-8")
        written.append(out.name)
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="plik nadpisań (merge-patch) dla config/default.json")
    args = ap.parse_args()
    cfg = load_config(args.config)
    meshes = build_meshes(cfg)
    cfg["_fin_area"] = meshes["fin_area"]
    bal = solve_ballast(cfg, meshes["parts"])
    report(cfg, meshes["parts"], bal)
    written = fill_templates(cfg, bal, meshes)
    print(f"\nSiatki: {MESH_DIR.relative_to(ROOT)}/  Scenariusze: {', '.join(written)}")


if __name__ == "__main__":
    main()
