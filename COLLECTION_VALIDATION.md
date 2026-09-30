# Expanded collection verification

Verified against the current application with headless Microsoft Edge/WebGL at 1440×900.

- 9/9 numerical tests passed.
- All 12 public families initialized at 16³, normalized to 0.001 m/s RMS after filtering/projection, remained finite, and had dimensionless divergence below 1e-10.
- The 20-slot selection bag contains 11 structured families and one random Fourier slot. A reproducible 10,000-seed audit measured random at 5.06%.
- Twelve canvas-generated flows were captured at one camera and 1.6 s comparable elapsed time, without consecutive repeats.
- Every one of 11 observed regeneration frames immediately cleared particles, arrows, and trail vertices.
- Evolution changes retained the same seed/family, and free-decay persisted into subsequent flows.
- Canvas drag did not regenerate. Enter did. Six rapid clicks converged to one valid active generation with no client errors or stale history.
- Browser stress sample: 53.33 FPS, 20.9 ms frame-time p95, 0.153 ms mean renderer work, zero long tasks, four geometries, zero textures, and 16.4 MB used JS heap.

Evidence:

- [Simplified simulator](artifacts/simplified-simulator.png)
- [Twelve-flow contact sheet](artifacts/expanded-flow-contact-sheet.png)
- Individual captures are under `static/evidence/`.

The repeatable browser verifier is `tools/verify_collection.py`.
