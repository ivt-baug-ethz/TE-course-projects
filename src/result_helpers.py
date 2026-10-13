"""Simulation log: every run is stored as JSON in its own timestamped results/ directory."""

import json
from ast import literal_eval
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from src.config import Boundary, Config, NetworkType, StateKey

if TYPE_CHECKING:
    from src.controllers.controller import Controller
    from src.environment.demand import Demand
    from src.environment.environment import Network
    from src.environment.supply import Supply

RESULTS_DIR = Path("results")


class Run(TypedDict):
    """A stored run as read back by load_run: its settings and its recorded series."""

    run_dir: Path
    network: NetworkType
    controller: str
    sim_duration: int
    step_length: int
    u_min: float
    u_max: float
    crit: list[float]
    t: list[int]
    n: list[dict[StateKey, float]]
    n_region: list[list[float]]
    n_ratio: list[list[float]]
    m_region: list[list[float]]
    q: list[dict[StateKey, float]]
    u: list[dict[Boundary, float]]
    mfd_n: list[int]
    mfd_m: list[list[float]]


def make_run_dir(results_dir: Path, config: Config) -> Path:
    """Create <results_dir>/<network>_<controller>_<timestamp>/ and return its path."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{config['network']}_{config['controller'].__name__}_{stamp}"
    run_dir = results_dir / name
    # fails instead of overwriting when the same setup is started twice within a second
    run_dir.mkdir(parents=True)
    return run_dir


def save_config(
    run_dir: Path, config: Config, supply: "Supply", demand: "Demand"
) -> None:
    """Write config.json: the config plus the loaded supply and demand inputs."""
    # dict keys that are tuples are stored as their str(), read back with ast.literal_eval
    log = {
        **config,
        "controller": config["controller"].__name__,
        "supply": {
            "neighbors": supply.neighbors,
            "multiplier": supply.multiplier,
            "crit": supply.crit,
        },
        "demand": {
            name: {str(key): v for key, v in values.items()}
            for name, values in (
                ("n_init", demand.n_init),
                ("q_base", demand.q_base),
                ("normal_veh", demand.normal_veh),
                ("normal_mu", demand.normal_mu),
                ("normal_sigma", demand.normal_sigma),
            )
        },
    }
    (run_dir / "config.json").write_text(json.dumps(log, indent=2))


def save_results(run_dir: Path, env: "Network", controller: "Controller") -> None:
    """Write results.json: the recorded state and control plus derived region values."""
    supply, demand = env.supply, env.demand
    t = [k * env.step_length for k in range(len(env.n_record))]

    # n_ratio and m_region are derived from the recorded region accumulations with the
    # functions the simulation uses
    n_region = env.n_region_record

    # accumulations [veh] at which the MFDs are sampled, up to the base jam accumulation
    n_mfd = list(range(0, int(supply.mfd_params["grid"]) + 1, 100))
    m_mfd = [supply.get_m_region([n] * supply.num_regions) for n in n_mfd]
    log = {
        # time [s] of every record; u[k] is held from t[k] to t[k + 1]
        "t": t,
        # accumulation [veh] of every state and every region
        "n": [{str(key): v for key, v in n.items()} for n in env.n_record],
        "n_region": n_region,
        # accumulation relative to the critical one per region
        "n_ratio": [
            [n_r[r] / supply.crit[r] for r in range(supply.num_regions)]
            for n_r in n_region
        ],
        # trip completion [veh/s] per region and demand [veh/s] per path
        "m_region": [supply.get_m_region(n_r) for n_r in n_region],
        "q": [{str(key): v for key, v in demand.get_demand(t_k).items()} for t_k in t],
        # one control per step, so one entry fewer than the records
        "u": [{str(key): v for key, v in u.items()} for u in controller.u_record],
        # every region's MFD sampled every 100 veh, one row per accumulation
        "mfd": {"n": n_mfd, "m": m_mfd},
    }
    (run_dir / "results.json").write_text(json.dumps(log))


def load_run(run_dir: Path) -> Run:
    """Read config.json and results.json of a stored run."""
    config = json.loads((run_dir / "config.json").read_text())
    results = json.loads((run_dir / "results.json").read_text())

    # settings from config.json, series from results.json; tuple keys stored as str()
    # are read back as tuples
    return {
        "run_dir": run_dir,
        "network": NetworkType(config["network"]),
        "controller": config["controller"],
        "sim_duration": config["sim_duration"],
        "step_length": config["step_length"],
        "u_min": config["u_min"],
        "u_max": config["u_max"],
        "crit": config["supply"]["crit"],
        "t": results["t"],
        "n": [{literal_eval(key): v for key, v in n.items()} for n in results["n"]],
        "n_region": results["n_region"],
        "n_ratio": results["n_ratio"],
        "m_region": results["m_region"],
        "q": [{literal_eval(key): v for key, v in q.items()} for q in results["q"]],
        "u": [{literal_eval(key): v for key, v in u.items()} for u in results["u"]],
        "mfd_n": results["mfd"]["n"],
        "mfd_m": results["mfd"]["m"],
    }
