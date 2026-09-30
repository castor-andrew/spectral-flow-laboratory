"""Fourier-pseudospectral solver for periodic incompressible water flow."""
from dataclasses import asdict, dataclass
import numpy as np

RHO0 = 998.2
MU = 1.0016e-3
NU = MU / RHO0
REFERENCE_T = 293.15
REFERENCE_P = 101325.0

@dataclass(frozen=True)
class Config:
    seed: int = 1
    n: int = 32
    length: float = .01
    u_rms: float = .001
    preset: str = "random"
    forcing: str = "sustained"
    cfl: float = .35

    def validate(self):
        if self.n not in (16, 32, 64): raise ValueError("resolution must be 16, 32, or 64")
        if not (1e-4 <= self.length <= 1.0): raise ValueError("length must be 1e-4..1 m")
        if not (0 <= self.u_rms <= .05): raise ValueError("u_rms must be 0..0.05 m/s")
        families=("helical-vortex","co-vortex-pair","counter-vortex-pair","triple-vortex","crossed-tubes","vortex-lattice","taylor-green","helical-cellular","broad-shear","balanced-counterflow","double-helix","random","rest","shear")
        if self.preset not in families: raise ValueError("unknown preset")
        if self.forcing not in ("sustained", "free-decay"): raise ValueError("forcing must be sustained or free-decay")
        return self

class SpectralFluid:
    def __init__(self, config=Config()): self.reset(config)
    def reset(self, config):
        self.config=config.validate(); self.n=config.n; self.L=config.length; self.dx=self.L/self.n; self.t=0.; self.steps=0
        modes=np.fft.fftfreq(self.n)*self.n; k=2*np.pi*np.fft.fftfreq(self.n,d=self.dx)
        self.k=np.meshgrid(k,k,k,indexing="ij"); self.k2=sum(q*q for q in self.k); self.k2_safe=self.k2.copy(); self.k2_safe[0,0,0]=1
        mx,my,mz=np.meshgrid(modes,modes,modes,indexing="ij"); self.mask=(np.abs(mx)<=self.n//3)&(np.abs(my)<=self.n//3)&(np.abs(mz)<=self.n//3)
        self.uh=self._initial(); self.uh=self.project(self.filter(self.uh)); self._normalize(); self.initial_energy=self.energy()
    def filter(self,uh): return uh*self.mask[None]
    def project(self,uh):
        dot=sum(self.k[i]*uh[i] for i in range(3)); out=uh.copy()
        for i in range(3): out[i]-=self.k[i]*dot/self.k2_safe
        out[:,0,0,0]=0 if self.config.preset!="shear" else out[:,0,0,0]
        return out
    def _initial(self):
        n,L,c=self.n,self.L,self.config; x=np.arange(n)*L/n; X,Y,Z=np.meshgrid(x,x,x,indexing="ij")
        if c.preset=="rest": u=np.zeros((3,n,n,n))
        elif c.preset=="shear": u=np.array([np.sin(2*np.pi*Y/L),np.zeros_like(X),np.zeros_like(X)])
        elif c.preset=="taylor-green":
            rng=np.random.default_rng(c.seed); q=2*np.pi/L*rng.choice((1,2)); px,py,pz=rng.uniform(0,2*np.pi,3); s=rng.choice((-1.,1.)); xx=q*X+px; yy=q*Y+py; zz=q*Z+pz
            base=np.array([s*np.sin(xx)*np.cos(yy)*np.cos(zz),-s*np.cos(xx)*np.sin(yy)*np.cos(zz),np.zeros_like(X)])
            # Seeded axis permutation produces distinct periodic braided cells without changing the benchmark family.
            perm=rng.permutation(3); u=base[perm]
        elif c.preset in ("helical-vortex","co-vortex-pair","counter-vortex-pair","triple-vortex","crossed-tubes","vortex-lattice","double-helix"):
            rng=np.random.default_rng(c.seed); q=2*np.pi/L; sign=rng.choice((-1.,1.)); cx,cy=rng.uniform(.35*L,.65*L,2); beta=rng.uniform(2.2,3.8)
            def tube_z(px,py,s=1.,axial=.25):
                xx=q*(X-px); yy=q*(Y-py); psi=np.exp(beta*(np.cos(xx)+np.cos(yy)-2)); return np.array([-s*beta*q*np.sin(yy)*psi,s*beta*q*np.sin(xx)*psi,s*q*beta*axial*(psi-psi.mean())])
            def tube_x(py,pz,s=1.):
                yy=q*(Y-py); zz=q*(Z-pz); psi=np.exp(beta*(np.cos(yy)+np.cos(zz)-2)); return np.array([s*q*beta*.18*(psi-psi.mean()),-s*beta*q*np.sin(zz)*psi,s*beta*q*np.sin(yy)*psi])
            def tube_y(px,pz,s=1.):
                xx=q*(X-px); zz=q*(Z-pz); psi=np.exp(beta*(np.cos(xx)+np.cos(zz)-2)); return np.array([s*beta*q*np.sin(zz)*psi,s*q*beta*.18*(psi-psi.mean()),-s*beta*q*np.sin(xx)*psi])
            gap=rng.uniform(.20,.31)*L
            if c.preset=="helical-vortex": u=tube_z(cx,cy,sign,.32)
            elif c.preset=="co-vortex-pair": u=tube_z((cx-gap/2)%L,cy,sign)+.82*tube_z((cx+gap/2)%L,cy,sign)
            elif c.preset=="counter-vortex-pair": u=tube_z((cx-gap/2)%L,cy,sign)+tube_z((cx+gap/2)%L,cy,-sign)
            elif c.preset=="double-helix": u=tube_z((cx-gap/2)%L,cy,sign,.42)+tube_z((cx+gap/2)%L,cy,-sign,-.30)
            elif c.preset=="triple-vortex":
                u=sum((1,.8,-.72)[i]*tube_z((cx+gap*np.cos(2*np.pi*i/3))%L,(cy+gap*np.sin(2*np.pi*i/3))%L,sign if i<2 else -sign) for i in range(3))
            elif c.preset=="crossed-tubes": u=tube_z(cx,cy,sign)+.85*tube_x(cy,.5*L,-sign)+.7*tube_y(cx,.5*L,sign)
            else:
                u=sum(tube_z(px,py,sign*((-1)**(i+j)),.08) for i,px in enumerate((.28*L,.72*L)) for j,py in enumerate((.28*L,.72*L)))
            u += .05*np.std(u)*np.array([np.sin(q*Z+1.3),np.sin(q*X+.7),np.sin(q*Y+2.1)])
        elif c.preset=="helical-cellular":
            rng=np.random.default_rng(c.seed); q=2*np.pi/L; A,B,C=rng.uniform(.65,1.2,3); px,py,pz=rng.uniform(0,2*np.pi,3); u=np.array([A*np.sin(q*Z+pz)+C*np.cos(q*Y+py),B*np.sin(q*X+px)+A*np.cos(q*Z+pz),C*np.sin(q*Y+py)+B*np.cos(q*X+px)])
        elif c.preset=="broad-shear":
            rng=np.random.default_rng(c.seed); q=2*np.pi/L; p=rng.uniform(0,2*np.pi,3); u=np.array([np.sin(q*Y+p[0])+.35*np.sin(q*Z+p[1]),.2*np.sin(q*Z+p[2]),np.zeros_like(X)])
        elif c.preset=="balanced-counterflow":
            rng=np.random.default_rng(c.seed); q=2*np.pi/L; p=rng.uniform(0,2*np.pi,3); u=np.array([np.sin(q*Y+p[0]),np.sin(q*Z+p[1]),np.sin(q*X+p[2])])
        else:
            rng=np.random.default_rng(c.seed); u=rng.normal(size=(3,n,n,n)); uh=np.fft.fftn(u,axes=(1,2,3)); low=(self.k2 <= (2*np.pi/L*4)**2); uh*=low[None]; return uh
        return np.fft.fftn(u,axes=(1,2,3))
    def _normalize(self):
        if self.config.preset=="rest" or self.config.u_rms==0: self.uh*=0; return
        u=self.velocity(); rms=np.sqrt(np.mean(np.sum(u*u,axis=0))); self.uh*=self.config.u_rms/rms
    def velocity(self): return np.fft.ifftn(self.uh,axes=(1,2,3)).real
    def rhs(self,uh):
        uh=self.project(self.filter(uh)); u=np.fft.ifftn(uh,axes=(1,2,3)).real; adv=np.empty_like(u)
        for i in range(3):
            adv[i]=sum(u[j]*np.fft.ifftn(1j*self.k[j]*uh[i]).real for j in range(3))
        ah=self.filter(np.fft.fftn(adv,axes=(1,2,3))); out=-ah-NU*self.k2[None]*uh
        if self.config.forcing=="sustained" and self.config.preset not in ("rest","shear"):
            low=self.k2 <= (2*np.pi/self.L*4)**2; out += .18*uh*low[None]
        return self.project(out)
    def timestep(self,speed=None):
        speed=np.sqrt(np.sum(self.velocity()**2,axis=0)).max() if speed is None else speed; adv=np.inf if speed==0 else self.config.cfl*self.dx/speed
        diff=.18*self.dx*self.dx/NU; return min(adv,diff,2e-2)
    def step(self,dt=None):
        stable=self.timestep(); dt=min(dt or stable,stable); a=self.uh; k1=self.rhs(a); k2=self.rhs(self.project(self.filter(a+dt*k1/2))); k3=self.rhs(self.project(self.filter(a+dt*k2/2))); k4=self.rhs(self.project(self.filter(a+dt*k3)))
        self.uh=self.project(self.filter(a+dt*(k1+2*k2+2*k3+k4)/6)); self.t+=dt; self.steps+=1
        if not np.isfinite(self.uh).all(): raise FloatingPointError("nonfinite spectral state")
        return dt
    def divergence(self):
        dh=sum(1j*self.k[i]*self.uh[i] for i in range(3)); return np.fft.ifftn(dh).real
    def energy(self, u=None): return .5*np.mean(np.sum((self.velocity() if u is None else u)**2,axis=0))
    def diagnostics(self, u=None):
        u=self.velocity() if u is None else u; ref=max(self.config.u_rms,1e-12); div=np.max(np.abs(self.divergence()))*self.L/ref
        speed=np.sqrt(np.sum(u*u,axis=0))
        max_speed=float(speed.max()); forcing_power=.18*float(np.mean(np.sum(u*u,axis=0))) if self.config.forcing=="sustained" else 0.; return {"time":self.t,"step":self.steps,"dt":self.timestep(max_speed),"energy":self.energy(u),"forcing_power":forcing_power,"max_speed":max_speed,"divergence":float(div),"reynolds":self.config.u_rms*self.L/NU,"rho":RHO0,"mu":MU,"nu":NU,"config":asdict(self.config)}
    def sample(self,pos,u=None):
        # Periodic trilinear interpolation; pos is (m,3) in metres.
        q=(pos%self.L)/self.dx; i=np.floor(q).astype(int); f=q-i; u=self.velocity() if u is None else u; out=np.zeros_like(pos)
        for dz in (0,1):
            for dy in (0,1):
                for dx in (0,1):
                    w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2]); ix=(i[:,0]+dx)%self.n; iy=(i[:,1]+dy)%self.n; iz=(i[:,2]+dz)%self.n
                    out += w[:,None]*u[:,ix,iy,iz].T
        return out
