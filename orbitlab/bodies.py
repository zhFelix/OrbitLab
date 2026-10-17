"""Define celestial bodies and the preset scene factories."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from config import CONFIG


@dataclass
class Body:
    name: str
    kind: str
    mass: float
    radius: float
    color: tuple[int, int, int]
    x: float
    y: float
    vx: float
    vy: float
    fixed: bool = False
    trail: list[tuple[float, float]] = field(default_factory=list)
    ax: float = 0.0
    ay: float = 0.0
    primary: bool = False


def make_initial_bodies() -> list[Body]:
    # Distances and masses are intentionally stylized, but velocities are
    # selected from the circular-orbit approximation for stable visuals.
    specs = [
        ("Mercury", 35, 0.18, 3, (177, 181, 190)),
        ("Venus", 52, 0.55, 5, (224, 180, 111)),
        ("Earth", 70, 0.75, 5, (76, 157, 235)),
        ("Mars", 95, 0.32, 4, (205, 100, 83)),
        ("Jupiter", 150, 5.0, 10, (214, 166, 118)),
        ("Saturn", 205, 3.4, 9, (222, 197, 139)),
        ("Uranus", 255, 1.6, 7, (123, 204, 214)),
        ("Neptune", 300, 1.8, 7, (73, 117, 220)),
    ]
    sun_mass = 10000.0
    bodies = [Body("Sun", "star", sun_mass, 16, (250, 193, 70), 0, 0, 0, 0, True, primary=True)]
    for name, radius, mass, draw_radius, color in specs:
        speed = math.sqrt(CONFIG["G"] * sun_mass / radius)
        bodies.append(Body(name, "planet", mass, draw_radius, color, radius, 0, 0, speed))
    return bodies


def make_binary_bodies() -> list[Body]:
    star_mass = 4500.0
    separation = 70.0
    speed = math.sqrt(CONFIG["G"] * star_mass / (2.0 * separation))
    return [
        Body("Star A", "star", star_mass, 13, (255, 187, 70), -separation / 2, 0, 0, -speed),
        Body("Star B", "star", star_mass, 13, (235, 115, 76), separation / 2, 0, 0, speed),
        Body("Planet", "planet", 1.0, 5, (87, 174, 225), 0, 150, -math.sqrt(CONFIG["G"] * star_mass * 2 / 150), 0),
    ]


def make_earth_moon_bodies() -> list[Body]:
    earth_mass = 10000.0
    moon_distance = 38.0
    moon_speed = math.sqrt(CONFIG["G"] * earth_mass / moon_distance)
    return [
        Body("Earth", "planet", earth_mass, 15, (75, 157, 235), 0, 0, 0, 0, True, primary=True),
        Body("Moon", "moon", 1.0, 5, (190, 196, 207), moon_distance, 0, 0, moon_speed),
    ]


def make_figure8_bodies() -> list[Body]:
    # A scaled, symmetric three-body teaching scene based on the classic
    # figure-eight initial condition.
    scale = 85.0
    mass = 1200.0
    velocity_scale = math.sqrt(mass / scale)
    positions = [(-0.97000436, 0.24308753), (0.97000436, -0.24308753), (0.0, 0.0)]
    velocities = [(0.466203685, 0.43236573), (0.466203685, 0.43236573), (-0.93240737, -0.86473146)]
    colors = [(244, 117, 98), (104, 184, 226), (224, 190, 83)]
    return [Body(f"Body {index + 1}", "planet", mass, 8, colors[index], px * scale, py * scale, vx * velocity_scale, vy * velocity_scale) for index, ((px, py), (vx, vy)) in enumerate(zip(positions, velocities))]


SCENE_FACTORIES = {
    "Solar System": make_initial_bodies,
    "Binary Star": make_binary_bodies,
    "Earth-Moon": make_earth_moon_bodies,
    "Figure-8": make_figure8_bodies,
}
