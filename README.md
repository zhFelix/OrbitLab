# OrbitLab (Python)

2D solar-system orbital sandbox implemented with Python and Pygame. It uses a softened Newtonian N-body model and Velocity Verlet integration.

## Run

```bash
python -m pip install -r requirements.txt
cd orbitlab
python main.py
```

Preferences, scene files, and screenshots default to the `orbitlab/` directory
beside `config.py`, regardless of the current working directory. You can also
launch the app with `python /absolute/path/to/orbitlab/main.py`.

The code is split into six modules: `main.py` launches the app, `config.py`
defines shared configuration, `bodies.py` defines bodies and scene presets,
`physics.py` handles simulation, `camera.py` handles coordinate transforms,
and `app.py` contains the complete application interface and event loop.

## Controls

- `Space`: pause / resume
- `R`: reset
- `T`: toggle trails
- `Always trails`: keep the complete trail history visible until the scene is reset
- `F`: follow the selected body with the camera
- `L`: toggle labels; `C` or the Scene button cycles presets
- `N`: pause if running, then advance one physics step
- `F12`: save a screenshot of the current window
- `+` / `-`: change time scale (`0.1x` to `100x`)
- `[` / `]`: decrease / increase selected mass
- `,` / `.`: decrease / increase selected radius
- `P`: toggle selected body fixed state
- `X`: delete selected body
- `Ctrl+S` / `Ctrl+O`: save / load `scene.json`
- `1`-`5`: select body type before creating a body (`5` = Star)
- Mouse wheel: zoom around cursor
- Drag the canvas: pan
- Click a body: inspect its state
- Toggle `Add body`, then click-drag on empty canvas to create a probe and give it an initial velocity

Open `Settings` in the upper-right panel to switch between English and
Chinese, toggle the starfield, enable or disable collision merging, or restore
default preferences.

The `Delete` button beside the scene selector removes the selected body. The
Sun is protected from deletion.

The panel also reports kinetic energy, potential energy, total energy, and
relative energy drift. Bodies merge on contact while conserving mass and
linear momentum.

Available presets are Solar System, Binary Star, Earth-Moon, and Figure-8;
clicking the Scene button opens a direct selection menu.
Selecting a body also shows a cached dashed trajectory prediction and basic
two-body orbital elements. Prediction is skipped when there are more than
80 bodies and resumes on the next prediction refresh at 80 or fewer.
