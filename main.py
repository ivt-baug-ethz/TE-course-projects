"""Run the perimeter-control simulation on the configured network and log it to results/."""

from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from pathlib import Path

import matplotlib.pyplot as plt
from tqdm import tqdm

from src.analysis.visualize_inputs import save_input_figures
from src.analysis.visualize_results import analyze_run
from src.analysis.video_generator import generate_video
from src.config import Config, NetworkType
from src.environment.environment import Network
from src.controllers.controller import Controller

# imported so NoControl can be selected as CONTROLLER_TYPE below
from src.controllers.no_control import NoControl
from src.controllers.bang_bang_controller import BangBangController
from src.controllers.p_pd_pid_controller import PController
from src.controllers.nmpc_controller import NMPCController
from src.controllers.empc_controller import EMPCController
from src.environment.demand import Demand
from src.environment.supply import Supply
from src.result_helpers import (
    RESULTS_DIR,
    load_run,
    make_run_dir,
    save_config,
    save_results,
)

# every controller that can be selected with --controller
CONTROLLERS = [
    NoControl,
    BangBangController,
    PController,
    NMPCController,
    EMPCController,
]

# define simulation parameters, the defaults of the command line arguments
NETWORK_TYPE = (
    NetworkType.MULTI_REGION_7
)  # options: NetworkType.CORDON, NetworkType.MULTI_REGION_7
CONTROLLER_TYPE = BangBangController  # options: CONTROLLERS
SIM_DURATION = 7200
STEP_LENGTH = 60
GENERATE_VIDEO = True  # render the simulation video of the run (simulation.mp4)
ANALYZE_RESULTS = True  # store the analysis figures after the simulation


def make_config(
    network: NetworkType,
    controller: type[Controller],
    sim_duration: int = SIM_DURATION,
    step_length: int = STEP_LENGTH,
) -> Config:
    """Simulation config of a run of controller on network."""
    return {
        "network": network,
        "controller": controller,
        "sim_duration": sim_duration,
        "step_length": step_length,
        "total_steps": sim_duration // step_length,  # number of control steps
        "u_max": 0.9,  # upper bound of every boundary control
        "u_min": 0.1,  # lower bound of every boundary control
        "mfd_params": {  # legacy settings of base MFD
            "crit": 8271,  # critical accumulation of the MFD
            "sep": 12900,  # where the MFD changes from a polynomial to a linear function
            "grid": 35670,  # maximal (jam) accumulation of the MFD
            # cubic coefficients below sep, per hour divided by 3600 for veh/s
            "a1": 9.58 / 3600,
            "a2": -8.62e-4 / 3600,
            "a3": 2.28e-8 / 3600,
            # linear branch from sep: value at sep and slope, per hour divided by 3600
            "b1": 29081 / 3600,
            "b2": -1.2772 / 3600,
        },
    }


def main(args: Namespace) -> None:
    """Build supply, demand, network and controller, simulate, store and plot the run."""
    # controller classes by name, as given by --controller
    controllers = {c.__name__: c for c in CONTROLLERS}
    config = make_config(
        args.network, controllers[args.controller], args.sim_duration, args.step_length
    )

    # initialize supply, demand, network and controller
    supply = Supply(config)
    demand = Demand(config)
    env = Network(config, supply, demand)
    controller = config["controller"](config)

    # save the configuration for reference
    run_dir = make_run_dir(args.results_dir, config)
    save_config(run_dir, config, supply, demand)

    # run the simulation: every control step, the controller sets u from the current
    # state and the network advances step_length seconds with u held constant
    for step in tqdm(range(config["total_steps"]), desc="Simulating", unit="step"):
        u = controller.get_control(env)
        env.make_step(step, u=u)

    # store simulation results to file and read them back; everything below works
    # from the stored run
    save_results(run_dir, env, controller)
    print(f"Results stored in {run_dir}")
    run = load_run(run_dir)

    # store the input figures supplied to students: every region's MFD and the demand
    save_input_figures(run, args.show)

    # render the video of the run: every region's MFD with its current state
    if args.video:
        generate_video(run)

    # if enabled, analyze the run and plot the results
    if args.analysis:
        analyze_run(run, args.show)

    if args.show:
        plt.show()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--network", type=NetworkType, choices=list(NetworkType), default=NETWORK_TYPE
    )
    parser.add_argument(
        "--controller",
        choices=[c.__name__ for c in CONTROLLERS],
        default=CONTROLLER_TYPE.__name__,
    )
    parser.add_argument(
        "--sim-duration", type=int, default=SIM_DURATION, help="simulated time [s]"
    )
    parser.add_argument(
        "--step-length", type=int, default=STEP_LENGTH, help="control step [s]"
    )
    parser.add_argument(
        "--video",
        action=BooleanOptionalAction,
        default=GENERATE_VIDEO,
        help="render the simulation video of the run (simulation.mp4)",
    )
    parser.add_argument(
        "--analysis",
        action=BooleanOptionalAction,
        default=ANALYZE_RESULTS,
        help="store all analysis figures of the run",
    )
    parser.add_argument("--show", action="store_true", help="also show the figures")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help="directory the run directory is created in",
    )
    main(parser.parse_args())
