"""Convert between world and screen coordinates and control zoom."""

from __future__ import annotations

import pygame


class Camera:
    def __init__(self, canvas_rect: pygame.Rect) -> None:
        self.rect = canvas_rect
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.45

    def world_to_screen(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(self.rect.centerx + (x - self.x) * self.zoom),
            int(self.rect.centery + (y - self.y) * self.zoom),
        )

    def screen_to_world(self, px: int, py: int) -> tuple[float, float]:
        return (
            self.x + (px - self.rect.centerx) / self.zoom,
            self.y + (py - self.rect.centery) / self.zoom,
        )

    def zoom_at(self, px: int, py: int, factor: float) -> None:
        before = self.screen_to_world(px, py)
        self.zoom = max(0.18, min(6.0, self.zoom * factor))
        after = self.screen_to_world(px, py)
        self.x += before[0] - after[0]
        self.y += before[1] - after[1]
