# NBA Momentum Visualizer — Phase 2 Plan

> The difference between a visualization tool and an experience.

Phase 1 proved the concept: play-by-play data can drive a living audiovisual system. Phase 2 is about depth. Every improvement below targets the gap between *reacting to data* and *feeling like a world*.

---

## 1. Momentum as physics, not a UI variable

**The problem:** Momentum currently changes colors and particle speed. That's a mapping. What it should do is change the *rules of the simulation*.

**What to build:**

- **Gravity direction** shifts toward the leading team's side. Particles don't just drift — they *fall* toward dominance.
- **Particle inertia** is asymmetric. Trailing team's particles are sluggish, heavy. Leading team's particles are light, reactive.
- **Camera lean** (Cosmic mode): the camera's rest position biases toward the dominant nebula, not the center.
- **Collision frequency** increases during momentum instability — when the curve is flat near zero, particles interfere more, creating visible turbulence.

**Why it matters:** Right now momentum is legible. After this change, it's *felt*. The viewer doesn't read the score — they sense who's winning from the behavior of the world.

**Implementation notes:**
- Add a `gravityBias` vector derived from `momentumCurve`: `(momentum * 0.8, 0)` in 2D, applied as a constant force each tick
- Particle mass: `mass = 1.0 + (isTrailingTeam ? 0.6 : -0.3)` — affects velocity damping per frame
- Camera lean in `drawCosmic`: nudge `camera.position.x` target by `momentum * 30` with a slow lerp (0.02 per frame)

---

## 2. Crowd Heat with thresholds and aftershock decay

**The problem:** The current energy curve is smooth. Crowds are not smooth. They are dormant, then explosive, then residually charged.

**What to build:**

- **Activation threshold:** When `energyCurve > 0.7`, the system enters an *activated state*. Visual and audio effects don't just scale — they *switch behavior*.
- **Hysteresis:** Activation requires heat to drop below 0.5 before it can deactivate. No flickering in and out at the boundary.
- **Aftershock decay:** When heat spikes and drops, the *visual response* lingers for 5–10 real seconds regardless of the current value.
- **Compounding spikes:** Multiple heat spikes within 30 seconds add rather than average. A sequence of three 0.65 moments should feel bigger than one 0.8 moment.

**Concrete behavior:**
```
activationState = false
aftershockPool  = 0.0  // drains at 0.05/s

each frame:
  if energy > 0.7:
    activationState = true
    aftershockPool = min(aftershockPool + energy * 0.3, 1.5)
  if energy < 0.5 and activationState:
    activationState = false
  aftershockPool = max(0, aftershockPool - 0.05 * dt/1000)

effectiveEnergy = max(energy, aftershockPool * 0.6)
```

Use `effectiveEnergy` in renderers instead of raw `energy`.

---

## 3. Intentional imbalance — visual breathing room

**The problem:** Everything is polished all the time. A visualization tool is consistently good. An experience has quiet and loud.

**What to build:**

- **Dead space baseline:** At low energy, reduce active particle count to 80–120 (from 150). Let the canvas breathe. Black space is not a failure state.
- **Delayed visual response:** Add a 0.3–0.8 second lag between the data signal changing and the full visual response kicking in. Felt as anticipation, not latency.
- **Rare overload events:** When `aftershockPool > 1.2`, briefly push particle count past the normal maximum (1200 → 1800), then decay back. Should happen maybe twice per game.
- **Asymmetric recovery:** Visual intensity rises fast, falls slow. A spike recovers over 4–6 seconds, not immediately.

**Why it matters:** Without breathing room, the viewer habituates. Contrast makes peaks feel like peaks.

---

## 4. State memory — visuals that remember

**The problem:** The system reacts to the current second. Emotion in sports is memory-based. A dunk matters more if the previous 3 minutes have been silent.

**What to build:**

- **Momentum inertia buffer:** A secondary momentum value that lags the real curve by ~90 seconds with exponential smoothing. The visual response blends both — 70% current, 30% remembered.
- **Recent dominance bias:** Track which team has led the last 4 minutes of game time. Bias particle drift subtly toward the team that *has been* dominant, even during brief swings.
- **Clutch sequence memory:** If two or more `clutch_shot` or `lead_change` moments occur within 3 minutes, flag a `highStakes` state. Visual effects gain a subtle persistent undertone (slightly elevated particle baseline, slightly compressed audio range) until the half ends.

**Implementation:**
```javascript
// In the main tick, maintain alongside playheadSec:
momentumMemory = momentumMemory * 0.998 + currentMomentum * 0.002  // ~90s lag
effectiveMomentum = currentMomentum * 0.7 + momentumMemory * 0.3
```

---

## 5. Audio as emotional mixing desk

**The problem:** Audio currently mirrors visuals — intensity goes up, volume and filter cutoff go up. That's one instrument playing the same note louder.

**Four independent audio layers:**

| Layer | Always present | Responds to |
|-------|---------------|-------------|
| **Ambient** | Yes — low sine drones | Nothing. Provides the floor. |
| **Momentum** | Fades in after Q1 | Tonality / key shift. Home dominant = minor. Away dominant = major. Tied = suspended. |
| **Chaos** | Triggered by `toBurst` > 0.4 | Adds rhythmic distortion, stuttered noise bursts. Turnover sequences sound like static. |
| **Clutch** | Final 4 minutes only | Compresses dynamic range + narrows frequency band. Everything gets quieter but more present. |

**Key design rule:** Layers are additive and independent. The chaos layer fires during a turnover burst even if the momentum layer is serene. They don't share a volume bus — they coexist.

**Implementation notes:**
- Momentum layer: retune drone oscillators to minor/major/suspended chord voicings based on `effectiveMomentum`, not just detune cents
- Chaos layer: filtered noise source gated by `toBurst` with a 200ms attack and 2s release; add a subtle low-frequency tremolo at 4–6Hz
- Clutch layer: a compressor node (`DynamicsCompressorNode`) inserted before `_master` in the final 4 minutes, threshold −18dB, ratio 6:1, with a slow attack so it feels like pressure building

---

## 6. Modes that diverge structurally, not cosmetically

**The problem:** The four modes look different but simulate identically. They're skins, not worlds.

**Each mode should change time perception, motion rules, and event sensitivity:**

**Minimal**
- Slow response curve (signals take 2s to fully propagate to visuals)
- Long particle decay — trails persist 3–4x longer than the data warrants
- Smooth cubic easing on all transitions. No abrupt changes.
- Event sensitivity: only `run_start` and `lead_change` trigger visible responses. Single baskets are invisible.

**Anime**
- Exaggerated spikes: energy is raised to the power of 0.6 before being applied (compresses the low end, stretches the high end)
- Frame-freeze on `clutch_shot`: pause particle simulation for 3–5 frames, then release with a burst
- Overshoot + rebound: when momentum shifts, it briefly overshoots the target value before settling (spring dynamics)
- Event sensitivity: everything fires. Free throws get a reaction.

**Cosmic**
- Nonlinear gravity: gravitational pull uses an inverse-square falloff from each nebula center, not linear
- Orbit-based flow: particles near the center follow an orbital path rather than random drift; eccentricity increases with energy
- Momentum bends the *shape* of the nebulae, not just their color — the dominant team's nebula elongates toward center

**Broadcast**
- Discrete updates: HUD elements update on scoring events, not every frame. Feels like a TV cut, not a continuous feed.
- Emphasis on *cuts*: when a key moment fires, the canvas briefly dims to near-black and recovers over 0.5s — like a camera switch
- Reduced particle density (50% of minimal) — the data layer is the visual, not the particles

---

## 7. Editorial key moments

**The problem:** Key moments are algorithmic — a run of 8+, a lead change, a high-energy three. The system has no taste.

**What "taste" means:**

- A dunk in a 20-point blowout is not a key moment
- A missed free throw at 97–97 with 12 seconds left is
- Context is everything

**What to build:**

**Contextual importance score** for every potential moment:
```
importance = base_intensity
           × game_closeness_factor      // exponential: diff < 5pts = 2x, < 2pts = 4x
           × time_remaining_factor      // final 4 min = 3x, final 1 min = 6x
           × sequence_factor            // 3rd key moment in 5 minutes = 2x
```

Only emit a key moment if `importance > threshold` (tuned per type).

**Sequence importance:** Track `momentumSwingVelocity` — the rate of change of the momentum curve over 60 seconds. High velocity (game flipping quickly) amplifies importance of every event during that window.

**Suppress redundant moments:** A timeout called during a 15-point lead is noise. A timeout called after a 7–0 opponent run is editorial — it's the coach stopping the bleeding.

---

## 8. Visual hierarchy

**The problem:** At any given moment, every visual element has similar weight. The eye has nowhere to rest and nowhere to go.

**The hierarchy:**

At all times, exactly three tiers:

1. **Dominant signal** — momentum direction. One color, one drift axis, fills the frame. This is always visible, always legible.
2. **Supporting signal** — crowd heat / energy. Particle density and trail length. Readable but secondary.
3. **Background** — noise, flow, breathing. Never draws attention. Always present.

**Everything else is an interrupt.** Key moments, chyrons, impact frames — these temporarily collapse the hierarchy to a single focus point, then the hierarchy restores.

**Practical changes:**
- Cap the number of simultaneously visible "special" particles (those with glow halos) at 5% of active count, regardless of energy. Scarcity creates emphasis.
- Background particle alpha hard-capped at 0.35 in all modes. They never compete with foreground.
- Key moment text overlays fade in over 0.4s and out over 1.2s — slow exit keeps context readable without demanding attention.

---

## Priority order

If building incrementally, this sequence maximizes perceptible quality gain per unit of work:

1. **Crowd Heat thresholds + aftershock** — highest impact, self-contained change
2. **Momentum as physics** — biggest conceptual leap, changes the feel of everything
3. **State memory** — narrative depth, moderate complexity
4. **Visual hierarchy enforcement** — mostly parameter tuning, immediate improvement
5. **Audio mixing desk** — independent of visuals, can be built in parallel
6. **Editorial key moments** — Python-side change, requires data regeneration
7. **Mode structural divergence** — large scope, best done one mode at a time
8. **Intentional imbalance / breathing room** — fine-tuning layer, last
