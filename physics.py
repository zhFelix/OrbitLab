"""Compute body motion, energy, collisions, and probe creation."""

from __future__ import annotations

import math
from typing import Optional

from bodies import Body, make_initial_bodies
from config import CONFIG, PROBE_TYPES


class Physics:
    def __init__(self) -> None:
        self.bodies = make_initial_bodies()

    def accelerations(self) -> list[tuple[float, float]]:
        g = CONFIG["G"]
        eps2 = CONFIG["softening"] ** 2
        result = [[0.0, 0.0] for _ in self.bodies]
        for i, first in enumerate(self.bodies):
            for j in range(i + 1, len(self.bodies)):
                second = self.bodies[j]
                dx, dy = second.x - first.x, second.y - first.y
                dist2 = dx * dx + dy * dy + eps2
                inv_dist3 = 1.0 / (dist2 * math.sqrt(dist2))
                scale = g * inv_dist3
                if not first.fixed:
                    result[i][0] += dx * scale * second.mass
                    result[i][1] += dy * scale * second.mass
                if not second.fixed:
                    result[j][0] -= dx * scale * first.mass
                    result[j][1] -= dy * scale * first.mass
        return [(a[0], a[1]) for a in result]

    def step(self) -> None:
        old_acc = self.accelerations()
        dt = CONFIG["dt"]
        half_dt2 = 0.5 * dt * dt
        for body, (ax, ay) in zip(self.bodies, old_acc):
            body.ax, body.ay = ax, ay
            if not body.fixed:
                body.x += body.vx * dt + ax * half_dt2
                body.y += body.vy * dt + ay * half_dt2
        new_acc = self.accelerations()
        for body, (old, new) in zip(self.bodies, zip(old_acc, new_acc)):
            if not body.fixed:
                body.vx += 0.5 * (old[0] + new[0]) * dt
                body.vy += 0.5 * (old[1] + new[1]) * dt
            body.ax, body.ay = new

    def reset(self) -> None:
        self.bodies = make_initial_bodies()

    def compute_energy(self) -> tuple[float, float, float]:
        kinetic = 0.0
        potential = 0.0
        for body in self.bodies:
            kinetic += 0.5 * body.mass * (body.vx * body.vx + body.vy * body.vy)
        eps2 = CONFIG["softening"] ** 2
        for i, first in enumerate(self.bodies):
            for second in self.bodies[i + 1:]:
                dx, dy = second.x - first.x, second.y - first.y
                distance = math.sqrt(dx * dx + dy * dy + eps2)
                potential -= CONFIG["G"] * first.mass * second.mass / distance
        return kinetic, potential, kinetic + potential

    def merge_collisions(self) -> list[tuple[Body, Body]]:
        """Merge overlapping bodies while conserving mass and linear momentum."""
        merged: list[tuple[Body, Body]] = []
        bodies = self.bodies
        i = 0
        while i < len(bodies):
            j = i + 1
            while j < len(bodies):
                first, second = bodies[i], bodies[j]
                # body.radius is the radius used by the renderer in world
                # units, so contact happens when the two visible circles
                # touch rather than at an arbitrary half-radius threshold.
                if first.fixed and second.fixed:
                    j += 1
                    continue
                if math.hypot(second.x - first.x, second.y - first.y) < first.radius + second.radius:
                    if second.fixed and not first.fixed:
                        bodies[i], bodies[j] = second, first
                        first, second = bodies[i], bodies[j]
                    total_mass = first.mass + second.mass
                    if not first.fixed:
                        first.x = (first.x * first.mass + second.x * second.mass) / total_mass
                        first.y = (first.y * first.mass + second.y * second.mass) / total_mass
                        first.vx = (first.vx * first.mass + second.vx * second.mass) / total_mass
                        first.vy = (first.vy * first.mass + second.vy * second.mass) / total_mass
                    first.mass = total_mass
                    first.radius = math.sqrt(first.radius * first.radius + second.radius * second.radius)
                    merged.append((first, second))
                    del bodies[j]
                    continue
                j += 1
            i += 1
        return merged

    def add_probe(self, x: float, y: float, vx: float, vy: float, probe_type: int = 1) -> Optional[Body]:
        if len(self.bodies) >= CONFIG["max_bodies"]:
            return None
        label, kind, mass, radius, color = PROBE_TYPES.get(probe_type, PROBE_TYPES[1])
        number = 1 + sum(body.kind == kind for body in self.bodies)
        probe = Body(f"{label} {number}", kind, mass, radius, color, x, y, vx, vy)
        self.bodies.append(probe)
        return probe
