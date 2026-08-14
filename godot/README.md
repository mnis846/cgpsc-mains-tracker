# CGPSC Study Garden (Godot 4.3+)

A premium, living garden that grows with your study milestones. Built for the CGPSC Mains tracker — open as a standalone window or export to HTML5 and embed from the dashboard.

## Mechanics

| Achievement | Visual |
|---|---|
| **4 consecutive days** of ≥ daily goal hours | New **permanent tree** planted |
| Extend to **6 consecutive days** | Tree **blooms** (cherry blossoms + falling petals) |
| **>60%** on the matching weekly/block test | **Shiny fruits** on that tree |
| **Streak breaks** | Only the **active/in-progress** sprout wilts; past trees stay beautiful |

Completed 4-day+ milestones remain forever — the grove is a visual record of hard work.

## Requirements

- [Godot 4.3+](https://godotengine.org/download) (4.3 or 4.4 recommended)
- Optional: FastAPI backend (`garden_api.py` in the repo root) for live data

## Quick start

### 1. Open the project

```text
Godot → Import → select  godot/project.godot  → Run (F5)
```

Without a backend, the garden loads `data/mock_garden.json` so it still looks lush.

### 2. Live data from the tracker

From the **repo root** (venv recommended):

```bash
pip install fastapi uvicorn
uvicorn garden_api:app --reload --port 8000
```

Then run the Godot project. `GardenManager` polls:

```text
GET http://127.0.0.1:8000/api/garden/milestones
```

### 3. CLI overrides (Godot)

```bash
godot --path godot -- --api=http://127.0.0.1:8000
godot --path godot -- --mock
godot --path godot -- --poll=5
```

## Expected API JSON

```json
{
  "current_streak_days": 5,
  "milestones": [
    {
      "id": 1,
      "achieved_date": "2026-07-10",
      "has_flowers": true,
      "has_fruits": true,
      "test_score": 72
    }
  ],
  "active_tree": {
    "progress_days": 1,
    "wilted": false
  }
}
```

- **milestones** — permanent trees only (never removed / never wilted)
- **active_tree** — optional mid-streak sprout; `wilted: true` when the streak breaks
- **has_flowers** — cherry blossom canopy + petal particles
- **has_fruits** — shiny red/gold fruit + sparkles

## Project layout

```text
godot/
  project.godot
  scenes/
    GardenScene.tscn      # main scene
    StudyTree.tscn        # reusable tree
  scripts/
    GardenManager.gd      # autoload: HTTP + state
    GardenScene.gd
    StudyTree.gd
    GroundPainter.gd
    DecorLayer.gd
  shaders/
    sky_gradient.gdshader # sky + god rays
    foliage_sway.gdshader
  data/
    mock_garden.json
  export_presets.cfg      # Web + Windows
```

## Architecture

1. **GardenManager** (autoload) fetches JSON on startup and on a poll timer.
2. Diffs milestone ids / flower / fruit flags and emits signals (`tree_planted`, `tree_bloomed`, …).
3. **GardenScene** spawns **StudyTree** instances in an organic spiral layout.
4. Each **StudyTree** has states: `Sapling → Young → Bloomed → Fruited` (+ `Wilted` for the active slot only).
5. Procedural drawing + `GPUParticles2D` + warm `PointLight2D` keep the build lightweight (no large art pack).

## Export

### HTML5 (embeddable)

In Godot: **Project → Export → Web**  
Preset path: `../build/garden-web/index.html`

Serve the folder over HTTP (not `file://`). You can iframe it from Streamlit:

```python
import streamlit.components.v1 as components
components.iframe("http://127.0.0.1:5500/index.html", height=720)
```

CORS is open on `garden_api.py` so the web export can call the API.

### Windows standalone

**Project → Export → Windows Desktop** → `../build/garden-win/StudyGarden.exe`

## Controls

| Input | Action |
|---|---|
| **R** | Refresh garden |
| **Scroll** | Zoom |
| **Middle-drag** | Pan |
| **Hover tree** | Tooltip (date, score, state) |

## Polish notes

- Trees are drawn procedurally (premium mobile-game feel without asset packs).
- Petal particles activate on bloomed / fruited trees.
- God-ray sky shader + fireflies + pollen give depth and warmth.
- Permanent trees always use the healthy palette; only the active sprout yellows when wilted.

## Wiring from Streamlit (optional)

Open the exported window or web build from the Garden tab — keep the existing SVG map for now, or swap the interactive panel for an iframe / “Open Living Garden” button once you export HTML5.
