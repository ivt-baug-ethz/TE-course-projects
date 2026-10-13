"""BangBangController: bang-bang perimeter gating into the more congested region."""

from typing import TYPE_CHECKING

from src.config import Boundary
from src.controllers.controller import Controller

if TYPE_CHECKING:
    from src.environment.environment import Network


class BangBangController(Controller):
    """Bang-bang gating: once a region is above critical, throttle the flow into the more
    congested side of each boundary to u_min."""

    def compute_control(self, env: "Network") -> dict[Boundary, float]:
        u: dict[Boundary, float] = {}
        # every pair of neighbouring regions once; both directions are set together
        pairs = {tuple(sorted(key)) for key in env.supply.u}
        for i, j in pairs:
            # accumulation relative to critical, above 1 means congested
            ratio_i, ratio_j = env.n_ratio[i], env.n_ratio[j]
            if max(ratio_i, ratio_j) <= 1:
                # both regions uncongested: open both gates
                u[i, j] = u[j, i] = self.u_max
            elif ratio_i >= ratio_j:
                # i is more congested: throttle the inflow j -> i, keep the outflow open
                u[j, i], u[i, j] = self.u_min, self.u_max
            else:
                # j is more congested: throttle the inflow i -> j, keep the outflow open
                u[i, j], u[j, i] = self.u_min, self.u_max
        return u
