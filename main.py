"""Launch the OrbitLab application.

OrbitLab - a small 2D solar-system sandbox built with Pygame.

Run with:
    python main.py

Controls:
    Space       pause / resume
    R           reset the scene
    T           toggle trails
    +/-         change simulation speed
    Mouse wheel zooms around the cursor; drag the canvas to pan.
    Click a body to inspect it. Enable Add body, then click-drag on empty
    space to create a probe with a velocity matching the drag direction.

"""

from __future__ import annotations

import sys

import pygame

from app import App


def main() -> None:
    try:
        App().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
