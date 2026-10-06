"""Wspólny styl wykresów (matplotlib, zapis PNG do results/)."""

import matplotlib

matplotlib.use("Agg")  # bez okien – tylko zapis do plików
import matplotlib.pyplot as plt

import om_config as C

# Kolejność kolorów serii jest stała: seria 1 zawsze niebieska, seria 2 zawsze pomarańczowa itd.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT_2, "axes.titlecolor": TEXT,
    "xtick.color": TEXT_2, "ytick.color": TEXT_2, "text.color": TEXT,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    "lines.linewidth": 2, "legend.frameon": False, "font.size": 10, "figure.dpi": 120,
})


def save(fig, name, subdir="tests"):
    out = C.RESULTS_DIR / subdir
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    return out / name


def compare(t, sim, ref, ylabel, title, name, sim_label="symulacja", ref_label="analitycznie"):
    """Dwa panele o wspólnej osi czasu: przebiegi (symulacja vs wzorzec) i błąd sim − ref."""
    fig, (ax, ax_err) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1.3]})
    ax.plot(t, sim, color=SERIES[0], label=sim_label)
    ax.plot(t, ref, color=SERIES[1], linestyle=(0, (4, 3)), label=ref_label)
    ax.set_ylabel(ylabel)
    # Tytuł i legenda nad wykresem, żeby legenda nigdy nie zasłaniała przebiegów.
    ax.set_title(title, loc="left", fontsize=11, pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    ax_err.plot(t, sim - ref, color=SERIES[0])
    ax_err.set_ylabel(f"błąd\n{ylabel}")
    ax_err.set_xlabel("czas [s]")
    return save(fig, name)
