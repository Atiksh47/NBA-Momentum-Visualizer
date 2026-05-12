# NBA Momentum Visualizer

> What did the game *feel* like?

Historic games become living audiovisual experiences.

Momentum shifts distort the particle field.  
Scoring runs trigger shockwaves.  
Clutch possessions tighten the soundtrack into low-frequency pulses.

The same game — experienced four ways:

- **Minimal** — motion graphics. Color and particle drift.
- **Anime** — speed lines, impact frames, screen shake.
- **Cosmic** — teams as colliding star systems. Gravity bends with momentum.
- **Broadcast** — the television layer. Score bug, foul warnings, live run banner.

Not a replay. An interpretation.

---

<!-- Screenshots / GIFs go here — one per mode -->
<!-- ![Minimal mode](docs/minimal.gif) -->
<!-- ![Cosmic mode](docs/cosmic.gif) -->

---

## The signal

Every game is reduced to two curves, sampled once per second:

**Crowd Heat** — overall game intensity, 0→1. Driven by pace, closeness, scoring bursts, and turnover chaos. This is the energy in the room.

**Momentum** — which team owns the moment, −1.0 to +1.0. Derived from recent scoring runs, field goal streaks, and time pressure. It shifts slowly, then suddenly.

These two numbers drive everything — color, particle velocity, audio filter cutoff, gravitational pull in the 3D nebula. The visuals are not decorative. They *are* the data.

Additional signals feed the Broadcast layer:

- **Rolling FG%** — hot streaks and cold spells, team by team, over the last 10 shots
- **Foul pressure** — cumulative fouls per half, flagged when a team is in danger
- **Chaos index** — turnover density per 60-second window; spikes when the game is unraveling

---

## Games

Five games chosen for emotional weight, not statistical significance.

| | Game | Why it's here |
|-|------|---------------|
| 🏆 | **2016 Finals Game 7** | The only 3–1 comeback in Finals history. The Block. The Shot. |
| 🐍 | **Kobe's Last Game** | 60 points at age 37. The last time the crowd got to say goodbye. |
| 🏹 | **Warriors Win 73** | A record that had stood 21 years, broken on the final night. |
| 🎄 | **Christmas 2015 — Warriors vs Cavs** | The rematch nobody could wait for. Curry vs LeBron on the biggest stage. |
| 🍀 | **2022 Finals Game 6 — Curry 43** | The one thing that had eluded him. He got it in Boston. |

---

## Four lenses, one dataset

The modes don't change the data. They change the emotional register you experience it through.

| Mode | Aesthetic | What it emphasizes |
|------|-----------|--------------------|
| **Minimal** | Motion graphics | The slow drift of momentum; color as feeling |
| **Anime** | Sports broadcast energy | Impact, reaction, the visceral moment |
| **Cosmic** | Astrophysics | Scale, inevitability, two forces in collision |
| **Broadcast** | Television | Context, stats, the analytical layer |

Same data. Different medium.

---

## Setup

**Requirements:** Python 3.10+, `nba_api`

```bash
pip install nba_api
python scripts/fetch_games.py   # writes data/*.json, ~30s
```

Then open `index.html` directly in a browser, or serve locally:

```bash
npx serve .
# or
python -m http.server 8000
```

No build step. No dependencies at runtime.

---

## Controls

| | |
|-|-|
| Click to begin | Initializes audio and starts playback |
| Space / ▶ | Play / pause |
| Timeline | Scrub to any moment; colored ticks mark key events |
| ½× 1× 2× 4× | Speed — full game is ~10 min at 4× |
| Mode button | Cycles Minimal → Anime → Cosmic → Broadcast |

---

## Stack

Data: Python + nba_api → static JSON  
Rendering: Canvas 2D (Minimal, Anime, Broadcast) + Three.js lazy-loaded (Cosmic)  
Audio: Web Audio API — no libraries  
Build: none

---

Data from [NBA Stats API](https://www.nba.com/stats).
