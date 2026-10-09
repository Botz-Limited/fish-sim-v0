"""On-screen readouts for the SOFA GUI: lines of text drawn over the 3D view.

SOFA has no "status panel" component, but OglLabel writes one line of overlay text at a
fixed pixel position. A Hud is a column of OglLabels; a controller calls show() every step
with the new lines. The overlay font covers ASCII only, so labels avoid Greek letters and
degree signs (dp, deg).

Also here: per-section water forces for the force arrows (used by replay and the live scene).
"""
import numpy as np

PLUGINS = ["Sofa.GL.Component.Rendering2D"]


class Hud:
    def __init__(self, root, n_lines: int, x: int = 70, y: int = 24, size: int = 22,
                 color=(1.0, 1.0, 1.0, 1.0), name: str = "hud"):
        root.addObject("RequiredPlugin", pluginName=PLUGINS)
        dy = int(round(size * 1.7))
        self.labels = [root.addObject("OglLabel", name=f"{name}{i}", label=" ", x=x, y=y + i * dy,
                                      fontsize=size, color=list(color), updateLabelEveryNbSteps=1)
                       for i in range(n_lines)]

    def show(self, lines):
        for i, lab in enumerate(self.labels):
            lab.label.value = lines[i] if i < len(lines) and lines[i] else " "


class Sections:
    """Groups skin nodes into n slices along the tail (by rest position x) and sums the
    nodal water forces of each slice: one arrow per slice is readable, one per node is not."""

    def __init__(self, x0: np.ndarray, skin: np.ndarray, n: int = 8):
        xs = x0[skin, 0]
        edges = np.linspace(xs.min(), xs.max(), n + 1)
        idx = np.clip(np.digitize(xs, edges) - 1, 0, n - 1)
        self.groups = [skin[idx == k] for k in range(n) if np.any(idx == k)]

    def points(self, x: np.ndarray) -> np.ndarray:
        """Arrow base: centroid of each slice in the current configuration (K, 3)."""
        return np.array([x[g].mean(axis=0) for g in self.groups])

    def forces(self, node_forces: np.ndarray) -> np.ndarray:
        """Sum of nodal forces in each slice (K, 3) [N]."""
        return np.array([node_forces[g].sum(axis=0) for g in self.groups])


def add_arrows(root, n: int, name: str = "forceArrows"):
    """A node whose ConstantForceField only DRAWS arrows: no solver acts on it.
    Update `dofs.position` and `ff.forces`, and set `ff.showArrowSize` [m/N]."""
    root.addObject("RequiredPlugin", pluginName=["Sofa.Component.MechanicalLoad", "Sofa.Component.StateContainer"])
    node = root.addChild(name)
    dofs = node.addObject("MechanicalObject", name="dofs", template="Vec3d", position=[[0.0, 0.0, 0.0]] * n)
    ff = node.addObject("ConstantForceField", name="ff", indices=list(range(n)), forces=[[0.0, 0.0, 0.0]] * n,
                        showArrowSize=0.0)
    return dofs, ff
