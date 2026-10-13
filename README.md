# Numerical Simulation of Perimeter Control in Multi-Region Urban Networks

This repository contains a **numerical simulation** of **perimeter control** in urban road
networks that are divided into regions. Every region is described by its **macroscopic
fundamental diagram (MFD)**, and the simulation integrates the vehicle accumulation of every
region in time steps of one second. You implement perimeter controllers, simulate them on two
networks and compare them based on the stored simulation data.

The MFD of a region relates its accumulation, the number of vehicles in the region, to its trip
completion rate. Beyond a critical accumulation, additional vehicles reduce the number of
completed trips. A perimeter controller sets, for every directed boundary $(i, j)$, the share
$u_{ij} \in [u_{\min}, u_{\max}]$ of the transfer flow that may cross from region $i$ into
region $j$ (also known as "gates"). In this way, it keeps regions out of congestion, while
vehicles that are held back wait in the neighbouring region.

## Contents

- [Networks](#networks)
- [Controllers](#controllers)
- [Setup](#setup)
- [Running a simulation](#running-a-simulation)
- [Results](#results)
- [Visualizations](#visualizations)
- [Implementing a controller](#implementing-a-controller)
- [Interface checks](#interface-checks)
- [Repository structure](#repository-structure)
- [License](#license)

## Networks

| Network          | Regions                                                | Directed boundaries |
| ---------------- | ------------------------------------------------------ | ------------------: |
| `cordon`         | inner region 0 enclosed by outer region 1              |                   2 |
| `multi_region_7` | centre region 0 surrounded by a ring of regions 1 to 6 |                  24 |

The MFD of every region is a scaled copy of one base MFD. In `cordon`, the inner MFD is half
the size of the outer one. In `multi_region_7`, the centre has the largest MFD, and the ring
MFDs become smaller from region 1 to region 6. The demand of every path consists of a constant
base rate and a Gaussian peak.

## Controllers

All controllers are located in `src/controllers/` and inherit a base structure from the `Controller`.

| Controller           | File                      | Role                                                   |
| -------------------- | ------------------------- | ------------------------------------------------------ |
| `NoControl`          | `no_control.py`           | provided baseline that keeps every boundary at `u_max` |
| `BangBangController` | `bang_bang_controller.py` | provided example of a complete controller              |
| `FeedbackController` | `p_pd_pid_controller.py`  | stub for a P, PD or PID feedback controller            |
| `NMPCController`     | `nmpc_controller.py`      | stub for a nonlinear MPC with CasADi Opti and IPOPT    |
| `EMPCController`     | `empc_controller.py`      | bonus stub for an economic MPC built on the NMPC       |

The parts you implement are marked with `>>> to be implemented by you <<<`. Every stub runs as
shipped, so you can simulate it before you fill it in.

## Setup

The simulation requires a modern version of Python (the project was designed and tested with Python 3.13),
as well as git and [ffmpeg](https://ffmpeg.org/) for the simulation video. You can skip ffmpeg if you
always run with `--no-video`.

```sh
# on macOS or Linux
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```powershell
# on Windows (PowerShell)
py -3.13 -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install ffmpeg with `brew install ffmpeg` on macOS, `sudo apt install ffmpeg` on Debian or
Ubuntu, or `winget install ffmpeg` on Windows, and check the installation with
`ffmpeg -version`.

Run every command from the repository root with the virtual environment activated.

## Running a simulation

```sh
python main.py                                          # defaults set at the top of main.py
python main.py --network cordon --controller NoControl  # choose network and controller
python main.py --controller FeedbackController --no-video      # skip the video for quick iterations
python main.py --help                                   # list all options
```

| Option                         | Default              | Meaning                                             |
| ------------------------------ | -------------------- | --------------------------------------------------- |
| `--network`                    | `multi_region_7`     | `cordon` or `multi_region_7`                        |
| `--controller`                 | `BangBangController` | any controller from the table above                 |
| `--sim-duration`               | `7200`               | simulated time [s]                                  |
| `--step-length`                | `60`                 | control step [s], during which `u` is held constant |
| `--video` / `--no-video`       | on                   | render `simulation.mp4` (requires ffmpeg)           |
| `--analysis` / `--no-analysis` | on                   | call your `analyze_run` after the simulation        |
| `--show`                       | off                  | also open the figures in a window                   |
| `--results-dir`                | `results`            | directory in which the run directory is created     |

To change the defaults, edit the constants at the top of `main.py`. The control bounds
(`u_min = 0.1`, `u_max = 0.9`) and the MFD parameters are set in `make_config` in `main.py`.

## Results

Every run is stored in its own directory, named `<network>_<controller>_<YYYYmmdd-HHMMSS>`.

```text
results/
└── cordon_NoControl_20261013-115550/
    ├── config.json      # run settings, topology, MFD and demand parameters
    ├── results.json     # recorded time series of the run
    ├── mfd.png          # MFD of every region
    ├── demand.png       # demand profiles
    └── simulation.mp4   # animated region states (only with --video)
```

`results.json` contains one record for the initial state and one for the end of every control
step, at the times `t = 0, step_length, ..., sim_duration`.

| Key        | Content                                                                                                                  | Unit       |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `t`        | time of every record                                                                                                     | s          |
| `n`        | accumulation of every state `(path, region)`                                                                             | veh        |
| `n_region` | accumulation of every region                                                                                             | veh        |
| `n_ratio`  | accumulation of every region relative to its critical accumulation                                                       | -          |
| `m_region` | trip completion of every region, given by its MFD                                                                        | veh/s      |
| `q`        | demand of every path                                                                                                     | veh/s      |
| `u`        | control of every boundary `(from, to)`, with one entry fewer than the records, as `u[k]` is held from `t[k]` to `t[k+1]` | -          |
| `mfd`      | MFD of every region, sampled every 100 veh (`n`, with one row of `m` per sample)                                         | veh, veh/s |

A path is the tuple of regions that a trip visits, with the origin first and the destination
last. Since JSON keys cannot be tuples, tuple keys are stored as strings.

```json
"n": [{"((0,), 0)": 2400.0, "((0, 1), 0)": 300.0, "((0, 1), 1)": 0.0, "...": "..."}, "..."],
"u": [{"(0, 1)": 0.9, "(1, 0)": 0.9}, "..."]
```

For example, `((0, 1), 0)` counts the vehicles on the path from region 0 to region 1 that are
currently in region 0. The function `load_run` reads a run back and restores the tuple keys.

```python
from pathlib import Path
from src.result_helpers import load_run

run = load_run(Path("results/cordon_NoControl_20261013-115550"))
run["n_region"][-1]  # accumulation of every region at the end of the run
run["u"][0][(1, 0)]  # first control of the boundary from region 1 into region 0
```

## Visualizations

Every run stores the following figures and the video in its directory. They support
exploration and debugging, whereas the figures in your report should be produced by your own
analysis of the stored data.

- `mfd.png` shows the MFD of every region, that is, the trip completion over the accumulation.
- `demand.png` shows the demand over time, per origin-destination pair for `cordon` (dashed
  lines cross the cordon) and per origin region for `multi_region_7`.
- `simulation.mp4` shows a map of the network with the MFD of every region drawn inside it. A
  dot follows the current state of each region, and the region turns from green through orange
  to red as its accumulation passes the peak of its MFD.

Your own figures belong in `analyze_run` in `src/analysis/visualize_results.py`, which
`main.py` calls after every run unless `--no-analysis` is set. Save the figures to
`run["run_dir"]`.

## Implementing a controller

A controller overrides a single method. `compute_control` receives the current network state
`env` and returns a dict that maps every directed boundary `(i, j)` to a Python `float` in
`[self.u_min, self.u_max]`. `main.py` calls it once per control step through `get_control`,
which records every decision. Do not override `get_control`, and keep the class names and
method signatures of the stubs unchanged.

```python
def compute_control(self, env: "Network") -> dict[Boundary, float]:
    # env.supply.u has every directed boundary as its keys
    # env.n_ratio[i] is the accumulation of region i relative to its critical accumulation
    return {(i, j): self.u_max for i, j in env.supply.u}
```

`BangBangController` is a complete example that acts on the current state of the regions.

## Interface checks

`tests/test_controllers.py` runs every implemented controller through a full simulation with the
default settings on both networks. At every control step, it checks that each boundary receives
exactly one `float` within the control bounds. GitHub Actions
(`.github/workflows/controllers.yml`) runs these checks on every push, with one job per
controller. Your submission can only be evaluated if all checks pass.

```sh
python -m pytest tests              # all controllers
python -m pytest tests -k p_pd_pid  # one controller (bang_bang, p_pd_pid, nmpc or empc)
```

## Repository structure

```text
├── main.py                       # configures, simulates, stores and plots a run
├── requirements.txt
├── src/
│   ├── config.py                 # Config, NetworkType, state and boundary key types
│   ├── result_helpers.py         # storing and loading runs
│   ├── environment/
│   │   ├── supply.py             # topology and MFD of every region
│   │   ├── demand.py             # paths, initial accumulations, demand profiles
│   │   └── environment.py        # Network with the accumulation state and time stepping
│   ├── controllers/              # Controller base class and all controllers
│   └── analysis/
│       ├── visualize_inputs.py   # mfd.png and demand.png
│       ├── video_generator.py    # simulation.mp4
│       └── visualize_results.py  # analyze_run for your own analysis
├── tests/test_controllers.py     # interface checks
└── .github/workflows/            # runs the interface checks on every push
```

## License

[GNU Affero General Public License v3.0](LICENSE)
