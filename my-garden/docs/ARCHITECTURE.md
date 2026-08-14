# Architecture — Discipline World (standalone)

## Independence rule

```text
CGPSC Mains Tracker (repo root)     my-garden (this folder)
───────────────────────────────     ─────────────────────────
  app.py, database.py                 own study log
  garden_api.py, godot/               own progression (4 / 6 / fruits)
  Streamlit garden                    own world state
         │                                   │
         │         NO LIVE DATA FEED         │
         └───────────────────────────────────┘
```

**Do not** pipe mains-tracker hours, streaks, or test tables into Discipline World.

The world only grows from study recorded **inside my-garden**.

---

## Stack

```text
┌──────────────────────────────────────┐
│  my-garden Study Log                 │
│  • daily hours (timer or manual)     │
│  • optional test scores              │
│  • local JSON / SQLite in my-garden  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Progression Engine                  │
│  • 4 continuous ≥6h days → +1 tree   │
│  • 6 continuous ≥6h days → blossom   │
│  • good marks → fruits               │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  World State                         │
│  data/world_state.json (or Unity DB) │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Unity 6 + URP                       │
│  render trees, blossoms, fruits      │
│  walk, plant, inspect                │
└──────────────────────────────────────┘
```

Progression math can live in:

- **C# inside Unity** (simplest if the game owns the timer), or
- a tiny **local script** under `my-garden/tools` that writes JSON Unity loads.

Either way: **no dependency on repo-root `database.py` / `garden_api.py`.**

---

## Core loop

1. Study ≥ 6 hours (logged in my-garden).
2. Repeat **4 continuous days** → earn a tree (seed).
3. Continue to **6 continuous days** → cherry blossoms.
4. Log a strong test score → fruits on the tree.
5. Open the world: walk the forest that only you built.

---

## What the game stores locally

| Store | Examples |
|-------|----------|
| Study log | Date → hours |
| Test log | Date, score %, optional note |
| World | Planted trees, species, positions, blossom/fruit flags |
| Player | Logout position, cinematics already played |

---

## Unity modules (minimal first)

| Module | Job |
|--------|-----|
| `StudyLog` | Record daily hours / scores |
| `ProgressionEngine` | Apply 4-day / 6-day / fruit rules |
| `TreeRegistry` | Permanent trees + inspect |
| `SeedPlanting` | Optional: walk and plant earned seed |
| `WorldRenderer` | Show blossoms & fruits |
| `PlayerPersistence` | Last position |

---

## Explicitly out of scope for data

- `GET /api/garden/milestones` from mains tracker
- Reading `cgpsc_mains_tracker.db`
- Importing `data/daily_study_hours.json` from the parent app
- Sharing XP / check-in events from Streamlit garden
