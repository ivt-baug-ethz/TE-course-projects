"""The simulated network: accumulation state per (path, region) and its time stepping."""

from src.config import Boundary, Config, StateKey
from src.environment.demand import Demand
from src.environment.supply import Supply


class Network:
    """Accumulation state of the network, advanced in 1 s steps under a boundary control."""

    def __init__(self, config: Config, supply: Supply, demand: Demand) -> None:

        # initialize simulation parameters
        self.network = config["network"]
        self.step_length = config["step_length"]
        self.sim_duration = config["sim_duration"]
        self.total_steps = config["total_steps"]
        self.demand = demand
        self.supply = supply

        # initialize supply
        self.num_regions = supply.num_regions
        self.grid = supply.grid

        # initialize demand
        self.n = dict(demand.n_init)  # copy to avoid changing initialization quantity
        self.q_base = demand.q_base
        self.normal_veh = demand.normal_veh  # it is a normal distribution
        self.normal_mu = demand.normal_mu
        self.normal_sigma = demand.normal_sigma
        self.n_ratio = self.get_region_ratio()

        # initialize the records of the run
        self.n_record = [dict(self.n)]
        self.n_region_record = [self.get_n_region()]
        self.u_record: list[dict[Boundary, float]] = []

        # vehicle hours travelled [veh h], cumulative since t = 0 at every record
        self.vht_record = [0.0]

    def make_step(self, step: int, u: dict[Boundary, float]) -> None:
        """Advance one control step (step_length seconds) with boundary control u."""

        m: dict[StateKey, float] = {}
        m_: dict[StateKey, float] = {}

        # this step's record starts from the total so far and is summed up second by second
        self.vht_record.append(self.vht_record[-1])

        # simulate traffic dynamics for one time step
        for i in range(self.step_length):
            # current time in seconds
            t = step * self.step_length + i

            # current accumulation [veh] of every region
            n_r = self.get_n_region()

            # current trip completion [veh/s] of every region
            m_r = self.supply.get_m_region(n_r)

            # current demand [veh/s] of every state (path, region) at this second
            q = self.demand.get_demand(t)

            # every vehicle in the network at the start of this second spends it there
            self.vht_record[-1] += sum(n_r) / 3600

            for (path, loc), _ in self.n.items():
                # the first step is to compute completion
                m[path, loc] = m_r[loc] * self.n[path, loc] / n_r[loc]

                if loc != path[-1]:
                    # the second step is to check whether the vehicle can go to the next region
                    idx = path.index(loc)
                    if n_r[path[idx + 1]] > self.grid:
                        m[path, loc] = 0.0

                    # perimeter control the percentage of vehicle going across the region
                    m[path, loc] = m[path, loc] * u[loc, path[idx + 1]]
                    m_[path, path[idx + 1]] = m[path, loc]

            # increase a region's directed accumulation by the demand
            for key, value in q.items():
                self.n[key] += value

            # decrease a region's directed accumulation by the completion and transfer
            for key, value in m.items():
                self.n[key] -= value
            for key, value in m_.items():
                self.n[key] += value

        # record the state and control of this step for analysis and visualization
        self.n_record.append(dict(self.n))
        self.n_region_record.append(self.get_n_region())
        self.u_record.append(dict(u))
        self.get_region_ratio()

    def get_n_region(self) -> list[float]:
        """Total accumulation [veh] of every region in the current state."""
        n_r = [0.0] * self.num_regions
        for (_, loc), v in self.n.items():
            n_r[loc] += v
        return n_r

    def get_region_ratio(self) -> list[float]:
        """Update and return each region's accumulation relative to its critical one."""
        n_cur = self.get_n_region()
        self.n_ratio = [n_cur[_] / self.supply.crit[_] for _ in range(self.num_regions)]
        return self.n_ratio
