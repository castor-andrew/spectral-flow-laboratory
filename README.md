# Spectral Water Flow Laboratory

A Python-authoritative interactive 3D simulation of a periodic cube of incompressible water. NumPy advances the velocity with a Fourier pseudospectral method; FastAPI streams bounded binary tracer/vector data to a Three.js WebGL renderer.

## Model

- Single-phase, Newtonian, isothermal water at 20 °C and 101325 Pa.
- Fixed `rho = 998.2 kg/m³`, `mu = 1.0016e-3 Pa·s`, and `nu = mu/rho`.
- Periodic boundaries in all directions; the wireframe is not a physical wall.
- Pressure is implicit in the Fourier incompressibility projection.
- Fixed 16³ grid and 0.001 m/s initial RMS speed, normalized after filtering and projection.

The collection has 11 structured periodic families: helical, co-rotating and counter-rotating tubes; triple and crossed tubes; a vortex lattice; a double helix; Taylor–Green cells; helical cellular motion; broad shear; and balanced counterflow. A low-mode random Fourier field is the twelfth family. The smooth periodic vortex tubes are not claimed to be exact Burgers vortices.

Automatic selection uses a shuffled 20-entry bag, prevents consecutive repeats, and assigns exactly one slot (5%) to random Fourier flow. A seed identifies the family and its physical parameters. Canvas click/tap or Enter creates a flow; dragging rotates the camera. Sparse velocity arrows are always enabled.

**Sustained** behavior applies bounded linear acceleration (`a_hat = 0.18 u_hat`) only to resolved modes through the momentum RHS. **Free decay** adds no energy. Changing behavior preserves the seed/family and persists across later generations.

## Run

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run.ps1
```

Open <http://localhost:8765>. The first load needs internet access for Three.js from jsDelivr.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Numerical method and rendering

The solver uses a collocated periodic grid, physical wavenumbers `2πn/L`, NumPy FFT normalization, Fourier Helmholtz projection, consistent rectangular 2/3 truncation, and RK4 with projection/filtering at every stage. Advection is evaluated pseudospectrally in convective form. The timestep is the minimum of `0.35 dx/max|u|`, `0.18 dx²/nu`, and a conservative cap. `Re = U_rms L / nu`.

The browser receives generation-tagged little-endian float32 arrays and discards stale generations. One simulation thread runs independently of the single render loop. The renderer reuses buffers for 700 tracers, 90 finite pathlines, and a sparse 4×4×4 vector sample. The 90-path history uses the same maximum segment budget as the earlier 60-path version. A coordinated reset clears all numerical and visual history before new frames are accepted.

## Verification and deployment

`tests/test_solver.py` covers fixed water properties, rest preservation, seeded reproducibility, projection, mean momentum, every family at fixed resolution/RMS, and exact viscous-shear decay. The divergence target is `(L/Uref) max|div u| < 1e-10`.

See [COLLECTION_VALIDATION.md](COLLECTION_VALIDATION.md) for browser measurements and visual evidence, [RESEARCH.md](RESEARCH.md) for references, and [DEPLOY.md](DEPLOY.md) for Docker/iframe integration with andrewcastor.com.
