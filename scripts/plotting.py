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


def series(t, curves, ylabel, title, name, hlines=(), bottom=None):
    """Przebiegi czasowe z opcjonalnymi poziomymi liniami odniesienia i dolnym panelem.

    curves: [(y, etykieta), ...]; hlines: [(wartość, etykieta), ...];
    bottom: (y, etykieta_osi) – osobny panel (np. odchyłka), bez drugiej osi Y.
    """
    if bottom is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig, (ax, ax_b) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True,
                                       gridspec_kw={"height_ratios": [3, 1.3]})
    for i, (y, label) in enumerate(curves):
        ax.plot(t, y, color=SERIES[i], label=label)
    for value, label in hlines:
        ax.axhline(value, color=TEXT_2, linewidth=1, linestyle=(0, (2, 2)))
        ax.annotate(label, (t[-1], value), xytext=(-4, 4), textcoords="offset points",
                    ha="right", va="bottom", color=TEXT_2, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=11, pad=26 if len(curves) > 1 else 6)
    if len(curves) > 1:
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(curves), borderaxespad=0.2)
    if bottom is None:
        ax.set_xlabel("czas [s]")
    else:
        ax_b.plot(t, bottom[0], color=SERIES[0])
        ax_b.set_ylabel(bottom[1])
        ax_b.set_xlabel("czas [s]")
    return save(fig, name)


def panels(t, rows, title, name, subdir="examples"):
    """Kilka paneli jeden pod drugim, wspólna oś czasu; każda wielkość fizyczna we własnym panelu.

    rows: [(etykieta_osi_Y, [(y, etykieta_serii), ...]), ...]
    """
    fig, axes = plt.subplots(len(rows), 1, figsize=(9, 2.1 * len(rows) + 0.6), sharex=True)
    for ax, (ylabel, curves) in zip(axes, rows):
        for i, (y, label) in enumerate(curves):
            ax.plot(t, y, color=SERIES[i], label=label)
        ax.set_ylabel(ylabel)
        if len(curves) > 1:
            ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    axes[0].set_title(title, loc="left", fontsize=11)
    axes[-1].set_xlabel("czas [s]")
    fig.align_ylabels(axes)
    return save(fig, name, subdir)
