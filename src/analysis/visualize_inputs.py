"""Input figures supplied to students: the MFD of every region and the demand profiles."""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter
from matplotlib.typing import RcKeyType

from src.analysis.colors import COLORS
from src.config import NetworkType
from src.result_helpers import Run

# shared look of both figures; the legend sits right of the axes, so the figure is wide
STYLE: dict[RcKeyType, object] = {
    "figure.figsize": (8.0, 4.5),
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "axes.grid": True,
    "grid.color": "#E0E0E0",
    "grid.linewidth": 0.6,
    "legend.fontsize": 9,
    "legend.title_fontsize": 9,
    "legend.frameon": False,
    "lines.linewidth": 2,
    "lines.solid_capstyle": "round",
    "lines.dash_capstyle": "round",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}


def save_input_figures(run: Run, show: bool = False) -> None:
    """Save mfd.png and demand.png to the run directory; keep them open only to show them."""
    with plt.rc_context(STYLE):
        for name, plot in (("mfd", plot_mfd), ("demand", plot_demand)):
            plot(run)
            plt.savefig(run["run_dir"] / f"{name}.png")
            if not show:
                plt.close()


def plot_mfd(run: Run) -> None:
    """Plot the MFD of every region."""
    n_range = run["mfd_n"]
    m_max = max(max(row) for row in run["mfd_m"])
    _, ax = plt.subplots()
    for r in range(len(run["crit"])):
        m_range = [row[r] for row in run["mfd_m"]]
        # the MFD is zero beyond the jam accumulation, so the curve ends at its first zero
        end = next(
            (k for k in range(1, len(m_range)) if m_range[k] <= 0), len(m_range) - 1
        )
        ax.plot(
            n_range[: end + 1], m_range[: end + 1], color=COLORS[r], label=f"Region {r}"
        )
        # region index on the falling branch, where the curves are furthest apart
        k_peak = m_range.index(max(m_range))
        k_label = next(
            (j for j in range(k_peak, end + 1) if m_range[j] <= 0.3 * m_max), None
        )
        if k_label is not None:
            _label_curve(ax, n_range[k_label], m_range[k_label], str(r))

    ax.set_xlim(0, n_range[-1])
    ax.set_ylim(0, 1.1 * m_max)
    ax.set_xlabel("Vehicle accumulation [veh]")
    ax.set_ylabel("Trip completion [veh/s]")
    ax.set_title(f"MFD of every region ({run['network']})")
    _finish_plot(ax)


def plot_demand(run: Run) -> None:
    """Plot the demand per OD pair (cordon) or per origin region (multi_region_7)."""
    if run["network"] == NetworkType.CORDON:
        per_od = True
        title = "Demand per OD pair"
        legend_title = "Origin → destination\n(dashed: crosses the cordon)"
    elif run["network"] == NetworkType.MULTI_REGION_7:
        per_od = False
        title = "Demand per origin region"
        legend_title = "Origin region (all destinations)"
    else:
        raise ValueError(f"Undefined network type: {run['network']}")

    curves = _demand_curves(run, per_od)
    _, ax = plt.subplots()
    for label, (o, linestyle, values) in curves.items():
        ax.plot(run["t"], values, color=COLORS[o], linestyle=linestyle, label=label)
        # curve label at the peak, where the profiles are furthest apart
        k_peak = values.index(max(values))
        _label_curve(
            ax, run["t"][k_peak], values[k_peak], label.removeprefix("Region ")
        )

    quartiles = [0, 0.25, 0.5, 0.75, 1]
    ax.set_xlim(0, run["sim_duration"])
    ax.set_ylim(0, 1.1 * max(max(values) for _, _, values in curves.values()))
    ax.set_xticks([x * run["sim_duration"] for x in quartiles])
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Demand [veh/s]")
    ax.set_title(f"{title} ({run['network']})")
    _finish_plot(ax, legend_title)


def _demand_curves(run: Run, per_od: bool) -> dict[str, tuple[int, str, list[float]]]:
    # demand of every path added up per curve: label -> (origin, line style, per record)
    curves: dict[str, tuple[int, str, list[float]]] = {}
    for k, q in enumerate(run["q"]):
        for (path, _), v in q.items():
            o, d = path[0], path[-1]
            label = f"{o} → {d}" if per_od else f"Region {o}"
            # solid: trip stays in its origin region; dashed: trip crosses the cordon
            linestyle = "--" if per_od and o != d else "-"
            curves.setdefault(label, (o, linestyle, [0.0] * len(run["t"])))[2][k] += v
    return curves


def _label_curve(ax: Axes, x: float, y: float, text: str) -> None:
    # white box on the curve, so the label stays legible where it covers the line
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=8,
        color="#333333",
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none"},
        zorder=3,
    )


def _finish_plot(ax: Axes, legend_title: str | None = None) -> None:
    # thousands separated by apostrophes (European style), e.g. 10'000
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", "'"))
    )
    ax.legend(
        title=legend_title,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        alignment="left",
        handlelength=2.5,
    )
    plt.tight_layout()
