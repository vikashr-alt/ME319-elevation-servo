"""Render the Octave/MATLAB CSV outputs as paper figures (NumPy, Matplotlib)."""
from pathlib import Path
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parent
BLUE, ORANGE, GRAY, BLACK = "#194f86", "#a64e18", "#768492", "#20252c"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "axes.edgecolor": "#838b94", "grid.color": "#e1e5e9", "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 8, "lines.linewidth": 1.5,
    "figure.dpi": 140, "savefig.dpi": 300,
})


def read(results, name):
    return np.genfromtxt(results / f"{name}.csv", delimiter=",", names=True)


def save(fig, figures, name):
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"{name}.{suffix}", facecolor="white")
    plt.close(fig)


def draw_architecture(figures):
    fig, (a, b) = plt.subplots(2, 1, figsize=(4.15, 2.38),
                              gridspec_kw={"height_ratios": [1, 1.12]})
    fig.subplots_adjust(left=.02, right=.98, bottom=.04, top=.97, hspace=.25)
    for ax in (a, b):
        ax.set(xlim=(0, 100), ylim=(0, 33))
        ax.axis("off")

    def box(ax, x, y, w, label):
        ax.add_patch(Rectangle((x, y), w, 10, edgecolor=BLUE, facecolor="#f2f6fa"))
        ax.text(x+w/2, y+5, label, ha="center", va="center", fontsize=7.4)

    def arrow(ax, x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                                     mutation_scale=9, color=BLACK, linewidth=1))

    a.text(0, 30, "(a) Electromechanical axis", weight="bold", fontsize=8.3)
    box(a, 10, 11, 23, "DC motor")
    box(a, 42, 11, 20, "100:1 gear")
    box(a, 71, 11, 25, "Pivoted load")
    for start, end in [(0, 10), (33, 42), (62, 71)]:
        arrow(a, start, 16, end, 16)
    a.text(4, 21, "$V$", ha="center", fontsize=8)
    a.text(37.5, 20, r"$N\omega$", ha="center", fontsize=8)
    a.text(66.5, 20, r"$\omega$", ha="center", fontsize=8)
    for x, label in [(21.5, "$R, L, K_t, K_e, J_m$"), (83.5, r"$J_{\mathrm{load}}, b$")]:
        a.text(x, 3, label, ha="center", fontsize=8)

    b.text(0, 30, "(b) Closed-loop bench servo", weight="bold", fontsize=8.3)
    b.add_patch(Circle((18, 17), 3.2, edgecolor=BLACK, facecolor="white"))
    b.text(18, 17, r"$\Sigma$", ha="center", va="center", fontsize=8)
    box(b, 33, 12, 24, "$G_c(s)$")
    box(b, 69, 12, 20, "$G_p(s)$")
    for start, end in [(0, 14.8), (21.2, 33), (57, 69), (89, 100)]:
        arrow(b, start, 17, end, 17)
    for x, label in [(5, "$r_h$"), (26.5, "$e$"), (62.5, "$V$"), (95, r"$\theta$")]:
        b.text(x, 20, label, ha="center", fontsize=8)
    b.plot([94, 94, 18], [17, 3, 3], color=BLACK, lw=1)
    arrow(b, 18, 3, 18, 13.8)
    b.text(20.2, 10, "$-$", fontsize=8)
    save(fig, figures, "architecture")


def draw_frequency(results, figures):
    data = read(results, "frequency")
    w = data["omega_rad_s"]
    fig, (gain, phase) = plt.subplots(2, 1, sharex=True, figsize=(4.15, 2.65),
                                    layout="constrained")
    for ax, label, field, baseline in [
        (gain, "Magnitude (dB)", "loop_dB", "p_only_dB"),
        (phase, "Phase (deg)", "loop_phase_deg", "p_only_phase_deg"),
    ]:
        ax.semilogx(w, data[field], color=BLUE, label="Lead loop")
        ax.semilogx(w, data[baseline], "--", color=GRAY, label="P-only loop")
        ax.grid(True)
        ax.set(ylabel=label, xlim=(.1, 200))
    gain.axhline(0, color=BLACK, lw=.7)
    phase.axhline(-180, color=BLACK, lw=.7)
    gain.legend(loc="lower left")
    phase.set(xlabel="Frequency (rad/s)")
    save(fig, figures, "frequency")


def draw_step(results, figures):
    step = read(results, "step")
    t = step["t_s"]
    fig, (angle, effort) = plt.subplots(2, 1, sharex=True, figsize=(4.15, 3.35),
                                      layout="constrained")
    angle.plot(t, step["ideal_deg"], "--", color=GRAY, label="Command")
    angle.plot(t, step["output_deg"], color=BLUE, label="Axis")
    angle.axhspan(29.8, 30.2, color=BLUE, alpha=.09)
    angle.legend(loc="lower right")
    angle.set(ylabel="Angle (deg)", ylim=(19, 31))
    effort.plot(t, step["voltage_V"], color=ORANGE)
    effort.set(ylabel="Voltage (V)", xlabel="Time (s)")
    for ax in (angle, effort):
        ax.set(xlim=(0, 10))
        ax.grid(True)
    save(fig, figures, "step")


def draw_tracking(results, figures):
    smooth, noisy, hold = (read(results, name) for name in ("smooth", "noise", "hold"))
    t = smooth["t_s"]
    fig, (angle, error, delta) = plt.subplots(
        3, 1, sharex=True, figsize=(8.0, 4.0), layout="constrained",
        gridspec_kw={"height_ratios": [1.4, 1, .8]},
    )
    angle.plot(t, smooth["ideal_deg"], color=GRAY, ls="--", label="Ideal command")
    angle.plot(t, noisy["output_deg"], color=BLUE, label="Noisy updates")
    angle.plot(t, hold["output_deg"], color=ORANGE, ls=":", label="With gap")
    gap = (t >= .95) & (t < 1.55)
    angle.step(t[gap], hold["applied_deg"][gap], where="post", color=BLACK, lw=1,
               label="Held command near gap")
    angle.legend(loc="upper center", ncol=4, bbox_to_anchor=(.5, 1.25))
    angle.set(ylabel="Angle (deg)")
    error.plot(t, smooth["error_deg"], color=GRAY, label="Clean")
    error.plot(t, hold["error_deg"], color=ORANGE, ls="--", label="With gap")
    error.set(ylabel="Error (deg)")
    error.legend(loc="upper right", ncol=2)
    delta.plot(t, hold["output_deg"] - noisy["output_deg"], color=ORANGE)
    delta.axhline(.1, color=GRAY, lw=.7, ls="--")
    delta.axhline(-.1, color=GRAY, lw=.7, ls="--")
    delta.set(ylabel="Gap effect (deg)", xlabel="Time (s)")
    for ax in (angle, error, delta):
        ax.axvspan(1, 1.5, color=ORANGE, alpha=.12)
        ax.set(xlim=(0, 10), xticks=np.arange(0, 11))
        ax.grid(True)
    save(fig, figures, "tracking")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--figures", type=Path, default=ROOT / "figures")
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    draw_architecture(args.figures)
    draw_frequency(args.results, args.figures)
    draw_step(args.results, args.figures)
    draw_tracking(args.results, args.figures)


if __name__ == "__main__":
    main()
