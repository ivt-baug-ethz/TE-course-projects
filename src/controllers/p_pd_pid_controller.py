"""FeedbackController: P, PD or PID perimeter control per directed boundary."""

from typing import TYPE_CHECKING

from src.config import Boundary
from src.controllers.controller import Controller

if TYPE_CHECKING:
    from src.environment.environment import Network


class FeedbackController(Controller):
    """Feedback perimeter control per directed boundary."""

    def compute_control(self, env: "Network") -> dict[Boundary, float]:
        """Return the control u of every boundary (from, to) for the current state of env."""

        # ======================================================================
        # >>> to be implemented by you <<<
        # compute the control of every boundary from the current state
        u: dict[Boundary, float] = {key: self.u_max for key in env.supply.u}
        # ======================================================================

        # clip the control to [u_min, u_max]
        for key in u:
            u[key] = min(self.u_max, max(self.u_min, u[key]))

        return u
