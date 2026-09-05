# TractFigure Studio

Figure-oriented tractography visualization and registration starter for Vanderbilt BrainHack 2026.

The validated runtime is CPython 3.12. The committed `uv.lock` resolves native
wheels for Windows, macOS Apple Silicon, macOS Intel, and Linux.

## Start here

To begin, please follow the instructions in `PREHACKATHON_GUIDE.md` from beginning to end.

The stable coordinate, transform-direction, scene-state, and rendering rules are
summarized in `docs/ARCHITECTURE.md`.

## After installing and activating the environment

```bash
python scripts/fetch_demo_data.py
python scripts/verify_demo_data.py
python scripts/create_demo_recipe.py
python scripts/generate_registration_demo.py
python scripts/preflight.py
```

Launch the validated five-bundle scene:

```bash
python -m tractfigure.gui.app_trame_v1_20260730 \
  --recipe examples/recipes/five_bundle_trame_v1_20260730.json \
  --output-dir outputs \
  --app-port 8080
```

Open `http://localhost:8080` if the browser does not open automatically.

## DSI Studio TinyTrack and glass brain demo

Loads a DSI Studio `.tt.gz` bundle over a translucent MNI152 cortical mesh:

```bash
python -m tractfigure.gui.app_trame_v1_20260730 \
  --recipe examples/recipes/dsi_tinytrack.json \
  --output-dir outputs
```

Data is committed in `demo_data/dsi/` (not fetched by `scripts/fetch_demo_data.py`);
licenses in `DATA_LICENSES.md`. Validation steps: `PREHACKATHON_GUIDE.md`, section 13,
"Validate the DSI Studio TinyTrack and glass-brain demo".
