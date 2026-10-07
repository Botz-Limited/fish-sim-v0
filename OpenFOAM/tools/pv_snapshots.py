"""Zrzuty pola wirowości (ślad wirowy za ogonem) – uruchamiać przez pvbatch.

Użycie (z katalogu OpenFOAM/):
    pvbatch tools/pv_snapshots.py <katalog_przypadku_FSI> <prefiks_pliku> [liczba_zrzutów]
np.
    pvbatch tools/pv_snapshots.py 05-fsi-inflow/U0.1 e5_vorticity_U0.1 4

Wczytuje fluid-openfoam (wbudowany czytnik OpenFOAM w ParaView), bierze
ostatnie N zapisanych chwil (domyślnie 4, czyli np. jeden okres przy zapisie
co 1/4 okresu) i zapisuje PNG z polem wirowości (składowa z) w results/.
Kolory: czerwony = wir lewoskrętny (przeciwnie do zegara), niebieski = prawoskrętny.
"""
import sys
from pathlib import Path

from paraview.simple import (  # noqa: F401 – API ParaView
    ColorBy, GetActiveViewOrCreate, GetAnimationScene, GetColorTransferFunction, GetScalarBar,
    OpenFOAMReader, ResetSession, SaveScreenshot, Show, Text, UpdatePipeline,
)

case = Path(sys.argv[1]).resolve()
prefix = sys.argv[2]
n_snap = int(sys.argv[3]) if len(sys.argv) > 3 else 4
results = Path(__file__).resolve().parent.parent / "results"
results.mkdir(exist_ok=True)

fluid = case / "fluid-openfoam" if (case / "fluid-openfoam").is_dir() else case
foam = fluid / f"{fluid.name}.foam"
foam.touch()
reader = OpenFOAMReader(FileName=str(foam))
reader.MeshRegions = ["internalMesh"]
reader.CellArrays = ["vorticity", "U", "p"]
reader.CaseType = "Reconstructed Case"
reader.UpdatePipelineInformation()
times = [t for t in reader.TimestepValues if t > 0]
if not times:
    sys.exit(f"brak zapisanych chwil w {foam}")

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [1600, 700]
view.OrientationAxesVisibility = 0
view.Background = [1, 1, 1]
for attr, val in (("UseColorPaletteForBackground", 0), ("BackgroundColorMode", "Single Color")):
    try:
        setattr(view, attr, val)
    except (AttributeError, ValueError):
        pass

disp = Show(reader, view)
ColorBy(disp, ("CELLS", "vorticity", "Z"))
lut = GetColorTransferFunction("vorticity")
lut.ApplyPreset("Cool to Warm", True)
lut.VectorMode = "Component"   # bez tego ParaView potrafi pokazać moduł wektora
lut.VectorComponent = 2        # składowa z
lut.RescaleTransferFunction(-20.0, 20.0)   # [1/s] – stała skala dla porównań
disp.SetScalarBarVisibility(view, True)
bar = GetScalarBar(lut, view)
bar.Title = "wirowość z [1/s]"
bar.ComponentTitle = ""
bar.TitleColor = bar.LabelColor = [0, 0, 0]
label = Text()
label_disp = Show(label, view)
label_disp.Color = [0, 0, 0]
label_disp.FontSize = 14
label_disp.WindowLocation = "Upper Left Corner"

# kamera: od głowy do ~4 długości ogona za końcówką
view.CameraPosition = [0.3, 0.0, 3.0]
view.CameraFocalPoint = [0.3, 0.0, 0.5]
view.CameraViewUp = [0, 1, 0]
view.CameraParallelProjection = 1
view.CameraParallelScale = 0.17

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
for k, t in enumerate(times[-n_snap:]):
    view.ViewTime = t
    label.Text = f"{case.name}   t = {t:.3f} s   wirowość (składowa z) [1/s]"
    UpdatePipeline(time=t, proxy=reader)
    out = results / f"{prefix}_{k}.png"
    SaveScreenshot(str(out), view, ImageResolution=[1600, 700])
    print(f"zapisano {out}")
