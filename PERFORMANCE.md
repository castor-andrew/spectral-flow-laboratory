# Performance investigation

Profile date: 2026-09-29. Microsoft Edge headless, 1440×900, fixed seed, 16³ grid, 700 tracers, 64 vector arrows, identical water properties and solver tolerances. Browser measurements use `tools/profile_browser.py`; backend measurements come from `/api/perf`.

## Bottleneck found

The dominant problem was not WebGL fill rate or particle count. The binary WebSocket protocol did not align float data after its variable-length JSON header. Edge raised a `RangeError` on every snapshot. After parsing was corrected, the Points and LineSegments objects were still skipped because their initially empty geometries retained empty frustum-culling bounds. The old 20 Hz solver throttle also limited physical playback to about 0.4 simulated seconds per real second.

Backend physics was already within budget: the final 60-second run measured 6.03 ms mean, 7.25 ms p95, and 8.18 ms p99 per RK4 step. Tracer interpolation cost 0.30 ms mean. Rendering cost 0.085 ms mean and 0.20 ms p95.

## Before and after

| Metric | Before diagnosis | After |
|---|---:|---:|
| JavaScript stream errors | Every message | 0 |
| Rendered flow points | 0 | 700 |
| Draw calls | 1 (box only) | 3 (box, particles, vectors) |
| Physical seconds / real second | ~0.40 | 0.985 |
| Render FPS in headless Edge | not meaningful—the flow failed to render | 53.28 |
| Frame-time p95 / p99 | not meaningful—the flow failed to render | 20.9 / 20.9 ms |
| Render work mean / p95 | 0.15 / 0.20 ms (box only) | 0.085 / 0.20 ms |
| Long tasks over 60 s | — | 0 |
| WebGL resources | 1 geometry | stable at 3 geometries, 0 textures |
| JS heap growth over 60 s | — | 570,884 bytes |
| Payload cadence | ~8 Hz | ~8 Hz |
| Payload size | ~10.6 KB | ~10.6 KB |
| Serialization mean / p95 / p99 | — | 0.83 / 5.61 / 6.68 ms |

The automated Edge environment presents a roughly 53 Hz display cadence, so it cannot demonstrate 60 FPS; the actual WebGL work is far below the 16.7 ms budget. No camera-movement test applies because the requested fixed isometric POV intentionally removes camera controls.

## Changes

- Added 4-byte protocol padding and explicit binary layout handling.
- Disabled frustum culling for dynamic initially-empty particle/vector geometry.
- Reused particle, vector-position, and vector-color typed arrays and GPU attributes.
- Interpolated authoritative timestamped snapshots with shortest periodic displacement.
- Paces each numerical step against its own stable physical `dt`; no step is enlarged or skipped.
- Kept simulation, network delivery, and requestAnimationFrame schedules independent.
- Added bounded timing histories, browser frame/heap/WebGL diagnostics, and repeatable Edge profiling.

## Physics regression

The solver equations, density, viscosity, grid, float64 spectral state, RK4, 2/3 dealiasing, and adaptive stability limits were unchanged. Tests cover fixed properties, rest, seeded reproducibility, projection/momentum, exact viscous shear with timestep refinement, deterministic matching-time output, and non-growing unforced kinetic energy over the regression interval.

Remaining limitation: 32³ and especially 64³ may not maintain 1× real-time physical playback on one CPU core. The UI reports simulated-seconds/real-second honestly. Scaling quality modes requires native FFT acceleration or a dedicated simulation worker/service, not hidden timestep or quality changes.

## Helical-vortex visual redesign

The final 60-second Edge profile of the redesigned flow retained 700 particles, 60 eight-second trail strands, orbit controls, and the 16³ solver. It measured 53.24 FPS on the approximately 53 Hz headless display, 20.9 ms p95/p99 frame spacing, 0.122 ms mean and 0.20 ms p95 render work, four draw calls, zero long tasks, zero JavaScript errors, and no heap growth. Physics measured 6.20/7.56/8.39 ms mean/p95/p99 per step and 0.986 simulated seconds per real second. Five consecutive regenerations retained stable geometry counts. The captured inspected render is `artifacts/fluid-profile.png`.
