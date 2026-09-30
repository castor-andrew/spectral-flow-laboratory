import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "static" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
(ROOT / "artifacts").mkdir(exist_ok=True)

opts = Options()
opts.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1440,900")
opts.add_argument("--enable-webgl")
opts.add_argument("--ignore-gpu-blocklist")
opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
driver = webdriver.Edge(options=opts)


def metrics():
    return driver.execute_script("return window.__fluidMetrics?.()")


def wait_ready(old_generation=None, timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        m = metrics()
        if m and not m["resetting"] and m["family"] and (old_generation is None or m["generation"] != old_generation):
            return m
        time.sleep(0.05)
    raise TimeoutError({"metrics": metrics(), "error_text": driver.find_element("id", "error").text, "console": driver.get_log("browser")})


def canvas_click():
    canvas = driver.find_element("css selector", "#viewport canvas")
    ActionChains(driver).move_to_element(canvas).click().perform()


try:
    driver.get("http://127.0.0.1:8766/?embed=1")
    wait_ready()
    driver.save_screenshot(str(ROOT / "artifacts" / "simplified-simulator.png"))

    forbidden = ("new", "restart", "pause", "export", "import", "file", "preset", "resolution", "speed", "arrows")
    assert all(not driver.find_elements("id", item) for item in forbidden)
    assert len(driver.find_elements("id", "forcing")) == 1

    records, immediate_clears = [], []
    for index in range(12):
        if index:
            old = metrics()["generation"]
            canvas_click()
            cleared = metrics()
            immediate_clears.append(all(cleared[k] == 0 for k in ("trail_vertices", "point_draw_count", "arrow_draw_count")))
            wait_ready(old)
        time.sleep(1.6)
        m = metrics()
        assert m["resolution"] == 16 and m["u_rms"] == 0.001 and m["arrow_visible"]
        assert not m["errors"], m["errors"]
        records.append({k: m[k] for k in ("generation", "family", "seed", "render_fps", "frame_p95_ms", "render_mean_ms", "heap_used", "trail_vertices", "arrow_draw_count")})
        driver.save_screenshot(str(EVIDENCE / f"collection-{index:02d}.png"))

    # Changing behavior must restart the same seed/family and persist into later generations.
    before = metrics()
    Select(driver.find_element("id", "forcing")).select_by_value("free-decay")
    same = wait_ready(before["generation"])
    assert same["seed"] == before["seed"] and same["family"] == before["family"] and same["forcing"] == "free-decay"
    old = same["generation"]
    canvas_click()
    after = wait_ready(old)
    assert after["forcing"] == "free-decay"

    # A drag rotates but must not regenerate.
    canvas = driver.find_element("css selector", "#viewport canvas")
    old = metrics()["generation"]
    ActionChains(driver).move_to_element(canvas).click_and_hold().move_by_offset(80, 30).release().perform()
    time.sleep(0.2)
    assert metrics()["generation"] == old

    # Enter and rapid clicks exercise the shared generation-safe reset path.
    driver.find_element("tag name", "body").send_keys(Keys.ENTER)
    wait_ready(old)
    for _ in range(6):
        canvas_click()
        time.sleep(0.03)
    stress = wait_ready(timeout=10)
    time.sleep(1)
    stress = metrics()
    assert not stress["errors"] and stress["resolution"] == 16 and stress["arrow_visible"]

    slots = driver.execute_script("return window.__familySlots")
    assert len(slots) == 20 and slots.count("random") == 1 and len(set(slots) - {"random"}) == 11
    sample = driver.execute_script("return Array.from({length:10000},(_,i)=>window.__flowFamilyForSeed(i+1))")
    distribution = {name: sample.count(name) for name in sorted(set(sample))}
    random_share = distribution["random"] / len(sample)
    assert 0.04 <= random_share <= 0.06

    # Build a same-camera contact sheet from the captured frames.
    cards = "".join(f'<figure><img src="collection-{i:02d}.png"><figcaption id="p{i}"></figcaption></figure>' for i in range(12))
    html = f'''<!doctype html><meta charset="utf-8"><style>body{{margin:0;background:#071216;color:#dbe9e8;font:14px system-ui}}h1{{padding:18px 24px 4px;margin:0}}p{{padding:0 24px 14px;color:#8aa5a4}}main{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:8px}}figure{{margin:0;background:#0b1b20}}img{{display:block;width:100%;height:250px;object-fit:cover}}figcaption{{padding:9px 10px;font:12px monospace;color:#a8d8d4}}</style><h1>Expanded structured-flow collection</h1><p>Fixed camera · comparable elapsed time · 16³ · U₀ = 0.001 m/s</p><main>{cards}</main>'''
    (EVIDENCE / "collection-contact-sheet.html").write_text(html, encoding="utf-8")
    driver.get("http://127.0.0.1:8766/static/evidence/collection-contact-sheet.html")
    driver.execute_script("arguments[0].forEach((x,i)=>document.querySelector('#p'+i).textContent=`${i+1}. ${x.family} · seed ${x.seed}`)", records)
    driver.set_window_size(1440, 1260)
    driver.save_screenshot(str(ROOT / "artifacts" / "expanded-flow-contact-sheet.png"))
    print(json.dumps({"flows": records, "immediate_clears": immediate_clears, "distribution_10000": distribution, "random_share": random_share, "stress": stress}, indent=2))
finally:
    driver.quit()
