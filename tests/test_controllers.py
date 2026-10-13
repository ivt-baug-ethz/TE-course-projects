"""Interface checks of the student controllers on every network, run by CI per controller."""

import casadi as ca
import pytest

from main import make_config
from src.config import NetworkType
from src.controllers.bang_bang_controller import BangBangController
from src.controllers.controller import Controller
from src.controllers.empc_controller import EMPCController
from src.controllers.nmpc_controller import NMPCController
from src.controllers.p_pd_pid_controller import PController
from src.environment.demand import Demand
from src.environment.environment import Network
from src.environment.supply import Supply

# the student controllers by test id; CI runs one job per id with pytest -k <id>
CONTROLLERS: dict[str, type[Controller]] = {
    "bang_bang": BangBangController,
    "p_pd_pid": PController,
    "nmpc": NMPCController,
    "empc": EMPCController,
}

# slack on the control bounds, as ipopt may overshoot a bound by its tolerance
TOL = 1e-6


@pytest.mark.parametrize("network", list(NetworkType))
@pytest.mark.parametrize("key", CONTROLLERS)
def test_control_of_every_boundary(key: str, network: NetworkType) -> None:
    """Over a full default run, every control step sets a float u in [u_min, u_max] for
    exactly the boundaries of the network."""
    controller_type = CONTROLLERS[key]
    # main.py calls get_control, which records the control; only compute_control is overridden
    assert issubclass(controller_type, Controller)
    assert controller_type.get_control is Controller.get_control

    config = make_config(network, controller_type)
    env = Network(config, Supply(config), Demand(config))
    controller = controller_type(config)

    for step in range(config["total_steps"]):
        u = controller.get_control(env)
        assert set(u) == set(env.supply.u), f"step {step}: wrong boundaries"
        for boundary, value in u.items():
            # a python float, so that the run can be stored as JSON
            assert isinstance(value, float), f"step {step}, {boundary}: {type(value)}"
            assert (
                config["u_min"] - TOL <= value <= config["u_max"] + TOL
            ), f"step {step}, {boundary}: u = {value}"
        env.make_step(step, u)

    assert len(controller.u_record) == config["total_steps"]


@pytest.mark.parametrize("network", list(NetworkType))
def test_empc_completion_rate(network: NetworkType) -> None:
    """EMPCController builds on the NMPC and its completion rate is a scalar of the state."""
    assert issubclass(EMPCController, NMPCController)
    controller = EMPCController(make_config(network, EMPCController))
    x = ca.MX.sym("x", len(controller.states))
    assert controller.completion_rate(x).shape == (1, 1)
