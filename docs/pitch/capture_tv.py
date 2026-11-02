"""Screenshots the admin 'Show on lobby TV' card, proves a saved choice changes /tv, then captures every
/tv scene at 1920x1080 and a short clip. Usage: python capture_tv.py <password-file>"""
import json, shutil, sys, urllib.request
from playwright.sync_api import sync_playwright

U = "http://localhost:3000"
pw_ = open(sys.argv[1]).read().strip()
temple = lambda: json.load(urllib.request.urlopen(U + "/api/v1/temple"))["tv_sections"]

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page(); pg.goto(U + "/login", wait_until="networkidle")
    pg.fill("input >> nth=0", "demoadmin"); pg.fill("input[type=password]", pw_); pg.click("button[type=submit]"); pg.wait_for_url("**/admin**")
    pg.goto(U + "/admin/temple", wait_until="networkidle"); pg.add_style_tag(content="nextjs-portal{display:none!important}")
    card = pg.locator("section", has_text="Show on lobby TV"); card.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    card.screenshot(path="shots2/admin_tv_card.png")
    # untick two sections, save, and check the API (and so /tv) follows
    card.get_by_label("Poojas & sevas").uncheck(); card.get_by_label("Scrolling announcement ticker").uncheck()
    card.get_by_role("button", name="Save TV display").click(); pg.wait_for_timeout(1500)
    saved = temple(); assert "poojas" not in saved and "ticker" not in saved and "timings" in saved, saved
    print("saved choice honoured:", saved)
    card.get_by_role("button", name="All").click(); card.get_by_role("button", name="Save TV display").click(); pg.wait_for_timeout(1500)
    assert len(temple()) == 10; ctx.close()

    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir="video", record_video_size={"width": 1280, "height": 720})
    pg = ctx.new_page(); pg.goto(U + "/tv", wait_until="networkidle"); pg.add_style_tag(content="nextjs-portal{display:none!important}")
    for i in range(12):
        pg.wait_for_timeout(2500); pg.screenshot(path=f"shots2/tv_{i}.png")
        if i < 11: pg.wait_for_timeout(9500)
    vid = pg.video; ctx.close(); b.close(); shutil.move(vid.path(), "video/tv.webm")
