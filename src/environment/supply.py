"""Network supply: region topology and the MFD (trip completion) of every region."""

from collections.abc import Sequence

from src.config import Boundary, Config, NetworkType


class Supply:
    """Regions, their neighbours and their MFDs, each a scaled copy of one base MFD."""

    def __init__(self, config: Config) -> None:

        # defines the base MFD; each region is a multiplier of this base MFD
        self.network = config["network"]
        self.mfd_params = config["mfd_params"]

        # initialize network
        self.neighbors: dict[int, list[int]]
        self.multiplier: list[float]
        self.num_regions: int
        self.num_controllers: int
        self.crit: list[float]

        # jam accumulation [veh] of the base MFD
        self.grid: float = self.mfd_params["grid"]
        self.u: dict[Boundary, float]
        self.u_max: float = config["u_max"]
        self.load_supply()

    def load_supply(self) -> None:
        """Set topology, MFD multipliers, critical accumulations and boundary keys."""

        # the inner region is always labeled as 0
        if self.network == NetworkType.CORDON:
            self.neighbors = {
                0: [1],
                1: [0],
            }
            self.multiplier = [0.5, 1]  # the inner MFD is only half of the outer MFD

        elif self.network == NetworkType.MULTI_REGION_7:
            # the centre 0 borders every ring region, each ring region the centre and its
            # two ring neighbours
            self.neighbors = {
                0: [1, 2, 3, 4, 5, 6],
                1: [0, 2, 6],
                2: [0, 1, 3],
                3: [0, 2, 4],
                4: [0, 3, 5],
                5: [0, 4, 6],
                6: [0, 1, 5],
            }
            # the centre has the base MFD, the ring MFDs shrink from region 1 to region 6
            self.multiplier = [
                1.0,
                0.95,
                0.9,
                0.85,
                0.8,
                0.75,
                0.7,
            ]

        else:
            raise ValueError(f"Undefined network type: {self.network}")

        # number of regions and of directed boundaries (two per pair of neighbours)
        self.num_regions = len(self.neighbors)
        self.num_controllers = sum(
            len(neighbors) for neighbors in self.neighbors.values()
        )

        # critical accumulation [veh] of every region, where its MFD peaks
        self.crit = [self.mfd_params["crit"] * m for m in self.multiplier]

        # every directed boundary (from, to) at u_max; controllers take the boundaries
        # from its keys
        self.u = {
            (i, j): self.u_max
            for i, neighbors in self.neighbors.items()
            for j in neighbors
        }

    def unit_mfd(self, n: float) -> float:
        """Base MFD: trip completion [veh/s] at accumulation n [veh]."""
        # unpacked in the key order of mfd_params in main.py
        _crit, sep, grid, a1, a2, a3, b1, b2 = self.mfd_params.values()

        # cubic up to sep, peaking at the critical accumulation
        if n < sep:
            m = a1 * n + a2 * n**2 + a3 * n**3

        # linear from sep, falling to zero at the jam accumulation grid
        elif n < grid:
            m = b1 + b2 * (n - sep)

        # no trip completion at or beyond the jam accumulation
        else:
            m = 0
        return m

    def mfd(self, n: float, mul: float) -> float:
        """Base MFD scaled by the multiplier mul in accumulation and trip completion."""
        return self.unit_mfd(n / mul) * mul

    def get_m_region(self, n: Sequence[float]) -> list[float]:
        """Trip completion [veh/s] of every region for region accumulations n [veh]."""
        return [self.mfd(n[_], self.multiplier[_]) for _ in range(self.num_regions)]
