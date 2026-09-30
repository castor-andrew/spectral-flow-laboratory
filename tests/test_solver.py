import numpy as np
from solver import Config, MU, NU, RHO0, SpectralFluid
def test_fixed_properties(): assert RHO0==998.2 and MU==1.0016e-3 and NU==MU/RHO0
def test_rest_preserved():
 s=SpectralFluid(Config(n=16,preset="rest",u_rms=0)); s.step(.001); assert np.max(np.abs(s.velocity()))==0
def test_seed_reproducible():
 a=SpectralFluid(Config(n=16,seed=42)); b=SpectralFluid(Config(n=16,seed=42)); assert np.array_equal(a.uh,b.uh)
def test_projection_and_momentum():
 s=SpectralFluid(Config(n=16,seed=8)); mean0=s.velocity().mean((1,2,3)); s.step(.001); assert np.max(np.abs(s.divergence()))*s.L/s.config.u_rms<1e-10; assert np.max(np.abs(s.velocity().mean((1,2,3))-mean0))<1e-14
def test_viscous_shear_exact_and_refines():
 def err(dt):
  s=SpectralFluid(Config(n=16,preset="shear",u_rms=.001)); t=.04
  while s.t<t-1e-14: s.step(min(dt,t-s.t))
  exact=s.config.u_rms*np.sqrt(2)*np.exp(-NU*(2*np.pi/s.L)**2*t); y=np.arange(s.n)*s.L/s.n; target=exact*np.sin(2*np.pi*y/s.L); return np.linalg.norm(s.velocity()[0]-target[None,:,None])/np.linalg.norm(target[None,:,None])
 e1,e2=err(.01),err(.005); assert e2<1e-3 and e2<=e1*1.1
def test_matching_time_and_energy_regression():
 c=Config(n=16,seed=2026,forcing="free-decay"); a,b=SpectralFluid(c),SpectralFluid(c); e0=a.energy()
 for _ in range(10): a.step(.002); b.step(.002)
 assert a.t==b.t and np.array_equal(a.uh,b.uh)
 assert a.energy() <= e0*(1+1e-10)
def test_helical_vortex_is_3d_divergence_free_and_seeded():
 a=SpectralFluid(Config(n=16,seed=10,preset="helical-vortex")); b=SpectralFluid(Config(n=16,seed=11,preset="helical-vortex")); u=a.velocity()
 assert all(np.std(u[i])>0 for i in range(3))
 assert not np.array_equal(a.uh,b.uh)
 assert np.max(np.abs(a.divergence()))*a.L/a.config.u_rms < 1e-10
def test_supported_families_are_distinct_and_reproducible():
 fields=[]
 for family in ("helical-vortex","co-vortex-pair","taylor-green"):
  a=SpectralFluid(Config(n=16,seed=77,preset=family)); b=SpectralFluid(Config(n=16,seed=77,preset=family)); assert np.array_equal(a.uh,b.uh); fields.append(a.uh)
 assert all(not np.array_equal(fields[i],fields[j]) for i in range(3) for j in range(i))
 a=SpectralFluid(Config(n=16,seed=1,preset="taylor-green")); b=SpectralFluid(Config(n=16,seed=2,preset="taylor-green")); assert not np.array_equal(a.uh,b.uh)
def test_all_public_families_fixed_resolution_rms_and_projection():
 families=("helical-vortex","co-vortex-pair","counter-vortex-pair","triple-vortex","crossed-tubes","vortex-lattice","taylor-green","helical-cellular","broad-shear","balanced-counterflow","double-helix","random")
 for family in families:
  s=SpectralFluid(Config(n=16,seed=913,preset=family,u_rms=.001)); u=s.velocity()
  assert np.isfinite(u).all() and s.n==16
  assert abs(np.sqrt(np.mean(np.sum(u*u,axis=0)))-.001)<1e-14
  assert np.max(np.abs(s.divergence()))*s.L/s.config.u_rms<1e-10
