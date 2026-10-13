"""Shared types: the simulation config and the keys of the state and control dicts."""

from enum import StrEnum
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from src.controllers.controller import Controller

# regions a trip visits, origin first and destination last
type Path = tuple[int, ...]
# (path, region the vehicles are currently in)
type StateKey = tuple[Path, int]
# (from region, to region)
type Boundary = tuple[int, int]


class NetworkType(StrEnum):
    """Supported networks; the value names the network in config.json and in run directories."""

    CORDON = "cordon"  # inner region 0 inside outer region 1
    MULTI_REGION_7 = "multi_region_7"  # centre region 0, ring of regions 1-6


class Config(TypedDict):
    """Simulation settings built in main.py and passed to every component."""

    network: NetworkType
    controller: type["Controller"]
    sim_duration: int
    step_length: int
    total_steps: int
    u_max: float
    u_min: float
    mfd_params: dict[str, float]
