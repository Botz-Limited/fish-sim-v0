"""ParaView state for viewing an FSI case in the GUI.

Usage (from the OpenFOAM/ directory):
    paraview --script=tools/pv_gui.py                      # default 05-fsi-inflow/U0.2
    FSI_CASE=04-fsi-actuated/water paraview --script=tools/pv_gui.py

Shows the vorticity field (z component) around the deforming tail and sets up
an animation over the saved time steps – press Play (▶) on the toolbar.
"""
import os
from pathlib import Path

from paraview.simple import (
    ColorBy, GetActiveViewOrCreate, GetAnimationScene, GetColorTransferFunction,
    GetScalarBar, OpenFOAMReader, Render, Show,
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

view.OrientationAxesVisibility = 0
view.CameraPosition = [0.3, 0.0, 3.0]
view.CameraFocalPoint = [0.3, 0.0, 0.5]
view.CameraViewUp = [0, 1, 0]
view.CameraParallelProjection = 1
view.CameraParallelScale = 0.2

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
scene.AnimationTime = reader.TimestepValues[-1] if reader.TimestepValues else 0
Render()
