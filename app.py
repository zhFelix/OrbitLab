"""Manage application state, events, interface, and rendering."""

from __future__ import annotations

import json
import math
import time
from typing import Optional

import pygame

from config import CONFIG, SLIDER_X_OFFSET, SLIDER_WIDTH, SCENE_LOCALIZED, TEXT, PREFS_PATH, SCENE_PATH, BASE_DIR
from bodies import Body, SCENE_FACTORIES
from physics import Physics
from camera import Camera


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("OrbitLab | 2D orbital sandbox")
        self.screen = pygame.display.set_mode((CONFIG["width"], CONFIG["height"]), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        font_name = next((name for name in (
            "PingFang SC", "Heiti SC", "Hiragino Sans GB", "STHeiti", "stheitimedium", "Microsoft YaHei",
            "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Arial",
        ) if pygame.font.match_font(name)), "Arial")
        self.font = pygame.font.SysFont(font_name, 15)
        self.small_font = pygame.font.SysFont(font_name, 12)
        self.title_font = pygame.font.SysFont(font_name, 21, bold=True)
        self.physics = Physics()
        self.running = True
        self.paused = False
        self.show_trails = True
        self.permanent_trails = False
        self.add_mode = False
        self.follow_selected = False
        self.slider_dragging = False
        self.show_labels = True
        self.scene_name = "Solar System"
        self.scene_names = list(SCENE_FACTORIES)
        self.prediction: list[tuple[float, float]] = []
        self.prediction_timer = 0.0
        self.probe_type = 1
        self.language = "en"
        self.show_stars = True
        self.collisions_enabled = True
        self.settings_open = False
        self.scene_menu_open = False
        self.scene_menu_buttons: dict[str, pygame.Rect] = {}
        self.time_scale = 1.0
        self.sim_time = 0.0
        self.physics_accumulator = 0.0
        self.selected: Optional[Body] = None
        self.dragging_camera = False
        self.camera_drag_start = (0, 0)
        self.camera_origin = (0.0, 0.0)
        self.add_start: Optional[tuple[int, int]] = None
        self.add_current: Optional[tuple[int, int]] = None
        self.toast = ""
        self.toast_timer = 0.0
        self.panel_rect = pygame.Rect(CONFIG["width"] - CONFIG["panel_width"], 0, CONFIG["panel_width"], CONFIG["height"])
        self.canvas_rect = pygame.Rect(0, 0, self.panel_rect.left, CONFIG["height"])
        self.camera = Camera(self.canvas_rect)
        self.starfield = self.make_starfield(self.canvas_rect.width, self.canvas_rect.height)
        self.buttons: dict[str, pygame.Rect] = {}
        self.settings_buttons: dict[str, pygame.Rect] = {}
        self.load_preferences()
        self.energy_initial = self.compute_energy()[2]
        self.layout_panel()
        self.layout_scene_menu()
        self.layout_settings()

    def t(self, key: str) -> str:
        return TEXT[self.language].get(key, key)

    def scene_label(self) -> str:
        return SCENE_LOCALIZED.get(self.scene_name, self.scene_name) if self.language == "zh" else self.scene_name

    def make_starfield(self, width: int, height: int) -> list[tuple[int, int, int]]:
        # Deterministic stars keep screenshots stable and avoid random churn.
        import random
        rng = random.Random(19)
        return [(rng.randrange(0, max(1, width)), rng.randrange(0, max(1, height)), rng.choice([1, 1, 1, 2])) for _ in range(180)]

    def resize(self) -> None:
        width, height = self.screen.get_size()
        self.panel_rect = pygame.Rect(width - CONFIG["panel_width"], 0, CONFIG["panel_width"], height)
        self.canvas_rect = pygame.Rect(0, 0, self.panel_rect.left, height)
        self.camera.rect = self.canvas_rect
        self.starfield = self.make_starfield(self.canvas_rect.width, self.canvas_rect.height)
        self.layout_panel()
        self.layout_settings()
        self.layout_scene_menu()

    def say(self, message: str) -> None:
        self.toast, self.toast_timer = message, 2.4

    def reset(self) -> None:
        self.load_scene_preset(self.scene_name, announce=False)
        self.camera.x = self.camera.y = 0
        self.camera.zoom = 1.45
        self.say("Scene reset")

    def load_scene_preset(self, name: str, announce: bool = True) -> None:
        self.physics.bodies = SCENE_FACTORIES[name]()
        self.scene_name = name
        self.sim_time = 0.0
        self.physics_accumulator = 0.0
        self.selected = None
        self.follow_selected = False
        self.prediction = []
        self.scene_menu_open = False
        self.energy_initial = self.compute_energy()[2]
        if announce:
            self.say(f"Loaded {name}")

    def cycle_scene(self) -> None:
        index = self.scene_names.index(self.scene_name)
        self.load_scene_preset(self.scene_names[(index + 1) % len(self.scene_names)])

    def primary_body(self) -> Optional[Body]:
        return next((body for body in self.physics.bodies if body.primary), None)

    def save_preferences(self, path: str = str(PREFS_PATH)) -> None:
        data = {
            "language": self.language,
            "show_stars": self.show_stars,
            "collisions_enabled": self.collisions_enabled,
            "show_labels": self.show_labels,
            "permanent_trails": self.permanent_trails,
        }
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except OSError:
            pass

    def load_preferences(self, path: str = str(PREFS_PATH)) -> None:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        self.language = data.get("language", self.language) if data.get("language") in TEXT else self.language
        self.show_stars = bool(data.get("show_stars", self.show_stars))
        self.collisions_enabled = bool(data.get("collisions_enabled", self.collisions_enabled))
        self.show_labels = bool(data.get("show_labels", self.show_labels))
        self.permanent_trails = bool(data.get("permanent_trails", self.permanent_trails))

    def update_prediction(self) -> None:
        if not self.selected or len(self.physics.bodies) > 80:
            self.prediction = []
            return
        import copy
        sim = Physics()
        sim.bodies = copy.deepcopy(self.physics.bodies)
        target_index = next((index for index, body in enumerate(self.physics.bodies) if body is self.selected), None)
        if target_index is None or target_index >= len(sim.bodies):
            self.prediction = []
            return
        points: list[tuple[float, float]] = []
        # Longer forecasts make slow, large-orbit bodies readable. Keep a
        # smaller horizon for dense sandboxes so refreshing the cache stays
        # responsive when many bodies are present.
        steps = self.prediction_steps_for_body(self.selected)
        for _ in range(steps):
            sim.step()
            target = sim.bodies[target_index]
            points.append((target.x, target.y))
        self.prediction = points

    def prediction_steps_for_body(self, body: Body) -> int:
        """Choose a visual forecast horizon based on the body's screen size."""
        if len(self.physics.bodies) > 50:
            return 700
        screen_diameter = max(2.0, body.radius * self.camera.zoom * 2.0)
        screen_step = math.hypot(body.vx, body.vy) * CONFIG["dt"] * self.camera.zoom
        if screen_step < 1e-5:
            diameter_steps = CONFIG["prediction_steps"]
        else:
            diameter_steps = math.ceil(screen_diameter / screen_step * CONFIG["prediction_body_diameters"])
        return min(CONFIG["prediction_max_steps"], max(CONFIG["prediction_steps"], diameter_steps))

    def orbital_elements(self, body: Body) -> tuple[float, float, float]:
        primary = self.primary_body()
        if primary is None or body is primary:
            return 0.0, float("inf"), 0.0
        mu = CONFIG["G"] * (primary.mass + body.mass)
        rx, ry = body.x - primary.x, body.y - primary.y
        vx, vy = body.vx - primary.vx, body.vy - primary.vy
        distance = math.hypot(rx, ry)
        if distance < 1e-9 or mu <= 0:
            return 0.0, float("inf"), 0.0
        specific_energy = (vx * vx + vy * vy) / 2 - mu / distance
        angular_momentum = rx * vy - ry * vx
        eccentricity = math.sqrt(max(0.0, 1 + 2 * specific_energy * angular_momentum ** 2 / (mu * mu)))
        semi_major = -mu / (2 * specific_energy) if specific_energy < 0 else float("inf")
        return eccentricity, semi_major, specific_energy

    def should_label(self, body: Body) -> bool:
        if not self.show_labels:
            return False
        if body is self.selected:
            return True
        if body.kind == "probe":
            return False
        return self.camera.zoom > 0.6

    def compute_energy(self) -> tuple[float, float, float]:
        return self.physics.compute_energy()

    def energy_drift(self) -> float:
        total = self.compute_energy()[2]
        if abs(self.energy_initial) < 1e-12:
            return 0.0
        return (total - self.energy_initial) / abs(self.energy_initial) * 100.0

    def update_time_scale_from_mouse(self, position: tuple[int, int]) -> None:
        slider = self.buttons["slider"]
        ratio = max(0.0, min(1.0, (position[0] - (slider.left + 15)) / SLIDER_WIDTH))
        self.time_scale = 10 ** (-1 + ratio * 3)

    def save_scene(self, path: str = str(SCENE_PATH)) -> None:
        data = {
            "G": CONFIG["G"],
            "dt": CONFIG["dt"],
            "softening": CONFIG["softening"],
            "scene_name": self.scene_name,
            "language": self.language,
            "show_stars": self.show_stars,
            "collisions_enabled": self.collisions_enabled,
            "show_labels": self.show_labels,
            "permanent_trails": self.permanent_trails,
            "bodies": [
                {
                    "name": body.name,
                    "kind": body.kind,
                    "mass": body.mass,
                    "radius": body.radius,
                    "color": list(body.color),
                    "x": body.x,
                    "y": body.y,
                    "vx": body.vx,
                    "vy": body.vy,
                    "fixed": body.fixed,
                    "primary": body.primary,
                }
                for body in self.physics.bodies
            ],
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        self.energy_initial = self.compute_energy()[2]
        self.say(f"Saved {path}")

    def load_scene(self, path: str = str(SCENE_PATH)) -> None:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        loaded: list[Body] = []
        for item in data["bodies"]:
            loaded.append(Body(
                name=item["name"], kind=item["kind"], mass=float(item["mass"]),
                radius=float(item["radius"]), color=tuple(item["color"]),
                x=float(item["x"]), y=float(item["y"]), vx=float(item["vx"]),
                vy=float(item["vy"]), fixed=bool(item.get("fixed", False)),
                primary=bool(item.get("primary", False)),
            ))
        if not loaded:
            raise ValueError("scene has no bodies")
        self.physics.bodies = loaded[: CONFIG["max_bodies"]]
        self.scene_name = data.get("scene_name", self.scene_name)
        if self.scene_name not in SCENE_FACTORIES:
            self.scene_name = "Solar System"
        if data.get("language") in TEXT:
            self.language = data["language"]
        self.show_stars = bool(data.get("show_stars", self.show_stars))
        self.collisions_enabled = bool(data.get("collisions_enabled", self.collisions_enabled))
        self.show_labels = bool(data.get("show_labels", self.show_labels))
        self.permanent_trails = bool(data.get("permanent_trails", self.permanent_trails))
        self.physics_accumulator = 0.0
        self.sim_time = 0.0
        self.selected = None
        self.follow_selected = False
        self.energy_initial = self.compute_energy()[2]
        self.say(f"Loaded {path}")

    def delete_selected(self) -> None:
        body = self.selected
        if body is None:
            self.say("Select a body first")
            return
        try:
            index = next(index for index, candidate in enumerate(self.physics.bodies) if candidate is body)
        except StopIteration:
            self.selected = None
            return
        self.physics.bodies.pop(index)
        self.selected = None
        self.follow_selected = False
        self.prediction = []
        self.energy_initial = self.compute_energy()[2]
        if body.primary:
            self.say(f"Removed {body.name} (primary) - no primary body remains")
        else:
            self.say(f"Removed {body.name}")

    def edit_selected(self, key: int) -> None:
        if not self.selected:
            return
        body = self.selected
        changed = False
        if key == pygame.K_LEFTBRACKET:
            body.mass = max(0.001, body.mass / 1.25)
            changed = True
        elif key == pygame.K_RIGHTBRACKET:
            body.mass *= 1.25
            changed = True
        elif key == pygame.K_COMMA:
            body.radius = max(1.0, body.radius - 1.0)
            changed = True
        elif key == pygame.K_PERIOD:
            body.radius += 1.0
            changed = True
        elif key == pygame.K_p:
            body.fixed = not body.fixed
            changed = True
        elif key == pygame.K_x:
            self.delete_selected()
            return
        if changed:
            self.energy_initial = self.compute_energy()[2]
            if key == pygame.K_p:
                self.say(f"{body.name}: {self.t('fixed') if body.fixed else self.t('free')}")
            else:
                self.say("Energy baseline reset")

    def simulate_step(self) -> None:
        self.physics.step()
        merge_events = self.physics.merge_collisions() if self.collisions_enabled else []
        for survivor, removed in merge_events:
            if self.selected is removed:
                self.selected = survivor
            self.say(f"{survivor.name} absorbed {removed.name}")
        self.sim_time += CONFIG["dt"]

    def record_trails(self) -> None:
        if not self.show_trails:
            return
        for body in self.physics.bodies:
            if body.fixed:
                continue
            body.trail.append((body.x, body.y))
            # Normal trails are bounded for performance. Always trails
            # keeps a long, decimated history until the scene is reset.
            if self.permanent_trails and len(body.trail) > CONFIG["permanent_max_trail"]:
                drop = max(1, len(body.trail) // 3)
                del body.trail[:drop]
            elif not self.permanent_trails and len(body.trail) > CONFIG["max_trail"]:
                del body.trail[: len(body.trail) - CONFIG["max_trail"]]

    def step_once(self) -> None:
        if not self.paused:
            self.paused = True
            self.say("Paused for single step")
        self.simulate_step()
        self.record_trails()
        self.prediction_timer = 0.0

    def update(self, elapsed: float) -> None:
        if self.toast_timer > 0:
            self.toast_timer -= elapsed
        advanced = False
        if not self.paused:
            # Keep the physical step fixed; time scale only controls how much
            # simulated time is consumed per rendered frame.
            self.physics_accumulator += elapsed * self.time_scale
            max_substeps = 400
            substeps = 0
            while self.physics_accumulator >= CONFIG["dt"] and substeps < max_substeps:
                self.simulate_step()
                self.physics_accumulator -= CONFIG["dt"]
                substeps += 1
                advanced = True
            if substeps >= max_substeps:
                self.physics_accumulator = 0.0
        if self.show_trails and advanced:
            self.record_trails()
        if self.follow_selected and self.selected:
            self.camera.x += (self.selected.x - self.camera.x) * 0.15
            self.camera.y += (self.selected.y - self.camera.y) * 0.15
        self.prediction_timer -= elapsed
        if self.prediction_timer <= 0.0:
            self.update_prediction()
            self.prediction_timer = 0.25

    def draw_text(self, text: str, pos: tuple[int, int], color=None, font=None) -> None:
        surface = (font or self.font).render(text, True, color or CONFIG["text"])
        self.screen.blit(surface, pos)

    def draw(self) -> None:
        self.screen.fill(CONFIG["background"])
        if self.show_stars:
            for sx, sy, radius in self.starfield:
                if sx < self.canvas_rect.right:
                    pygame.draw.circle(self.screen, (65, 79, 104), (sx, sy), radius)
        self.draw_canvas()
        self.draw_panel()
        if self.toast_timer > 0:
            surface = self.font.render(self.toast, True, CONFIG["text"])
            box = surface.get_rect(center=(self.canvas_rect.centerx, 34))
            pygame.draw.rect(self.screen, (25, 36, 52), box.inflate(28, 15), border_radius=8)
            self.screen.blit(surface, box)
        if self.settings_open:
            self.draw_settings()
        pygame.display.flip()

    def draw_canvas(self) -> None:
        # A subtle center guide and a 100-world-unit scale bar ground the view.
        origin = self.camera.world_to_screen(0, 0)
        if self.canvas_rect.collidepoint(origin):
            pygame.draw.circle(self.screen, (26, 39, 55), origin, 4)
        if self.show_trails:
            for body in self.physics.bodies:
                if len(body.trail) < 2:
                    continue
                self.draw_trail(body)
        for body in self.physics.bodies:
            px, py = self.camera.world_to_screen(body.x, body.y)
            if not self.canvas_rect.inflate(40, 40).collidepoint((px, py)):
                continue
            # Keep the visual radius tied to the same world-space radius used
            # by collision detection. The 2 px floor only helps at far zoom.
            radius = max(2, int(body.radius * self.camera.zoom))
            if body.name == "Saturn":
                pygame.draw.ellipse(self.screen, (190, 173, 122), (px - radius * 2, py - radius // 2, radius * 4, radius), 1)
            pygame.draw.circle(self.screen, body.color, (px, py), radius)
            if body is self.selected:
                pygame.draw.circle(self.screen, CONFIG["accent"], (px, py), radius + 5, 2)
            if self.should_label(body):
                self.draw_text(body.name, (px + radius + 5, py - 8), CONFIG["muted"], self.small_font)
        self.draw_prediction()
        if self.add_start and self.add_current:
            pygame.draw.line(self.screen, CONFIG["accent_2"], self.add_start, self.add_current, 2)
            pygame.draw.circle(self.screen, CONFIG["accent_2"], self.add_start, 5, 1)
            sx, sy = self.camera.screen_to_world(*self.add_start)
            ex, ey = self.camera.screen_to_world(*self.add_current)
            vx, vy = (ex - sx) * 0.10, (ey - sy) * 0.10
            speed = math.hypot(vx, vy)
            distance = math.hypot(sx, sy)
            primary = self.primary_body()
            if primary is not None and distance > 1e-6:
                circular = math.sqrt(CONFIG["G"] * primary.mass / distance)
                ratio = speed / circular if circular else 0.0
                label = f"v {speed:.2f}  ({ratio:.2f}x circular)"
            else:
                label = f"v {speed:.2f}"
            self.draw_text(label, (self.add_current[0] + 12, self.add_current[1] - 8), CONFIG["accent_2"], self.small_font)
        # scale bar
        bar_world = 100
        bar_px = int(bar_world * self.camera.zoom)
        if bar_px > 28:
            x, y = 22, self.canvas_rect.bottom - 28
            pygame.draw.line(self.screen, CONFIG["muted"], (x, y), (x + bar_px, y), 2)
            pygame.draw.line(self.screen, CONFIG["muted"], (x, y - 4), (x, y + 4), 1)
            pygame.draw.line(self.screen, CONFIG["muted"], (x + bar_px, y - 4), (x + bar_px, y + 4), 1)
            self.draw_text("100 units", (x, y - 22), CONFIG["muted"], self.small_font)

    def draw_prediction(self) -> None:
        """Draw the selected body's forecast above bodies and historical trails."""
        if not self.prediction or not self.selected:
            return
        points = [self.camera.world_to_screen(x, y) for x, y in self.prediction]
        body_center = self.camera.world_to_screen(self.selected.x, self.selected.y)
        body_radius = max(2, int(self.selected.radius * self.camera.zoom)) + 2
        # A bright accent and a two-pixel dash make the forecast readable even
        # when the selected body's rendered radius is large.
        prediction_color = CONFIG["accent_2"]
        for index in range(0, len(points) - 1, 3):
            start, end = points[index], points[index + 1]
            if self.segment_intersects_circle(start, end, body_center, body_radius):
                continue
            pygame.draw.line(self.screen, prediction_color, start, end, 2)

    @staticmethod
    def segment_intersects_circle(
        start: tuple[int, int],
        end: tuple[int, int],
        center: tuple[int, int],
        radius: int,
    ) -> bool:
        """Return whether a screen-space line segment enters a circle."""
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_squared = dx * dx + dy * dy
        if length_squared == 0:
            closest = start
        else:
            t = ((center[0] - start[0]) * dx + (center[1] - start[1]) * dy) / length_squared
            t = max(0.0, min(1.0, t))
            closest = (start[0] + t * dx, start[1] + t * dy)
        distance_x = closest[0] - center[0]
        distance_y = closest[1] - center[1]
        return distance_x * distance_x + distance_y * distance_y <= radius * radius

    def draw_trail(self, body: Body) -> None:
        """Draw only contiguous visible runs of a trail.

        Filtering points before calling pygame.draw.lines() makes Pygame join
        two unrelated arcs when a camera pan puts the middle of the trail
        outside the viewport. Keeping a separate run for each visible arc
        avoids those artificial diagonal lines while retaining clipping.
        """
        visible = self.canvas_rect.inflate(80, 80)
        color = tuple(max(20, int(channel * 0.35)) for channel in body.color)
        screen_points = [self.camera.world_to_screen(x, y) for x, y in body.trail]
        run: list[tuple[int, int]] = []
        for index, point in enumerate(screen_points):
            if visible.collidepoint(point):
                if not run and index > 0:
                    run.append(screen_points[index - 1])
                run.append(point)
            elif run:
                run.append(point)
                if len(run) >= 2:
                    pygame.draw.lines(self.screen, color, False, run, 1)
                run = []
        if len(run) >= 2:
            pygame.draw.lines(self.screen, color, False, run, 1)

    def button(self, rect: pygame.Rect, label: str, active=False) -> None:
        color = (30, 75, 75) if active else (26, 36, 52)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, CONFIG["accent"] if active else CONFIG["panel_border"], rect, 1, border_radius=6)
        surface = self.font.render(label, True, CONFIG["text"])
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def layout_panel(self) -> None:
        """Compute panel hitboxes once so drawing and input share one layout."""
        x = self.panel_rect.left + 22
        pause_y = 24 + 70 + 21 + 94
        slider_y = pause_y + 55 + 21 + 3
        view_y = pause_y + 55 + 21 + 54 + 22
        always_y = view_y + 40
        scene_y = always_y + 34
        self.buttons = {
            "pause": pygame.Rect(x, pause_y, 116, 34),
            "reset": pygame.Rect(x + 124, pause_y, 108, 34),
            "slider": pygame.Rect(x + SLIDER_X_OFFSET - 15, slider_y, SLIDER_WIDTH + 30, 26),
            "trails": pygame.Rect(x, view_y, 110, 32),
            "add": pygame.Rect(x + 122, view_y, 110, 32),
            "always": pygame.Rect(x, always_y, 110, 26),
            "follow": pygame.Rect(x + 122, always_y, 110, 26),
            "scene": pygame.Rect(x, scene_y, 150, 26),
            "delete": pygame.Rect(x + 158, scene_y, 74, 26),
            "settings": pygame.Rect(self.panel_rect.right - 86, 22, 64, 28),
        }

    def layout_settings(self) -> None:
        width, height = 410, 330
        left = (self.screen.get_width() - width) // 2
        top = (self.screen.get_height() - height) // 2
        self.settings_buttons = {
            "language": pygame.Rect(left + 28, top + 78, width - 56, 34),
            "stars": pygame.Rect(left + 28, top + 126, width - 56, 34),
            "collisions": pygame.Rect(left + 28, top + 174, width - 56, 34),
            "defaults": pygame.Rect(left + 28, top + 222, 168, 34),
            "close": pygame.Rect(left + 214, top + 222, width - 242, 34),
        }

    def layout_scene_menu(self) -> None:
        scene_rect = self.buttons.get("scene")
        if scene_rect is None:
            self.scene_menu_buttons = {}
            return
        self.scene_menu_buttons = {
            name: pygame.Rect(scene_rect.left, scene_rect.bottom + index * 30, scene_rect.width, 28)
            for index, name in enumerate(self.scene_names)
        }

    def reset_preferences(self) -> None:
        self.language = "en"
        self.show_stars = True
        self.collisions_enabled = True
        self.show_labels = True
        self.permanent_trails = False
        self.save_preferences()
        self.say(self.t("saved"))

    def settings_action(self, position: tuple[int, int]) -> bool:
        if self.settings_buttons["language"].collidepoint(position):
            self.language = "zh" if self.language == "en" else "en"
            self.save_preferences()
            return True
        if self.settings_buttons["stars"].collidepoint(position):
            self.show_stars = not self.show_stars
            self.save_preferences()
            return True
        if self.settings_buttons["collisions"].collidepoint(position):
            self.collisions_enabled = not self.collisions_enabled
            self.save_preferences()
            return True
        if self.settings_buttons["defaults"].collidepoint(position):
            self.reset_preferences()
            return True
        if self.settings_buttons["close"].collidepoint(position):
            self.settings_open = False
            return True
        return False

    def draw_panel(self) -> None:
        pygame.draw.rect(self.screen, CONFIG["panel"], self.panel_rect)
        pygame.draw.line(self.screen, CONFIG["panel_border"], self.panel_rect.topleft, self.panel_rect.bottomleft, 1)
        x = self.panel_rect.left + 22
        y = 24
        self.draw_text("ORBITLAB", (x, y), CONFIG["accent"], self.title_font)
        self.draw_text(self.t("subtitle"), (x, y + 30), CONFIG["muted"], self.small_font)
        self.button(self.buttons["settings"], self.t("settings"))
        y += 70
        self.draw_text(self.t("simulation"), (x, y), CONFIG["muted"], self.small_font)
        y += 21
        self.draw_text(f"{self.t('status')}     {self.t('paused') if self.paused else self.t('running')}", (x, y), CONFIG["text"])
        self.draw_text(f"{self.t('sim_time')}   {self.sim_time:,.2f}", (x, y + 25), CONFIG["text"])
        self.draw_text(f"{self.t('bodies')}     {len(self.physics.bodies):>3}", (x, y + 50), CONFIG["text"])
        y += 94
        self.button(self.buttons["pause"], self.t("resume") if self.paused else self.t("pause"), self.paused)
        self.button(self.buttons["reset"], self.t("reset"))
        y += 55
        self.draw_text(self.t("time_scale"), (x, y), CONFIG["muted"], self.small_font)
        y += 21
        self.draw_text(f"{self.time_scale:.1f}x", (x, y), CONFIG["accent_2"])
        slider = pygame.Rect(x + SLIDER_X_OFFSET, y + 3, SLIDER_WIDTH, 6)
        pygame.draw.rect(self.screen, (44, 58, 77), slider, border_radius=3)
        ratio = (math.log10(self.time_scale) + 1.0) / 3.0
        fill = pygame.Rect(slider.x, slider.y, int(slider.width * max(0.0, min(1.0, ratio))), slider.height)
        pygame.draw.rect(self.screen, CONFIG["accent_2"], fill, border_radius=3)
        y += 54
        self.draw_text(self.t("view"), (x, y), CONFIG["muted"], self.small_font)
        y += 22
        self.button(self.buttons["trails"], self.t("trails"), self.show_trails)
        self.button(self.buttons["add"], self.t("add_body"), self.add_mode)
        y += 40
        self.button(self.buttons["always"], self.t("permanent"), self.permanent_trails)
        self.button(self.buttons["follow"], self.t("follow"), self.follow_selected)
        y += 34
        self.button(self.buttons["scene"], f"{self.t('scene')}: {self.scene_label()}")
        self.button(self.buttons["delete"], self.t("delete"), bool(self.selected))
        y += 36
        self.draw_text(self.t("selected"), (x, y), CONFIG["muted"], self.small_font)
        y += 23
        if self.selected:
            body = self.selected
            distance = math.hypot(body.x, body.y)
            speed = math.hypot(body.vx, body.vy)
            primary = self.primary_body()
            eccentricity, semi_major, specific_energy = self.orbital_elements(body)
            state_label = self.t("fixed") if body.fixed else self.t("free")
            if primary is not None and body is not primary and distance > 1e-9:
                period = 2 * math.pi * math.sqrt(distance ** 3 / (CONFIG["G"] * (primary.mass + body.mass)))
                period_text = f"{period:,.2f}"
            else:
                period_text = "-"
            self.draw_text(body.name, (x, y), body.color)
            self.draw_text(f"Distance {distance:,.2f}  Speed {speed:,.2f}", (x, y + 18), CONFIG["text"], self.small_font)
            self.draw_text(f"Period {period_text}  Mass {body.mass:,.2f}  {state_label}", (x, y + 34), CONFIG["text"], self.small_font)
            if primary is None:
                self.draw_text(self.t("no_primary"), (x, y + 50), CONFIG["muted"], self.small_font)
            elif body is primary:
                self.draw_text(self.t("primary_body"), (x, y + 50), CONFIG["muted"], self.small_font)
            else:
                semi_major_text = f"a {semi_major:,.1f}" if math.isfinite(semi_major) else "a escape"
                self.draw_text(f"e {eccentricity:.3f}  {semi_major_text}", (x, y + 50), CONFIG["text"], self.small_font)
                self.draw_text(f"Specific energy {specific_energy:,.3f}", (x, y + 66), CONFIG["text"], self.small_font)
        else:
            self.draw_text(self.t("click_body"), (x, y), CONFIG["muted"])
            self.draw_text(self.t("enable_add"), (x, y + 23), CONFIG["muted"])
        energy_y = y + 84
        kinetic, potential, total = self.compute_energy()
        drift = self.energy_drift()
        energy_color = CONFIG["danger"] if abs(drift) > 1.0 else CONFIG["text"]
        self.draw_text(self.t("energy"), (x, energy_y), CONFIG["muted"], self.small_font)
        self.draw_text(f"{self.t('kinetic')}   {kinetic:,.1f}", (x, energy_y + 16), CONFIG["text"], self.small_font)
        self.draw_text(f"{self.t('potential')} {potential:,.1f}", (x, energy_y + 32), CONFIG["text"], self.small_font)
        self.draw_text(f"{self.t('total')}     {total:,.1f}", (x, energy_y + 48), CONFIG["text"], self.small_font)
        self.draw_text(f"{self.t('drift')}     {drift:+.3f}%", (x, energy_y + 64), energy_color, self.small_font)
        y = self.panel_rect.bottom - 108
        pygame.draw.line(self.screen, CONFIG["panel_border"], (x, y - 18), (self.panel_rect.right - 22, y - 18), 1)
        self.draw_text(self.t("controls"), (x, y), CONFIG["muted"], self.small_font)
        self.draw_text(self.t("ctrl_pause"), (x, y + 22), CONFIG["muted"], self.small_font)
        self.draw_text(self.t("ctrl_reset"), (x, y + 42), CONFIG["muted"], self.small_font)
        self.draw_text(self.t("ctrl_follow"), (x, y + 62), CONFIG["muted"], self.small_font)
        self.draw_text(self.t("ctrl_body"), (x, y + 82), CONFIG["muted"], self.small_font)
        if self.scene_menu_open:
            for name, rect in self.scene_menu_buttons.items():
                active = name == self.scene_name
                label = SCENE_LOCALIZED.get(name, name) if self.language == "zh" else name
                self.button(rect, label, active)

    def draw_settings(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((3, 7, 14, 185))
        self.screen.blit(overlay, (0, 0))
        language_rect = self.settings_buttons["language"]
        card = pygame.Rect(language_rect.left - 28, language_rect.top - 52, 410, 330)
        pygame.draw.rect(self.screen, (18, 28, 44), card, border_radius=10)
        pygame.draw.rect(self.screen, CONFIG["accent"], card, 1, border_radius=10)
        self.draw_text(self.t("settings_title"), (card.left + 28, card.top + 22), CONFIG["accent"], self.title_font)
        language_name = self.t("chinese") if self.language == "en" else self.t("english")
        self.button(language_rect, f"{self.t('language')}: {language_name}")
        self.button(self.settings_buttons["stars"], f"{self.t('stars')}: {self.t('on') if self.show_stars else self.t('off')}", self.show_stars)
        self.button(self.settings_buttons["collisions"], f"{self.t('collisions')}: {self.t('on') if self.collisions_enabled else self.t('off')}", self.collisions_enabled)
        self.button(self.settings_buttons["defaults"], self.t("defaults"))
        self.button(self.settings_buttons["close"], self.t("close"), True)

    def panel_action(self, position: tuple[int, int]) -> bool:
        if self.scene_menu_open:
            for name, rect in self.scene_menu_buttons.items():
                if rect.collidepoint(position):
                    self.scene_menu_open = False
                    self.load_scene_preset(name)
                    return True
            if not self.buttons["scene"].collidepoint(position):
                self.scene_menu_open = False
                return True
        if self.buttons["pause"].collidepoint(position):
            self.paused = not self.paused
            return True
        if self.buttons["reset"].collidepoint(position):
            self.reset()
            return True
        if self.buttons["trails"].collidepoint(position):
            if self.permanent_trails:
                self.show_trails = True
                self.say("Disable Always trails first")
            else:
                self.show_trails = not self.show_trails
                if not self.show_trails:
                    for body in self.physics.bodies:
                        body.trail.clear()
            return True
        if self.buttons["add"].collidepoint(position):
            self.add_mode = not self.add_mode
            self.add_start = self.add_current = None
            return True
        if self.buttons["always"].collidepoint(position):
            self.permanent_trails = not self.permanent_trails
            self.save_preferences()
            if self.permanent_trails:
                self.show_trails = True
                self.say("Trails will stay visible")
            else:
                self.say("Always trails disabled")
            return True
        if self.buttons["follow"].collidepoint(position):
            self.follow_selected = not self.follow_selected
            if self.follow_selected and not self.selected:
                self.follow_selected = False
                self.say("Select a body first")
            return True
        if self.buttons["scene"].collidepoint(position):
            self.scene_menu_open = not self.scene_menu_open
            return True
        if self.buttons["delete"].collidepoint(position):
            self.delete_selected()
            return True
        if self.buttons["settings"].collidepoint(position):
            self.settings_open = True
            self.layout_settings()
            return True
        if self.buttons["slider"].collidepoint(position):
            self.slider_dragging = True
            self.update_time_scale_from_mouse(position)
            return True
        return False

    def pick_body(self, position: tuple[int, int]) -> Optional[Body]:
        best, best_distance = None, float("inf")
        for body in self.physics.bodies:
            px, py = self.camera.world_to_screen(body.x, body.y)
            distance = math.hypot(position[0] - px, position[1] - py)
            if distance <= max(12, body.radius * self.camera.zoom + 6) and distance < best_distance:
                best, best_distance = body, distance
        return best

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self.resize()
        elif self.settings_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.settings_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.settings_action(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_t:
                if self.permanent_trails:
                    self.say("Always trails is enabled")
                else:
                    self.show_trails = not self.show_trails
            elif event.key == pygame.K_l:
                self.show_labels = not self.show_labels
                self.save_preferences()
            elif event.key == pygame.K_c:
                self.cycle_scene()
            elif event.key == pygame.K_f:
                self.follow_selected = bool(self.selected) and not self.follow_selected
                if not self.selected:
                    self.say("Select a body first")
            elif event.key == pygame.K_n:
                self.step_once()
            elif event.key == pygame.K_F12:
                path = str(BASE_DIR / f"orbitlab_{time.strftime('%Y%m%d_%H%M%S')}.png")
                try:
                    pygame.image.save(self.screen, path)
                    self.say(f"Saved {path}")
                except pygame.error as error:
                    self.say(f"Screenshot failed: {error}")
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                self.probe_type = event.key - pygame.K_0
                self.say(f"Probe type {self.probe_type} selected")
            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                self.time_scale = min(100.0, self.time_scale * 2)
            elif event.key == pygame.K_MINUS:
                self.time_scale = max(0.1, self.time_scale / 2)
            elif event.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_x, pygame.K_p):
                self.edit_selected(event.key)
            elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                try:
                    self.save_scene()
                except OSError as error:
                    self.say(f"Save failed: {error}")
            elif event.key == pygame.K_o and event.mod & pygame.KMOD_CTRL:
                try:
                    self.load_scene()
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                    self.say(f"Load failed: {error}")
            elif event.key == pygame.K_ESCAPE:
                self.selected = None
                self.follow_selected = False
                self.add_start = self.add_current = None
        elif event.type == pygame.MOUSEWHEEL:
            if self.canvas_rect.collidepoint(pygame.mouse.get_pos()):
                self.camera.zoom_at(*pygame.mouse.get_pos(), 1.12 ** event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.panel_rect.collidepoint(event.pos):
                    self.panel_action(event.pos)
                elif self.canvas_rect.collidepoint(event.pos):
                    if self.add_mode:
                        self.add_start = event.pos
                        self.add_current = event.pos
                    else:
                        self.selected = self.pick_body(event.pos)
                        self.dragging_camera = self.selected is None
                        self.camera_drag_start = event.pos
                        self.camera_origin = (self.camera.x, self.camera.y)
            elif event.button == 3:
                self.dragging_camera = True
                self.camera_drag_start = event.pos
                self.camera_origin = (self.camera.x, self.camera.y)
        elif event.type == pygame.MOUSEMOTION:
            if self.slider_dragging:
                self.update_time_scale_from_mouse(event.pos)
            elif self.add_start:
                self.add_current = event.pos
            elif self.dragging_camera:
                dx = (event.pos[0] - self.camera_drag_start[0]) / self.camera.zoom
                dy = (event.pos[1] - self.camera_drag_start[1]) / self.camera.zoom
                self.camera.x = self.camera_origin[0] - dx
                self.camera.y = self.camera_origin[1] - dy
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.slider_dragging = False
                if self.add_start and self.add_current:
                    sx, sy = self.camera.screen_to_world(*self.add_start)
                    ex, ey = self.camera.screen_to_world(*self.add_current)
                    vx, vy = (ex - sx) * 0.10, (ey - sy) * 0.10
                    new_body = self.physics.add_probe(sx, sy, vx, vy, self.probe_type)
                    if new_body:
                        self.selected = new_body
                        self.say("Probe added")
                self.add_start = self.add_current = None
                self.dragging_camera = False
            elif event.button == 3:
                self.dragging_camera = False

    def run(self) -> None:
        while self.running:
            elapsed = min(0.05, self.clock.tick(60) / 1000.0)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(elapsed)
            self.draw()
        self.save_preferences()
        pygame.quit()
