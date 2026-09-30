# Flow regeneration and reset validation

## Causes

1. New Flow previously changed only the seed while retaining the selected helical family, so the topology stayed similar. Taylor–Green was seed-invariant. Sustained forcing was proportional to the current low-mode field, preserving whichever dominant pattern was selected.
2. The HTTP reset response assigned the new generation before its first WebSocket frame. The frame therefore did not appear to be a generation change, so the circular pathline history was retained. Old geometry also remained visible during solver initialization.

## Fixes

- Automatic mode chooses among `helical-vortex`, `vortex-pair`, and seeded `taylor-green`, excluding the immediately previous family.
- A specific family can be selected to explore seeded variations within it.
- Taylor–Green now varies physical wavenumber, phase, sign, and component orientation by seed before projection.
- Helical and pair families vary periodic core position, concentration/core width, circulation sign, pair spacing, and perturbation. Low-mode sustained forcing follows each run's projected state, so it does not drive all seeds toward one fixed forcing pattern.
- New Flow creates a new seed and family; Restart sends the exact active configuration.
- One coordinated client reset immediately zeroes point/arrow draw ranges, trail history and colors, circular indices, interpolation endpoints, and diagnostics state. It displays a clean loading panel until initialization completes.
- Client reset requests use abort tokens. The backend serializes reset construction. WebSocket visualization data is rejected while resetting and accepted afterward only when its generation exactly matches the reset response.

## Evidence

`tools/verify_regeneration.py` generated ten flows at the same camera and elapsed time, then tested paused reset and five rapid clicks. The run showed all nine post-first-click immediate-clear assertions passing, no JavaScript errors or long tasks, stable three-geometry ownership, approximately 52.7–53.5 FPS on the ~53 Hz headless Edge display, and no adjacent repeated family.

The visual contact sheet is [artifacts/flow-contact-sheet.png](artifacts/flow-contact-sheet.png). Each panel includes its active family and seed. Numerical verification reports eight passing tests, including fixed water properties, divergence, exact viscous shear refinement, reproducibility, energy behavior, three-dimensional helical flow, distinct supported families, and seed-varying Taylor–Green states.
