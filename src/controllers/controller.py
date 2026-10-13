"""Perimeter controllers: they set the share u of the transfer flow across each boundary."""

from typing import TYPE_CHECKING

from src.config import Boundary, Config

if TYPE_CHECKING:
    from src.environment.environment import Network


class Controller:
    """Base class: records every control decision."""

    def __init__(self, config: Config) -> None:
        self.network = config["network"]
        # bounds of every boundary control, the share of the transfer flow let through
        self.u_min = config["u_min"]
        self.u_max = config["u_max"]
        # control step [s], during which the returned control is held constant
        self.step_length = config["step_length"]
        self.sim_duration = config["sim_duration"]

        # every control returned by get_control, one per control step
        self.u_record: list[dict[Boundary, float]] = []

    def get_control(self, env: "Network") -> dict[Boundary, float]:
        """Compute, record and return the control dict (from, to) -> u for env."""
        # called by main.py once per control step; subclasses override compute_control only
        u = self.compute_control(env)

        # a copy, so the record stays unchanged if the controller reuses its dict
        self.u_record.append(dict(u))
        return u

    def compute_control(self, env: "Network") -> dict[Boundary, float]:
        """Return the control dict (from, to) -> u; implemented by every controller."""
        raise NotImplementedError("This controller is not defined")
