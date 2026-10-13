"""NoControl: perimeter controller that leaves every boundary at u_max."""

from typing import TYPE_CHECKING

from src.config import Boundary
from src.controllers.controller import Controller

if TYPE_CHECKING:
    from src.environment.environment import Network


class NoControl(Controller):
    """Every boundary at u_max."""

    def compute_control(self, env: "Network") -> dict[Boundary, float]:
        # every boundary at its upper bound u_max, the controller restricts nothing
        return {key: self.u_max for key in env.supply.u}
