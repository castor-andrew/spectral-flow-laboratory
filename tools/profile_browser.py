"""Repeatable Edge/WebGL profile. Run while the local server is active."""
import json, os, time, urllib.request
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.options import Options

opts=Options(); opts.binary_location=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
opts.add_argument("--headless=new"); opts.add_argument("--window-size=1440,900"); opts.add_argument("--enable-webgl"); opts.add_argument("--ignore-gpu-blocklist")
driver=webdriver.Edge(options=opts)
try:
    driver.get("http://127.0.0.1:8765/?embed=1")
    for _ in range(60):
        if driver.execute_script("return !!window.__fluidMetrics && document.querySelector('#connection').classList.contains('live')"): break
        time.sleep(.25)
    driver.execute_script("document.querySelector('#seed').value='2026';document.querySelector('#preset').value='helical-vortex';document.querySelector('#forcing').value='sustained';document.querySelector('#restart').click()")
    time.sleep(5); before=driver.execute_script("return window.__fluidMetrics()")
    canvas=driver.find_element("css selector","#viewport canvas"); ActionChains(driver).move_to_element(canvas).click_and_hold().move_by_offset(90,35).release().perform()
    time.sleep(float(os.getenv("PROFILE_SECONDS","60"))); after=driver.execute_script("return window.__fluidMetrics()")
    driver.save_screenshot("artifacts/fluid-profile.png")
    reset_times=[]
    for _ in range(5):
        t=time.perf_counter(); driver.find_element("id","new").click(); time.sleep(.75); reset_times.append((time.perf_counter()-t)*1000)
    after_resets=driver.execute_script("return window.__fluidMetrics()")
    backend=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/perf"))
    result={"browser_before":before,"browser_after_60s":after,"browser_after_resets":after_resets,"heap_growth_bytes":None if before["heap_used"] is None else after["heap_used"]-before["heap_used"],"reset_roundtrip_ms":reset_times,"backend":backend}
    print(json.dumps(result,indent=2))
finally: driver.quit()
