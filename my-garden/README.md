# Discipline World (`my-garden`)

A persistent open-world garden that grows from **your own study log inside this project**.

> **Independent of the CGPSC Mains Tracker.**  
> This folder does **not** read hours, streaks, or tests from the existing mains routine app (`garden_api.py`, `database.py`, Godot garden, etc.).  
> Study data for the world lives **here only**.

---

## Core mechanics (only these drive growth)

| Real study | World change |
|------------|--------------|
| **4 continuous days** of **≥ 6 hours** each | **One permanent tree** is earned |
| **6 continuous days** of **≥ 6 hours** each | **Cherry blossoms** on the tree |
| **Good marks** on a test you log | **Fruits** on the tree |

Trees never disappear. No coins, gems, XP, loot boxes, or battle pass.

Full vision (atmosphere, regions, wildlife — later layers): [`VISION.md`](./VISION.md)

---

## Philosophy

- Not a gamified dashboard — a living world you walk through.
- Only real study logged **in my-garden** grows the forest.
- No data wire into the mains tracker app.
- Years later the grove is a visual archive of discipline.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [`VISION.md`](./VISION.md) | Long-term world fantasy |
| [`docs/PROGRESSION.md`](./docs/PROGRESSION.md) | **Canonical rules** (4 / 6 / fruits) |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | Self-contained stack |
| [`docs/WORLD_STATE_SCHEMA.md`](./docs/WORLD_STATE_SCHEMA.md) | Local save / world JSON |
| [`docs/ROADMAP.md`](./docs/ROADMAP.md) | Build phases |

---

## Folder layout

```text
my-garden/
  VISION.md
  README.md
  docs/
  data/           # local study log + world state (this project only)
  unity/          # Unity 6 project (create with Unity Hub)
  tools/
```

---

## Data flow (standalone)

```text
my-garden study log  (hours per day + optional test scores)
        │
        ▼
  progression engine  (4-day tree · 6-day blossom · fruits)
        │
        ▼
  world state JSON
        │
        ▼
  Unity world  (trees, blossoms, fruits, walk around)
```

Nothing talks to the parent tracker’s SQLite or APIs.

---

## Guiding principles

1. Real study (logged here) drives all progression.
2. Mains tracker app is a separate project — no shared live feed.
3. **4 continuous 6h days → tree · 6 days → cherry blossom · good marks → fruits.**
4. Peaceful, personal forest — not competitive.
