"""Captures demo screenshots + walkthrough video from the local site. Usage: python capture.py <password-file>"""
import sys, glob, os, shutil
from playwright.sync_api import sync_playwright
U = "http://localhost:3000"
pw_ = open(sys.argv[1]).read().strip()
HIDE = "nextjs-portal,[data-nextjs-toast]{display:none!important}"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir="video", record_video_size={"width": 1280, "height": 800})
    pg = ctx.new_page()
    def go(path, name=None, wait=1500, scroll=False):
        pg.goto(U + path, wait_until="networkidle"); pg.add_style_tag(content=HIDE); pg.wait_for_timeout(wait)
        if name: pg.screenshot(path=f"shots2/{name}.png")
        if scroll:
            for _ in range(3): pg.mouse.wheel(0, 450); pg.wait_for_timeout(700)
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(500)
    for path, name in [("/en", "home"), ("/en/timings", "timings"), ("/en/poojas", "poojas"), ("/en/festivals", "festivals"), ("/en/gallery", "gallery"),
                       ("/en/announcements", "announcements"), ("/en/committee", "committee"), ("/en/contact", "contact"), ("/te", "telugu")]:
        go(path, name, scroll=name in ("home", "poojas"))
    # sign in
    go("/login", "login")
    pg.fill("input >> nth=0", "demoadmin"); pg.fill("input[type=password]", pw_); pg.wait_for_timeout(500)
    pg.click("button[type=submit]"); pg.wait_for_url("**/admin**", timeout=20000); pg.wait_for_timeout(2000)
    for path, name in [("/admin", "admin_dashboard"), ("/admin/seva-tickets", "admin_tickets"), ("/admin/donors", "admin_donors"), ("/admin/donations", "admin_donations"),
                       ("/admin/finance", "admin_finance"), ("/admin/poojas", "admin_poojas"), ("/admin/users", "admin_users"), ("/admin/audit", "admin_audit")]:
        go(path, name, wait=2500)
    pg.set_viewport_size({"width": 390, "height": 844}); go("/en", "mobile"); pg.set_viewport_size({"width": 1440, "height": 900})
    vid = pg.video; ctx.close(); b.close()
    shutil.move(vid.path(), "video/walkthrough.webm")
print("done", len(glob.glob("shots2/*.png")))
