# World State Schema (my-garden only)

Local contract for Discipline World.  
**Not** produced by the CGPSC Mains Tracker.

See `../data/mock_world_state.json` and `../data/study_log.json`.

---

## Study log (input)

```json
{
  "schema_version": 1,
  "daily_target_hours": 6.0,
  "days": [
    { "date": "2026-07-14", "hours": 6.2 },
    { "date": "2026-07-15", "hours": 6.0 },
    { "date": "2026-07-16", "hours": 7.1 },
    { "date": "2026-07-17", "hours": 6.5 }
  ],
  "tests": [
    {
      "id": "test_001",
      "date": "2026-07-17",
      "score_percent": 82,
      "note": "Inflation chapter"
    }
  ]
}
```

Rules engine reads this only.

---

## World state (output for Unity)

```json
{
  "schema_version": 1,
  "generated_at": "2026-07-17T08:00:00+05:30",
  "streak": {
    "continuous_goal_days": 4,
    "toward_tree": 4,
    "toward_blossom": 4
  },
  "pending_seeds": 1,
  "trees": [
    {
      "id": "tree_001",
      "planted_date": "2026-07-17",
      "species": "oak",
      "reason": "4 continuous days ≥ 6h",
      "has_cherry_blossom": false,
      "fruit_tier": null,
      "test_score": null,
      "memory": null
    }
  ]
}
```

### Tree fields

| Field | Meaning |
|-------|---------|
| `has_cherry_blossom` | True after **6 continuous** ≥6h days for that streak/tree |
| `fruit_tier` | `apples` / `peaches` / `mangoes` / `golden` from good marks |
| `test_score` | Optional % that unlocked fruits |

### Fruit tiers (from score)

| Score | `fruit_tier` |
|------:|--------------|
| ≥ 60 | `apples` |
| ≥ 70 | `peaches` |
| ≥ 80 | `mangoes` |
| ≥ 90 | `golden` |

---

## Progression summary (engine)

1. Scan `days` in date order; a day is complete if `hours >= 6`.
2. Continuous complete-day streak length:
   - every **+4** continuous block → `pending_seeds++` / new tree
   - streak length **≥ 6** → set `has_cherry_blossom` on the matching tree
3. On test with good marks → set fruit on latest (or chosen) tree.
