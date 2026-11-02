"""Screenshots the lobby TV page scenes (1920x1080) and records a short clip. Usage: python capture_tv.py"""
import shutil
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir="video", record_video_size={"width": 1280, "height": 720})
    pg = ctx.new_page(); pg.goto("http://localhost:3000/tv", wait_until="networkidle")
    pg.add_style_tag(content="nextjs-portal{display:none!important}")
    for i in range(7):
        pg.wait_for_timeout(2200); pg.screenshot(path=f"shots2/tv_{i}.png")
        pg.wait_for_timeout(9900) if i < 6 else None
    vid = pg.video; ctx.close(); b.close(); shutil.move(vid.path(), "video/tv.webm")
