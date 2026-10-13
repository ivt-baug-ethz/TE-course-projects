"""Video of a run: each region's MFD inside its cell, with a dot at the recorded accumulation."""

import math

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.axes import Axes
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch, RegularPolygon
from matplotlib.ticker import MaxNLocator
from tqdm import tqdm

from src.config import NetworkType
from src.result_helpers import Run

FPS = 10  # one frame per record
GREEN, ORANGE, RED = to_rgb("#82B366"), to_rgb("#E8A33D"), to_rgb("#B85450")
# cell colour by accumulation / accumulation at the MFD peak: green up to GREEN_UNTIL,
# blending to orange at the peak, then to red at RED_AT
GREEN_UNTIL = 0.9
RED_AT = 1.5
# MFD axes relative to the point inside the region: x, y, width, height in map units
INSET = (-0.45, -0.45, 1.05, 0.85)


def region_layout(
    network: NetworkType,
) -> tuple[list[Patch], list[tuple[float, float]], float]:
    """Region shapes and a point inside each (indexed by region), and the map's half-width."""
    if network == NetworkType.CORDON:
        # inner region 0 inside the ring of region 1, whose point sits in the ring above 0
        patches: list[Patch] = [Circle((0, 0), 1, zorder=2), Circle((0, 0), 2.35)]
        return patches, [(0.0, 0.0), (0.0, 1.65)], 2.35

    if network == NetworkType.MULTI_REGION_7:
        # flat-topped hexagons of circumradius 1 share an edge at centre distance sqrt(3);
        # 0 in the centre, 1-6 counter-clockwise from the top
        centers = [(0.0, 0.0)] + [
            (
                math.sqrt(3) * math.cos(math.radians(90 + 60 * k)),
                math.sqrt(3) * math.sin(math.radians(90 + 60 * k)),
            )
            for k in range(6)
        ]
        patches = [
            RegularPolygon(xy, 6, radius=1, orientation=math.pi / 6) for xy in centers
        ]
        return patches, centers, 2.6

    raise ValueError(f"Undefined network type: {network}")


def generate_video(run: Run) -> None:
    """Render the run as simulation.mp4 in its run directory."""
    patches, anchors, extent = region_layout(run["network"])
    fig, ax = plt.subplots(figsize=(12, 12))
    fig.subplots_adjust(0, 0, 1, 1)
    extent += 0.15  # margin around the map
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)
    ax.set_aspect("equal")
    ax.axis("off")

    # (dot, accumulation at the MFD peak) per region
    regions = [
        _draw_region(ax, run, r, patch, anchor)
        for r, (patch, anchor) in enumerate(zip(patches, anchors))
    ]
    clock = ax.text(-extent + 0.1, extent - 0.1, "", fontsize=16, va="top")

    # frame k: each region's dot at its recorded state, its cell coloured by the
    # accumulation relative to the MFD peak
    def update(k: int) -> None:
        for r, (dot, peak) in enumerate(regions):
            n = run["n_region"][k][r]
            dot.set_data([n], [run["m_region"][k][r]])
            patches[r].set_facecolor(_congestion_color(n / peak))

        clock.set_text(f"{run['network']}, {run['controller']}\nt = {run['t'][k]} s")

    # crf: constant quality (lower is better, 18-23 is visually near lossless for H.264)
    with tqdm(
        total=len(run["t"]), desc="Rendering simulation.mp4", unit="frame"
    ) as progress:
        FuncAnimation(fig, update, frames=len(run["t"])).save(
            run["run_dir"] / "simulation.mp4",
            writer=FFMpegWriter(fps=FPS, extra_args=["-crf", "20", "-preset", "slow"]),
            dpi=160,
            progress_callback=lambda _i, _n: progress.update(),
        )
    plt.close(fig)


def _draw_region(
    ax: Axes, run: Run, r: int, patch: Patch, anchor: tuple[float, float]
) -> tuple[Line2D, float]:
    patch.set(edgecolor="white", lw=3)
    ax.add_patch(patch)
    n_range = run["mfd_n"]
    m_range = [row[r] for row in run["mfd_m"]]
    # peak and jam accumulation from the sampled MFD, so they follow any MFD shape
    k_peak = m_range.index(max(m_range))
    # first sample from the peak on without trip completion, else the last sample
    k_jam = next(
        (k for k in range(k_peak, len(m_range)) if m_range[k] <= 0), len(m_range) - 1
    )

    # the region's MFD up to its jam accumulation, dashed line at its peak
    x, y = anchor
    inset = ax.inset_axes(
        (x + INSET[0], y + INSET[1], INSET[2], INSET[3]), transform=ax.transData
    )
    inset.patch.set_alpha(0.85)
    inset.plot(n_range[: k_jam + 1], m_range[: k_jam + 1], color="black", lw=1.5)
    inset.axvline(n_range[k_peak], color="grey", lw=1, ls="--")
    inset.set_xlim(0, n_range[k_jam])
    inset.set_ylim(0, 1.15 * m_range[k_peak])
    inset.set_title(f"Region {r}", fontsize=12)
    inset.set_xlabel("n [veh]", fontsize=9)
    inset.set_ylabel("m [veh/s]", fontsize=9)
    inset.tick_params(labelsize=8)
    inset.xaxis.set_major_locator(MaxNLocator(4))
    inset.grid(axis="both", lw=0.2, c="grey")

    # the dot is moved to the recorded state in every frame
    (dot,) = inset.plot([], [], "o", ms=10, color="black", mec="white", mew=2)
    return dot, n_range[k_peak]


def _congestion_color(ratio: float) -> tuple[float, float, float]:
    # ratio: accumulation relative to the accumulation at the MFD peak
    if ratio <= GREEN_UNTIL:
        return GREEN

    if ratio <= 1:
        return _blend(GREEN, ORANGE, (ratio - GREEN_UNTIL) / (1 - GREEN_UNTIL))

    # beyond RED_AT the cell stays red
    return _blend(ORANGE, RED, min((ratio - 1) / (RED_AT - 1), 1))


def _blend(
    a: tuple[float, float, float], b: tuple[float, float, float], w: float
) -> tuple[float, float, float]:
    # linear interpolation of the RGB values, from a at w = 0 to b at w = 1
    return (
        a[0] + w * (b[0] - a[0]),
        a[1] + w * (b[1] - a[1]),
        a[2] + w * (b[2] - a[2]),
    )
