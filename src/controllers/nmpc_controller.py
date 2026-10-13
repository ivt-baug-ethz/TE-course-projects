"""NMPCController: nonlinear MPC on the accumulation model, written with CasADi's Opti stack."""

from typing import TYPE_CHECKING

import casadi as ca

from src.config import Boundary, Config
from src.controllers.controller import Controller
from src.environment.demand import Demand
from src.environment.supply import Supply

if TYPE_CHECKING:
    from src.environment.environment import Network

# prediction horizon [control steps]
HORIZON = 20


class NMPCController(Controller):
    """Nonlinear MPC: every step, optimise the gates over the prediction horizon and apply the
    first control."""

    def mfd(self, n: ca.MX) -> ca.MX:
        """Supply.unit_mfd for a CasADi accumulation n [veh]: trip completion [veh/s] of the
        base MFD, a cubic up to sep, linear down to zero at the jam accumulation grid, zero
        beyond."""
        _, sep, grid, a1, a2, a3, b1, b2 = self.supply.mfd_params.values()
        return ca.if_else(
            n < sep,
            a1 * n + a2 * n**2 + a3 * n**3,
            ca.if_else(n < grid, b1 + b2 * (n - sep), 0),
        )

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.supply = Supply(config)
        self.demand = Demand(config)

        # (path, region) states, origin states with demand and boundaries, in vector order
        self.states = list(self.demand.n_init)
        self.origins = list(self.demand.q_base)
        self.boundaries = list(self.supply.u)
        self.multiplier = ca.DM(self.supply.multiplier)
        self.crit = ca.DM(self.supply.crit)

        # initialize the CasADi Opti stack for nonlinear optimisation over the prediction horizon
        self.opti = ca.Opti()

        # ======================================================================
        # >>> to be implemented by you <<<
        # define the state and input variables over the prediction horizon
        # note: uncomment the initial guess further below once x and u are defined
        self.x = self.opti.variable()
        self.u = self.opti.variable()
        # ======================================================================

        # parameters set at every step: the measured state and the demand forecast per origin
        self.n0 = self.opti.parameter(len(self.states))
        self.q = self.opti.parameter(len(self.origins), HORIZON)

        # ======================================================================
        # >>> to be implemented by you <<<
        # define the cost function and set it to be minimized
        # ======================================================================

        # ======================================================================
        # >>> to be implemented by you <<<
        # constrain the predicted states to the model dynamics from the measured state
        # hint: remember to constrain the first value of the predicted state trajectory as well
        # ======================================================================

        # ======================================================================
        # >>> to be implemented by you <<<
        # add the state and input constraints
        # ======================================================================

        # ======================================================================
        # >>> to be UNCOMMENTED by you <<<
        # warm start all optimization iterations after the first one (-> shorter solve time)
        # self.opti.set_initial(
        #     self.x, ca.repmat(ca.DM(list(self.demand.n_init.values())), 1, HORIZON + 1)
        # )
        # self.opti.set_initial(self.u, self.u_max)
        # ======================================================================

        # ipopt is silent; drop "print_level": 0 to see its iteration table at every step
        self.opti.solver(
            "ipopt",
            {"expand": True, "print_time": False},
            {"print_level": 0, "sb": "yes", "warm_start_init_point": "yes"},
        )

    def compute_control(self, env: "Network") -> dict[Boundary, float]:
        """Return the control u of every boundary (from, to) for the current state of env."""
        t = len(self.u_record) * self.step_length

        # set the measured state as the initial state of the prediction horizon (parameter)
        self.opti.set_value(self.n0, [env.n[key] for key in self.states])

        # demand in the middle of each step, as Network adds it second by second
        self.opti.set_value(
            self.q,
            ca.DM(
                [
                    [
                        self.demand.get_demand(t + (k + 0.5) * self.step_length)[key]
                        for k in range(HORIZON)
                    ]
                    for key in self.origins
                ]
            ),
        )

        # ======================================================================
        # >>> to be UNCOMMENTED by you - no changes needed <<<
        # solve, then warm start the next step from this solution, primal and dual
        # sol = self.opti.solve()
        # self.opti.set_initial(sol.value_variables())
        # self.opti.set_initial(self.opti.lam_g, sol.value(self.opti.lam_g))
        #
        # # apply only the first control of the optimal plan
        # return {
        #     key: float(sol.value(self.u[b, 0])) for b, key in enumerate(self.boundaries)
        # }
        # ======================================================================

        # ======================================================================
        # >>> to be REMOVED by you <<<
        # note: open gates until the block above is uncommented with full implementation
        # deliberate ci failure: a CasADi DM instead of a python float
        return {key: ca.DM(self.u_max) for key in self.boundaries}
        # ======================================================================
