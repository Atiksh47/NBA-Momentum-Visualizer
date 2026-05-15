# NBA Momentum Visualizer — Improvement Backlog

Improvements are grouped into phases. Each phase is self-contained and shippable on its own.
Earlier phases fix correctness and feel; later phases expand capability.

---

## Phase 1 — Bug Fixes & Correctness

These are things that are currently wrong, not just unpolished.

### 1.1 Seek doesn't restore broadcast state
When you seek into the middle of a game, `_bcRunTeam` and `_bcRunPts` are zeroed.
If you land inside a 15-0 run, the banner won't appear for the rest of that run.
**Fix:** on seek, fast-forward through `game.events` up to `sec` to rebuild run state,
same way `advanceScore()` already does for the score.

### 1.2 `loadGame` has no error handling
If the fetch fails (bad network, wrong `?game=` param), the page stays frozen on
"Loading…" with no feedback.
**Fix:** add a `.catch()` that shows a visible error message on the start screen.

### 1.3 Audio keeps running after game ends
After `endShown = true`, `updateAudio()` still loops and the drones keep shifting.
The end card appears but the audio never resolves.
**Fix:** fade master gain to 0 over ~3s when `endShown` is set, then stop scheduling
further audio updates.

### 1.4 `findScore()` ignores its `sec` argument
`function findScore(sec)` never uses `sec` — it just returns the global `_scoreH/_scoreA`.
The parameter is misleading.
**Fix:** remove the `sec` parameter from the signature and all call sites.

### 1.5 `silenceGain` / `silenceLayerMul` are dead code
Both are hardcoded to `1.0` in `updateAudio()` and never modified.
They multiply through audio gain calculations with no effect.
**Fix:** remove both variables and inline `1.0` (i.e. remove the multiplications).

---

## Phase 2 — Feel & Polish

These don't break anything but make the experience noticeably better.

### 2.1 Keyboard shortcuts
No keyboard support exists. Minimum useful set:
- `Space` — play / pause
- `←` / `→` — jump to previous / next moment tick
- `m` — cycle modes
- `1`–`4` — jump directly to a mode (Minimal / Anime / Cosmic / Broadcast)

### 2.2 Mode picker instead of cycling button
The single "Minimal" button gives no indication that 3 other modes exist.
Users who don't click it at least 4 times never know.
**Fix:** replace with a horizontal pill selector showing all four labels side by side.
The active mode is highlighted; others are dimmed. Fits in the same control row.

### 2.3 Moment text in Cosmic and Broadcast modes
Minimal shows the moment overlay text. Anime shows the chyron. Cosmic and Broadcast
show nothing textual when a key moment fires — you'd have to watch the timeline ticks.
**Fix:**
- Cosmic: subtle full-screen text label (small, centered, fades in/out) for lead
  changes and run starts. Keep it sparse — one or two words max.
- Broadcast: the chyron already exists in the DOM; show it in Broadcast mode too
  (possibly with a different color/style than Anime).

### 2.4 `bcClockStr` and `clockString` are the same function
Two functions, identical math, different return shapes.
**Fix:** merge into one `clockString(sec, asObject)` or just have one call the other.

---

## Phase 3 — Interaction

These add meaningful user control that doesn't exist yet.

### 3.1 Touch / mobile support for timeline
The timeline drag only listens to `mousemove` / `mouseup`. On mobile the timeline
is non-interactive.
**Fix:** add parallel `touchstart` / `touchmove` / `touchend` handlers that extract
`e.touches[0].clientX` and pass to `timelineSeek()`.

### 3.2 Click-to-jump on moment ticks
Moment ticks in the timeline already have a click handler (line 1259 in original).
But after seeking, if you were playing, playback should auto-resume.
Currently it seeks but leaves `playing` state unchanged — if you were paused, you
stay paused at the new position without feedback.
**Fix:** after a tick-click seek, resume playback and show a brief "jumped to X" label.

### 3.3 Scrubbing preview label
While dragging the timeline, show a floating label above the thumb with the clock
time at that position (e.g. "Q3 4:22"). Disappears on mouse-up.
**Fix:** on `mousemove` during drag, compute the clock string and position a tooltip
element above `timeline-thumb`.

---

## Phase 4 — Content Expansion

These add new games and give users more control over what they watch.

### 4.1 Fetch any game by ID
The Python pipeline (`scripts/fetch_games.py`) already works for any NBA game ID.
The UI only exposes the 5 hardcoded games.
**Fix:** add an input field on `index.html` where a user can paste any NBA game ID
and have the script fetch + cache it, then open the visualizer for that game.
Requires a small local server or pre-run step — document clearly.

### 4.2 More curated games
The current 5 games cover specific archetypes well. Gaps:
- A game that goes to OT
- A blowout that was close until Q4 (tests AFTERMATH scene)
- A playoff game from a different era (pre-2015)

Fetch 3–5 more with `fetch_games.py` and add them to `index.html`.

### 4.3 Game search on index page
Instead of a static list, add a search/filter on `index.html` by team, year, or type
(Finals / regular season / playoff). Works off the existing JSON metadata.

---

## Phase 5 — Cosmic Mode Depth

These are GPU-level improvements specific to Cosmic mode.

### 5.1 Move gravitational wave to GPU
Currently when `_cosmicWave > 0.005`, 3,000 star positions are updated in JS and
re-uploaded to the GPU every frame. This is the heaviest per-frame JS cost.
**Fix:** pass `waveAmplitude` and star base positions as shader uniforms/attributes.
The vertex shader computes the radial push: `pos = basePos + normalize(basePos) * wave * exp(-dist/90)`.
Zero JS per frame during waves.

### 5.2 Color-tinted nebula cores
Right now both nebulae are uniform point clouds. Adding a soft additive glow at
each attractor center (a `THREE.Sprite` or a second pass with a large blurred point)
would make the nebulae feel like they have a gravitational center.

### 5.3 Camera shake in Cosmic on big moments
The 2D modes have `triggerShake()`. Cosmic has no equivalent — a gravitational wave
fires but the camera stays smooth.
**Fix:** on `run_start` or `clutch_shot` moments, apply a brief camera position jitter
(add decaying noise to `camera.position.x/y`) in `drawCosmic()`.

---

## Done (already shipped)

- Named `GAME_SPEED_SCALE` constant replacing magic `* 20`
- Speed-line random lengths baked at `triggerFlash()` call, not per-frame
- Shared `drawParticles()` collapsing three near-identical particle loops
