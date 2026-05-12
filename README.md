# NBA Momentum Visualizer

> What did the game *feel* like?

A cinematic, data-driven experience that transforms NBA play-by-play into a living visual and audio landscape. Not a stats dashboard — a mood engine.

---

## What it does

Pick a historic game. Watch the momentum shift in real time as the data drives a particle field, a generative soundscape, and key moment overlays. Four visual modes let you experience the same game through completely different aesthetics.

---

## Visual modes

| Mode | Description |
|------|-------------|
| **Minimal** | Soft particle field. Team colors blend with momentum. Text overlays for key moments. |
| **Anime** | Speed-line trails, screen shake, impact flashes, chyron wipe-ins. Same data, different medium. |
| **Cosmic** | Three.js WebGL. Teams as star nebulae. Momentum warps gravity. Bloom + film grain post-processing. |
| **Broadcast** | TV graphics package. Score bug, momentum bar, shooting streak tags, foul trouble warnings, live run banner. |

---

## Games included

| Game | Date |
|------|------|
| 2016 Finals Game 7 — The Comeback | Jun 19, 2016 |
| Kobe's Last Game — 60 points | Apr 13, 2016 |
| Warriors Win 73 | Apr 13, 2016 |
| Christmas 2015 — Warriors vs Cavs | Dec 25, 2015 |
| 2022 Finals Game 6 — Curry 43 | Jun 16, 2022 |

---

## How it works

### Data pipeline

A Python script fetches play-by-play from the NBA Stats API and pre-processes it into static JSON files. No server required at runtime — everything runs from flat files.

**Signals computed per game:**

- `momentumCurve` — −1.0 (home dominant) to +1.0 (away dominant), driven by scoring runs, FG%, and time pressure
- `energyCurve` — 0→1 overall game intensity: pace, closeness, scoring bursts, turnover chaos
- `homeFgPct` / `awayFgPct` — rolling 10-shot field goal % per team, per second
- `homeFouls` / `awayFouls` — cumulative fouls within each half, reset at halftime
- `toBurst` — combined turnovers per 60s window, normalized
- `keyMoments` — scored runs, lead changes, clutch threes, foul trouble triggers, timeouts

### Frontend

Vanilla JS + Canvas 2D for Minimal / Anime / Broadcast. Three.js (lazy-loaded) for Cosmic. Web Audio API for the generative soundscape. No build step.

---

## Setup

### Prerequisites

- Python 3.10+
- `nba_api` library

```bash
pip install nba_api
```

### Generate game data

```bash
cd scripts
python fetch_games.py
```

This writes five JSON files to `data/`. Takes ~30 seconds due to rate-limit delays between requests.

### Run

Open `index.html` in a browser. No server needed — works from the filesystem via `file://`, or serve with any static file server:

```bash
npx serve .
# or
python -m http.server 8000
```

---

## Controls

| Control | Action |
|---------|--------|
| Click start screen | Begin playback + initialize audio |
| Space / play button | Play / pause |
| Timeline scrub | Jump to any moment |
| Moment ticks | Hover to preview, click to jump |
| ½× 1× 2× 4× | Playback speed (full game ≈ 10 min at 4×) |
| Mode button | Cycle through Minimal → Anime → Cosmic → Broadcast |
| ← All Games | Return to game selector |

---

## Project structure

```
├── index.html          # Game selector
├── visualizer.html     # Main experience
├── data/               # Pre-processed game JSONs
│   └── *.json
└── scripts/
    └── fetch_games.py  # Data pipeline
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Data | Python + nba_api |
| Rendering | Canvas 2D + Three.js (Cosmic mode only) |
| Audio | Web Audio API |
| Build | None |

---

Data from [NBA Stats API](https://www.nba.com/stats).
