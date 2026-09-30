import json, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.options import Options

root=Path(__file__).resolve().parents[1]; out=root/"static"/"evidence"; out.mkdir(parents=True,exist_ok=True)
opts=Options(); opts.binary_location=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"; opts.add_argument("--headless=new"); opts.add_argument("--window-size=1440,900"); opts.add_argument("--enable-webgl"); opts.add_argument("--ignore-gpu-blocklist")
d=webdriver.Edge(options=opts); records=[]; immediate_clears=[]
try:
 d.get("http://127.0.0.1:8765/?embed=1")
 for _ in range(100):
  m=d.execute_script("return window.__fluidMetrics?.()")
  if m and not m["resetting"] and m["family"]: break
  time.sleep(.1)
 previous=None
 for i in range(10):
  if i:
   old=d.execute_script("return window.__fluidMetrics().generation"); d.find_element("id","new").click(); now=d.execute_script("return window.__fluidMetrics()"); immediate_clears.append(now["trail_vertices"]==0 and now["point_draw_count"]==0 and now["arrow_draw_count"]==0)
   for _ in range(100):
    m=d.execute_script("return window.__fluidMetrics()")
    if not m["resetting"] and m["generation"]!=old: break
    time.sleep(.05)
  time.sleep(2); m=d.execute_script("return window.__fluidMetrics()"); assert m["family"]!=previous; previous=m["family"]; records.append({k:m[k] for k in ("generation","family","seed","render_fps","frame_p99_ms","heap_used","trail_vertices","errors")}); d.save_screenshot(str(out/f"flow-{i:02d}.png"))
 # Paused reset and rapid reset stress.
 d.find_element("id","pause").click(); time.sleep(.2); d.find_element("id","new").click(); time.sleep(1)
 for _ in range(5): d.find_element("id","new").click(); time.sleep(.03)
 time.sleep(2); stress=d.execute_script("return window.__fluidMetrics()")
 d.get("http://127.0.0.1:8765/static/evidence/contact-sheet.html"); labels=json.dumps(records)
 d.execute_script("const r=arguments[0];r.forEach((x,i)=>document.querySelector('#p'+i).textContent=`${i+1}. ${x.family} · seed ${x.seed}`)",records); d.set_window_size(1400,1700); d.save_screenshot(str(root/"artifacts"/"flow-contact-sheet.png"))
 print(json.dumps({"flows":records,"immediate_clears":immediate_clears,"stress":stress},indent=2))
finally: d.quit()
