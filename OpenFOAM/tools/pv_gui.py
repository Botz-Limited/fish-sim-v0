"""ParaView state for viewing an FSI case in the GUI.

Usage (from the OpenFOAM/ directory):
    paraview --script=tools/pv_gui.py                      # default 05-fsi-inflow/U0.2
    FSI_CASE=04-fsi-actuated/water paraview --script=tools/pv_gui.py

Shows the vorticity field (z component) around the deforming tail and sets up
an animation over the saved time steps – press Play (▶) on the toolbar.

Readouts (they follow the animation time):
- text in the upper left corner: time and the water force on the body (head + tail)
  and on the tail alone, pressure and viscous parts, and the moment on the tail
  about its root – read from postProcessing/forcesBody and forcesTail (the `forces`
  function objects in system/controlDict), interpolated to the current time;
- arrows at the centroids of the body and of the tail: total water force (black =
  body, magenta = tail); the arrow scale is chosen from the forces of the run and
  printed in the text.
Forces are per metre of span (2D case): N/m, shown as mN/m.
"""
import os
from pathlib import Path

from paraview.simple import (
    ColorBy, GetActiveViewOrCreate, GetAnimationScene, GetColorTransferFunction,
    GetScalarBar, Glyph, OpenFOAMReader, ProgrammableFilter, PythonAnnotation, Render, Show,
)

root = Path(os.environ.get("PWD", ".")).resolve()
case = root / os.environ.get("FSI_CASE", "05-fsi-inflow/U0.2")
fluid = case / "fluid-openfoam" if (case / "fluid-openfoam").is_dir() else case
foam = fluid / f"{fluid.name}.foam"
foam.touch()

reader = OpenFOAMReader(registrationName=case.name, FileName=str(foam))
reader.MeshRegions = ["internalMesh"]
reader.CellArrays = ["vorticity", "U", "p"]

view = GetActiveViewOrCreate("RenderView")
disp = Show(reader, view)
ColorBy(disp, ("CELLS", "vorticity", "Z"))
lut = GetColorTransferFunction("vorticity")
lut.ApplyPreset("Cool to Warm", True)
lut.VectorMode = "Component"
lut.VectorComponent = 2
lut.RescaleTransferFunction(-20.0, 20.0)
lut.AutomaticRescaleRangeMode = "Never"
disp.SetScalarBarVisibility(view, True)
GetScalarBar(lut, view).Title = "vorticity z [1/s]"

# ---- readouts: water forces from the function objects, at the current animation time
# (The filter namespace imports VTK numpy algorithms, which shadow max/min: use np.*.)
# The filter's input is the moving body surface (so the arrows follow the tail); its
# output is two points (body, tail) with the force interpolated to the time of the input.
FORCE_SCRIPT = r"""
import numpy as np
from pathlib import Path
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkCompositeDataSet, vtkDataObject, vtkPolyData
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy

def load(name, kind):
    # all restart directories (postProcessing/<name>/<start time>/<kind>.dat), sorted by time
    parts = sorted(Path(PP, name).glob("*/" + kind + ".dat"), key=lambda f: float(f.parent.name))
    a = np.vstack([np.loadtxt(f, comments="#", ndmin=2) for f in parts])
    _, keep = np.unique(a[:, 0], return_index=True)
    return a[keep]

def at(a, t):
    return np.array([np.interp(t, a[:, 0], a[:, j]) for j in range(1, a.shape[1])])

inp = self.GetInputDataObject(0, 0)
t = inp.GetInformation().Get(vtkDataObject.DATA_TIME_STEP()) or 0.0
pts = {"head": [], "tail": []}
it = inp.NewIterator()
it.InitTraversal()
while not it.IsDoneWithTraversal():
    name = it.GetCurrentMetaData().Get(vtkCompositeDataSet.NAME())
    block = it.GetCurrentDataObject()
    if block.GetNumberOfPoints():
        pts["tail" if "tail" in name else "head"].append(vtk_to_numpy(block.GetPoints().GetData()))
    it.GoToNextItem()
tail = np.vstack(pts["tail"])
body = np.vstack(pts["head"] + pts["tail"])

fb, ft = load("forcesBody", "force"), load("forcesTail", "force")
mt = load("forcesTail", "moment")
F = np.array([at(fb, t), at(ft, t)])          # rows: body, tail; columns: total, pressure, viscous (x, y, z)
# arrow scale: 95th percentile of |F_body| after the first 10% of the run (start-up spike) -> 0.12 m
late = fb[fb[:, 0] > 0.1 * fb[-1, 0]]
ref = float(np.maximum(np.percentile(np.linalg.norm(late[:, 1:3], axis=1), 95), 1e-9))
scale = 0.12 / ref

out = self.GetOutputDataObject(0)
p = vtkPoints()
base = np.array([body.mean(axis=0), tail.mean(axis=0)])
base[:, 2] = body[:, 2].max() + 1e-3            # in front of the 2D slab, otherwise the mesh hides the arrows
p.SetData(numpy_to_vtk(base, deep=1))
out.SetPoints(p)
verts = vtkCellArray()
for i in range(2):
    verts.InsertNextCell(1)
    verts.InsertCellPoint(i)
out.SetVerts(verts)
def add(name, values):
    arr = numpy_to_vtk(np.ascontiguousarray(values, dtype=float), deep=1)
    arr.SetName(name)
    out.GetPointData().AddArray(arr)
add("F_total", F[:, 0:3])
add("F_pressure", F[:, 3:6])
add("F_viscous", F[:, 6:9])
add("arrow", np.c_[F[:, 0:2], np.zeros(2)] * scale)
add("M_tail_z", np.full(2, at(mt, t)[2]))
add("arrow_ref", np.full(2, 1e3 * ref))
add("which", np.array([0.0, 1.0]))
"""

surface = OpenFOAMReader(registrationName="body surface", FileName=str(foam))
surface.MeshRegions = ["patch/head", "patch/tail"]
surface.CellArrays = []
forces = ProgrammableFilter(registrationName="water forces", Input=surface)
forces.OutputDataSetType = "vtkPolyData"
forces.Script = f"PP = {str(fluid / 'postProcessing')!r}\n" + FORCE_SCRIPT

arrows = Glyph(registrationName="force arrows", Input=forces, GlyphType="Arrow")
arrows.OrientationArray = ["POINTS", "arrow"]
arrows.ScaleArray = ["POINTS", "arrow"]
arrows.VectorScaleMode = "Scale by Magnitude"
arrows.ScaleFactor = 1.0
arrows.GlyphMode = "All Points"
arrows.GlyphType.TipRadius = 0.12
arrows.GlyphType.ShaftRadius = 0.04
arrows_disp = Show(arrows, view)
ColorBy(arrows_disp, ("POINTS", "which"))
which = GetColorTransferFunction("which")
which.InterpretValuesAsCategories = 1
which.Annotations = ["0", "body", "1", "tail"]
which.IndexedColors = [0.0, 0.0, 0.0, 1.0, 0.0, 1.0]
arrows_disp.SetScalarBarVisibility(view, False)

text = PythonAnnotation(registrationName="force readout", Input=forces)
text.ArrayAssociation = "Point Data"
text.Expression = (
    '"t = %6.3f s      water force per metre of span [mN/m]\\n'
    '                     F_x (drag +)   F_y     pressure x/y      viscous x/y\\n'
    'BODY (head+tail)  %+9.1f  %+9.1f   %+8.1f %+8.1f   %+7.1f %+7.1f\\n'
    'TAIL              %+9.1f  %+9.1f   %+8.1f %+8.1f   %+7.1f %+7.1f\\n'
    'moment on tail about root  M_z = %+.2f mN m/m\\n'
    'arrows: black = body, magenta = tail   (0.12 m = %.0f mN/m)" % ('
    't_value, '
    'F_total[0,0]*1e3, F_total[0,1]*1e3, F_pressure[0,0]*1e3, F_pressure[0,1]*1e3, F_viscous[0,0]*1e3, F_viscous[0,1]*1e3, '
    'F_total[1,0]*1e3, F_total[1,1]*1e3, F_pressure[1,0]*1e3, F_pressure[1,1]*1e3, F_viscous[1,0]*1e3, F_viscous[1,1]*1e3, '
    'M_tail_z[0]*1e3, arrow_ref[0])'
)
text_disp = Show(text, view)
text_disp.WindowLocation = "Upper Left Corner"
text_disp.FontFamily = "Courier"
text_disp.Justification = "Left"
text_disp.FontSize = int(os.environ.get("PV_FONT", "26"))
text_disp.Color = [1.0, 1.0, 1.0]
text_disp.BackgroundColor = [0.08, 0.1, 0.14, 0.8]
text_disp.ShowBorder = "Always"

view.OrientationAxesVisibility = 0

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
# Slower playback: ParaView 6 has no real-time play mode, Play renders frames as fast as it can.
# "Sequence" mode with PV_FRAMES_PER_STEP frames per saved time step shows each step that many times.
steps = len(reader.TimestepValues or [0])
scene.PlayMode = "Sequence"
# (no max(): the ParaView Python shell imports VTK numpy algorithms, which shadow it)
scene.NumberOfFrames = int(float(os.environ.get("PV_FRAMES_PER_STEP", "2")) * steps) + 1
scene.AnimationTime = reader.TimestepValues[-1] if reader.TimestepValues else 0
Render()
# camera last: the first render resets it to fit all data (the whole fluid domain)
view.CameraPosition = [0.3, 0.0, 3.0]
view.CameraFocalPoint = [0.3, 0.0, 0.5]
view.CameraViewUp = [0, 1, 0]
view.CameraParallelProjection = 1
view.CameraParallelScale = 0.2
Render()
