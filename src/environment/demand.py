"""Travel demand: paths, initial accumulations and time-varying demand per path."""

import math

from src.config import Config, NetworkType, StateKey


class Demand:
    """Paths of every OD pair with their initial accumulation and demand profile."""

    def __init__(self, config: Config) -> None:

        self.network = config["network"]
        self.sim_duration = config["sim_duration"]
        self.step_length = config["step_length"]

        # initialize demand
        self.n_init: dict[StateKey, float]
        self.q_base: dict[StateKey, float]
        self.normal_veh: dict[StateKey, float]
        self.normal_mu: dict[StateKey, float]
        self.normal_sigma: dict[StateKey, float]
        self.load_demand()

    def load_demand(self) -> None:
        """Set initial accumulations and demand parameters for the configured network."""

        # n_init: initial accumulation [veh] of the non-zero states (path, region);
        # q_base: constant demand [veh/s] of every path, keyed at its origin (path, path[0]);
        # normal_veh, normal_mu, normal_sigma: vehicles [veh], time [s] and standard
        # deviation [s] of each path's Gaussian demand peak, same keys as q_base
        if self.network == NetworkType.CORDON:
            self.n_init = {
                ((0,), 0): 2400.0,
                ((0, 1), 0): 300.0,
                ((1, 0), 1): 1300.0,
                ((1,), 1): 600.0,
            }
            self.q_base = {
                ((0,), 0): 0.24,
                ((0, 1), 0): 0.08,
                ((1, 0), 1): 0.615,
                ((1,), 1): 0.2,
            }
            self.normal_veh = {
                ((0,), 0): 5600.0,
                ((0, 1), 0): 1600.0,
                ((1, 0), 1): 15400.0,
                ((1,), 1): 3000.0,
            }
            self.normal_mu = {
                ((0,), 0): 1800.0,
                ((0, 1), 0): 1800.0,
                ((1, 0), 1): 1800.0,
                ((1,), 1): 1800.0,
            }
            self.normal_sigma = {
                ((0,), 0): 1000.0,
                ((0, 1), 0): 750.0,
                ((1, 0), 1): 1250.0,
                ((1,), 1): 1000.0,
            }

        elif self.network == NetworkType.MULTI_REGION_7:
            # origin 0 has 7 paths (itself and its six neighbours), every ring origin 9:
            # itself, its three neighbours and its three two-hop destinations, with one
            # path per route where two routes lead there
            self.n_init = {
                ((0,), 0): 500.0,
                ((0, 1), 0): 500.0,
                ((0, 2), 0): 500.0,
                ((0, 3), 0): 500.0,
                ((0, 4), 0): 500.0,
                ((0, 5), 0): 500.0,
                ((0, 6), 0): 500.0,
                # ---- origin 1 (9 paths) ----
                ((1,), 1): 800.0,
                ((1, 0), 1): 800.0,
                ((1, 2), 1): 800.0,
                ((1, 6), 1): 800.0,
                ((1, 0, 3), 1): 800.0 / 2,
                ((1, 2, 3), 1): 800.0 / 2,
                ((1, 0, 4), 1): 800.0,
                ((1, 0, 5), 1): 800.0 / 2,
                ((1, 6, 5), 1): 800.0 / 2,
                # ---- origin 2 (9 paths) ----
                ((2,), 2): 700.0,
                ((2, 0), 2): 700.0,
                ((2, 1), 2): 700.0,
                ((2, 3), 2): 700.0,
                ((2, 0, 4), 2): 700.0 / 2,
                ((2, 3, 4), 2): 700.0 / 2,
                ((2, 0, 5), 2): 700.0,
                ((2, 0, 6), 2): 700.0 / 2,
                ((2, 1, 6), 2): 700.0 / 2,
                # ---- origin 3 (9 paths) ----
                ((3,), 3): 600.0,
                ((3, 0), 3): 600.0,
                ((3, 2), 3): 600.0,
                ((3, 4), 3): 600.0,
                ((3, 0, 1), 3): 600.0 / 2,
                ((3, 2, 1), 3): 600.0 / 2,
                ((3, 0, 5), 3): 600.0 / 2,
                ((3, 4, 5), 3): 600.0 / 2,
                ((3, 0, 6), 3): 600.0,
                # ---- origin 4 (9 paths) ----
                ((4,), 4): 500.0,
                ((4, 0), 4): 500.0,
                ((4, 3), 4): 500.0,
                ((4, 5), 4): 500.0,
                ((4, 0, 1), 4): 500.0,
                ((4, 0, 2), 4): 500.0 / 2,
                ((4, 3, 2), 4): 500.0 / 2,
                ((4, 0, 6), 4): 500.0 / 2,
                ((4, 5, 6), 4): 500.0 / 2,
                # ---- origin 5 (9 paths) ----
                ((5,), 5): 400.0,
                ((5, 0), 5): 400.0,
                ((5, 4), 5): 400.0,
                ((5, 6), 5): 400.0,
                ((5, 0, 1), 5): 400.0 / 2,
                ((5, 6, 1), 5): 400.0 / 2,
                ((5, 0, 2), 5): 400.0,
                ((5, 0, 3), 5): 400.0 / 2,
                ((5, 4, 3), 5): 400.0 / 2,
                # ---- origin 6 (9 paths) ----
                ((6,), 6): 300.0,
                ((6, 0), 6): 300.0,
                ((6, 1), 6): 300.0,
                ((6, 5), 6): 300.0,
                ((6, 0, 2), 6): 300.0 / 2,
                ((6, 1, 2), 6): 300.0 / 2,
                ((6, 0, 3), 6): 300.0,
                ((6, 0, 4), 6): 300.0 / 2,
                ((6, 5, 4), 6): 300.0 / 2,
            }
            self.q_base = {
                ((0,), 0): 0.13,
                ((0, 1), 0): 0.13,
                ((0, 2), 0): 0.13,
                ((0, 3), 0): 0.13,
                ((0, 4), 0): 0.13,
                ((0, 5), 0): 0.13,
                ((0, 6), 0): 0.13,
                # ---- origin 1 (9 paths) ----
                ((1,), 1): 0.17,
                ((1, 0), 1): 0.145 / 2,
                ((1, 2), 1): 0.17,
                ((1, 6), 1): 0.17,
                ((1, 0, 3), 1): 0.145 / 2,
                ((1, 2, 3), 1): 0.17 / 2,
                ((1, 0, 4), 1): 0.145,
                ((1, 0, 5), 1): 0.145 / 2,
                ((1, 6, 5), 1): 0.17 / 2,
                # ---- origin 2 (9 paths) ----
                ((2,), 2): 0.14,
                ((2, 0), 2): 0.12 / 2,
                ((2, 1), 2): 0.14,
                ((2, 3), 2): 0.14,
                ((2, 0, 4), 2): 0.12 / 2,
                ((2, 3, 4), 2): 0.14 / 2,
                ((2, 0, 5), 2): 0.12,
                ((2, 0, 6), 2): 0.12 / 2,
                ((2, 1, 6), 2): 0.14 / 2,
                # ---- origin 3 (9 paths) ----
                ((3,), 3): 0.11,
                ((3, 0), 3): 0.095 / 2,
                ((3, 2), 3): 0.11,
                ((3, 4), 3): 0.11,
                ((3, 0, 1), 3): 0.095 / 2,
                ((3, 2, 1), 3): 0.11 / 2,
                ((3, 0, 5), 3): 0.095 / 2,
                ((3, 4, 5), 3): 0.11 / 2,
                ((3, 0, 6), 3): 0.095,
                # ---- origin 4 (9 paths) ----
                ((4,), 4): 0.085,
                ((4, 0), 4): 0.07 / 2,
                ((4, 3), 4): 0.085,
                ((4, 5), 4): 0.085,
                ((4, 0, 1), 4): 0.07,
                ((4, 0, 2), 4): 0.07 / 2,
                ((4, 3, 2), 4): 0.085 / 2,
                ((4, 0, 6), 4): 0.07 / 2,
                ((4, 5, 6), 4): 0.085 / 2,
                # ---- origin 5 (9 paths) ----
                ((5,), 5): 0.055,
                ((5, 0), 5): 0.05 / 2,
                ((5, 4), 5): 0.055,
                ((5, 6), 5): 0.055,
                ((5, 0, 1), 5): 0.05 / 2,
                ((5, 6, 1), 5): 0.055 / 2,
                ((5, 0, 2), 5): 0.05,
                ((5, 0, 3), 5): 0.05 / 2,
                ((5, 4, 3), 5): 0.055 / 2,
                # ---- origin 6 (9 paths) ----
                ((6,), 6): 0.03,
                ((6, 0), 6): 0.025 / 2,
                ((6, 1), 6): 0.03,
                ((6, 5), 6): 0.03,
                ((6, 0, 2), 6): 0.025 / 2,
                ((6, 1, 2), 6): 0.03 / 2,
                ((6, 0, 3), 6): 0.025,
                ((6, 0, 4), 6): 0.025 / 2,
                ((6, 5, 4), 6): 0.03 / 2,
            }
            self.normal_veh = {
                ((0,), 0): 2070.0,
                ((0, 1), 0): 1970.0,
                ((0, 2), 0): 1880.0,
                ((0, 3), 0): 1780.0,
                ((0, 4), 0): 1690.0,
                ((0, 5), 0): 1600.0,
                ((0, 6), 0): 1500.0,
                # ---- origin 1 (9 paths) ----
                ((1,), 1): 2910.0,
                ((1, 0), 1): 2380.0,
                ((1, 2), 1): 2620.0,
                ((1, 6), 1): 2470.0,
                ((1, 0, 3), 1): 1990.0 / 2,
                ((1, 2, 3), 1): 2180.0 / 2,
                ((1, 0, 4), 1): 1750.0,
                ((1, 0, 5), 1): 1620.0 / 2,
                ((1, 6, 5), 1): 1740.0 / 2,
                # ---- origin 2 (9 paths) ----
                ((2,), 2): 2620.0,
                ((2, 0), 2): 2120.0,
                ((2, 1), 2): 2330.0,
                ((2, 3), 2): 2180.0,
                ((2, 0, 4), 2): 1750.0 / 2,
                ((2, 3, 4), 2): 1900.0 / 2,
                ((2, 0, 5), 2): 1500.0,
                ((2, 0, 6), 2): 1370.0 / 2,
                ((2, 1, 6), 2): 1460.0 / 2,
                # ---- origin 3 (9 paths) ----
                ((3,), 3): 2330.0,
                ((3, 0), 3): 1870.0,
                ((3, 2), 3): 2040.0,
                ((3, 4), 3): 1900.0,
                ((3, 0, 1), 3): 1500.0 / 2,
                ((3, 2, 1), 3): 1600.0 / 2,
                ((3, 0, 5), 3): 1250.0 / 2,
                ((3, 4, 5), 3): 1310.0 / 2,
                ((3, 0, 6), 3): 1000.0,
                # ---- origin 4 (9 paths) ----
                ((4,), 4): 2040.0,
                ((4, 0), 4): 1620.0,
                ((4, 3), 4): 1740.0,
                ((4, 5), 4): 1600.0,
                ((4, 0, 1), 4): 1250.0,
                ((4, 0, 2), 4): 1130.0 / 2,
                ((4, 3, 2), 4): 1170.0 / 2,
                ((4, 0, 6), 4): 880.0 / 2,
                ((4, 5, 6), 4): 870.0 / 2,
                # ---- origin 5 (9 paths) ----
                ((5,), 5): 1740.0,
                ((5, 0), 5): 1370.0,
                ((5, 4), 5): 1460.0,
                ((5, 6), 5): 1310.0,
                ((5, 0, 1), 5): 1000.0 / 2,
                ((5, 6, 1), 5): 1020.0 / 2,
                ((5, 0, 2), 5): 740.0,
                ((5, 0, 3), 5): 620.0 / 2,
                ((5, 4, 3), 5): 580.0 / 2,
                # ---- origin 6 (9 paths) ----
                ((6,), 6): 1460.0,
                ((6, 0), 6): 1130.0,
                ((6, 1), 6): 1170.0,
                ((6, 5), 6): 1020.0,
                ((6, 0, 2), 6): 740.0 / 2,
                ((6, 1, 2), 6): 730.0 / 2,
                ((6, 0, 3), 6): 500.0,
                ((6, 0, 4), 6): 370.0 / 2,
                ((6, 5, 4), 6): 290.0 / 2,
            }

            # every peak at the same time with the same spread
            self.normal_mu = {key: 1800.0 for key in self.q_base}
            self.normal_sigma = {key: 1350.0 for key in self.q_base}

        else:
            raise ValueError(f"Undefined environment type: {self.network}")

        # every state of every path (one path per key of q_base), zero unless listed above
        n_init = self.n_init
        self.n_init = {
            (path, loc): n_init.pop((path, loc), 0.0)
            for path, _ in self.q_base
            for loc in path
        }

        # a listed state that is on no path is left over
        if n_init:
            raise ValueError(f"Initial accumulation of unknown states: {list(n_init)}")

    def get_demand(self, t: float) -> dict[StateKey, float]:
        """Demand [veh/s] per path at time t [s]: base rate plus a Gaussian peak."""
        q = {}
        for key, q_base in self.q_base.items():
            veh = self.normal_veh[key]
            mu = self.normal_mu[key]
            sigma = self.normal_sigma[key]

            # normal_veh vehicles spread over time as a Gaussian with mean mu and
            # standard deviation sigma
            peak = (
                veh
                * math.exp(-0.5 * ((t - mu) / sigma) ** 2)
                / (sigma * math.sqrt(2 * math.pi))
            )
            q[key] = q_base + peak
        return q
