import asyncio, json, struct, threading, time
from pathlib import Path
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from solver import Config, SpectralFluid

ROOT=Path(__file__).parent; app=FastAPI(title="Spectral Water Laboratory")
class ConfigBody(BaseModel):
    seed:int=1; n:int=32; length:float=.01; u_rms:float=.001; preset:str="helical-vortex"; forcing:str="sustained"; cfl:float=.35
class Engine:
    def __init__(self):
        self.lock=threading.Lock(); self.reset_lock=threading.Lock(); self.generation=1; self.paused=False; self.fluid=SpectralFluid(Config(seed=np.random.default_rng().integers(1,2**31).item())); self.rate=0.; self.sim_rate=0.; self.error=None; self.timings={k:[] for k in ("step_ms","velocity_ms","tracer_ms","cache_ms")}; self.transport={"messages":0,"bytes":0,"serialize_ms":[]}
        self.tracers=np.random.default_rng(2).random((700,3))*self.fluid.L; self.cached=None; self._cache_locked(self.fluid.velocity()); threading.Thread(target=self.run,daemon=True).start()
    def reset(self,c):
        with self.reset_lock:
            fresh=SpectralFluid(c); rng=np.random.default_rng(c.seed^0xA57A)
            if c.preset in ("helical-vortex","co-vortex-pair","counter-vortex-pair","triple-vortex","double-helix"):
                core_rng=np.random.default_rng(c.seed); core_rng.choice((-1.,1.)); cx,cy=core_rng.uniform(.35*c.length,.65*c.length,2); count=700; theta=rng.uniform(0,2*np.pi,count); radii=c.length*rng.choice(np.array([.055,.09,.14,.21,.30]),count)+rng.normal(0,.008*c.length,count); z=rng.uniform(0,c.length,count)
                radii[:90]=c.length*np.resize(np.array([.055,.08,.11,.145,.18]),90); theta[:90]=np.linspace(0,4*np.pi,90,endpoint=False); z[:90]=np.mod(np.linspace(0,1.8*c.length,90,endpoint=False),c.length)
                tracers=np.column_stack(((cx+radii*np.cos(theta))%c.length,(cy+radii*np.sin(theta))%c.length,z))
            else: tracers=rng.random((700,3))*c.length
            with self.lock: self.fluid=fresh; self.tracers=tracers; self.generation+=1; self.error=None; self._cache_locked(self.fluid.velocity())
    def run(self):
        while True:
            if self.paused: time.sleep(.03); continue
            try:
                start=time.perf_counter()
                with self.lock:
                    mark=time.perf_counter(); dt=self.fluid.step(); self._timing("step_ms",mark)
                    mark=time.perf_counter(); u=self.fluid.velocity(); self._timing("velocity_ms",mark)
                    mark=time.perf_counter(); vel=self.fluid.sample(self.tracers,u); self.tracers=(self.tracers+dt*vel)%self.fluid.L; self._timing("tracer_ms",mark)
                    mark=time.perf_counter(); self._cache_locked(u); self._timing("cache_ms",mark)
                elapsed=time.perf_counter()-start
                # One unit of physical time per wall-clock unit when compute fits its budget.
                time.sleep(max(0.,dt-elapsed)); cycle=time.perf_counter()-start; self.rate=.9*self.rate+.1/cycle; self.sim_rate=.9*self.sim_rate+.1*dt/cycle
            except Exception as e: self.error=str(e); self.paused=True
    def _timing(self,key,start):
        values=self.timings[key]; values.append((time.perf_counter()-start)*1000)
        if len(values)>1200: del values[:200]
    def perf(self):
        with self.lock:
            def stats(v):
                a=np.asarray(v[-1200:]); return {"mean":float(a.mean()),"p95":float(np.percentile(a,95)),"p99":float(np.percentile(a,99)),"samples":len(a)} if len(a) else {}
            return {"compute":{k:stats(v) for k,v in self.timings.items()},"transport":{"messages":self.transport["messages"],"bytes":self.transport["bytes"],"serialize":stats(self.transport["serialize_ms"])},"solver_hz":self.rate,"sim_seconds_per_real_second":self.sim_rate}
    def _cache_locked(self,u):
        d=self.fluid.diagnostics(u); p=(self.tracers/self.fluid.L).astype("<f4"); s=max(1,self.fluid.n//4); arrows=[]
        for x in range(0,self.fluid.n,s):
            for y in range(0,self.fluid.n,s):
                for z in range(0,self.fluid.n,s): arrows.append((x/self.fluid.n,y/self.fluid.n,z/self.fluid.n,*u[:,x,y,z]))
        d.update({"generation":self.generation,"solver_hz":self.rate,"sim_rate":self.sim_rate,"paused":self.paused,"error":self.error,"particles":len(p),"arrow_stride":s}); self.cached=(d,p,np.asarray(arrows,dtype="<f4"))
    def snapshot(self):
        with self.lock:
            d,p,a=self.cached; d={**d,"solver_hz":self.rate,"sim_rate":self.sim_rate,"paused":self.paused,"error":self.error}; return d,p.copy(),a.copy()
engine=Engine(); app.mount("/static",StaticFiles(directory=ROOT/"static"),name="static")
@app.get("/")
def root(): return FileResponse(ROOT/"static"/"index.html")
@app.get("/api/state")
def state(): return engine.snapshot()[0]
@app.get("/health")
def health(): return {"ok":engine.error is None,"generation":engine.generation}
@app.get("/api/perf")
def perf(): return engine.perf()
@app.post("/api/reset")
def reset(c:ConfigBody): engine.reset(Config(**c.model_dump())); return engine.snapshot()[0]
@app.post("/api/pause")
def pause(): engine.paused=not engine.paused; return {"paused":engine.paused}
@app.websocket("/ws")
async def ws(sock:WebSocket):
    await sock.accept()
    try:
        while True:
            started=time.perf_counter(); d,p,a=engine.snapshot(); header=json.dumps({**d,"layout":{"positions":[len(p),3],"arrows":[len(a),6],"dtype":"float32-le","units":{"position":"L-normalized","velocity":"m/s"}}}).encode(); padding=b"\0"*((-(8+len(header)))%4); packet=struct.pack("<II",len(header),p.nbytes)+header+padding+p.tobytes()+a.tobytes(); engine.transport["messages"]+=1; engine.transport["bytes"]+=len(packet); engine.transport["serialize_ms"].append((time.perf_counter()-started)*1000); await sock.send_bytes(packet); await asyncio.sleep(.05)
    except WebSocketDisconnect: pass
