"""EMPCController: economic MPC on the accumulation model, the NMPC with an economic cost."""

import casadi as ca

from src.config import Config
from src.controllers.nmpc_controller import HORIZON, NMPCController


class EMPCController(NMPCController):
    """Economic MPC: the NMPCController with an economic cost."""

    def __init__(self, config: Config) -> None:
        super().__init__(config)

        # ======================================================================
        # >>> to be implemented by you <<<
        # define the economic cost function and set it to be minimized
        # note: replaces the cost set in NMPCController.__init__; everything else (self.x,
        # self.u, constraints, solver, compute_control, mfd) is inherited unchanged
        cost: ca.MX = ca.MX(0)
        self.opti.minimize(cost)
        # ======================================================================
