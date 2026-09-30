# Research and implementation basis

- Wagner & Pruß (2002), *The IAPWS Formulation 1995 for the Thermodynamic Properties of Ordinary Water Substance*, DOI 10.1063/1.1461829 — basis for treating fixed density as an explicit incompressible approximation at a stated reference condition.
- Huber et al. (2009), *New International Formulation for the Viscosity of H2O*, DOI 10.1063/1.3088050 — basis for `mu = 1001.6 μPa·s` at 20 °C and 0.101325 MPa.
- Chorin (1968), *Numerical Solution of the Navier–Stokes Equations*, DOI 10.1090/S0025-5718-1968-0242392-2 — foundational projection of velocity onto the divergence-free subspace.
- Guermond, Minev & Shen (2006), *An Overview of Projection Methods for Incompressible Flows*, DOI 10.1016/j.cma.2005.10.010 — motivates explicit boundary/pressure conventions and quantitative error checks.
- Rogallo (1981), *Numerical Experiments in Homogeneous Turbulence*, NASA TM-81315 — periodic Fourier representation and resolution considerations.
- Mortensen & Langtangen (2016), *High Performance Python for Direct Numerical Simulations of Turbulent Flows*, arXiv:1602.03638 — concrete Python pseudospectral formulation, dealiasing, RK methods, and Taylor–Green verification route.
- Brachet et al. (1983), *Small-scale Structure of the Taylor–Green Vortex*, DOI 10.1017/S0022112083001159 — basis for treating Taylor–Green as a nonlinear resolution/convergence case, not a simple exponential exact solution.
- Stam (1999), *Stable Fluids*, DOI 10.1145/311535.311548 — useful visualization context and warning that visual stability does not establish engineering accuracy.

Published results motivate the algorithms and property values; the 32³ default, 0.01 m cube, 0.001 m/s RMS speed, UI, binary stream, and tolerances are implementation choices. The renderer shows particle pathlines and instantaneous sampled velocity arrows. Neither is evidence of spatial convergence. Finite resolution, explicit RK4, and truncation remove unresolved high-wavenumber content; results at higher Reynolds numbers require resolution and energy-spectrum studies.
