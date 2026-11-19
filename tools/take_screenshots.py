#!/home/hatch/workspace/tools/shot-venv/bin/python
"""Capture the local app scenes declared in shots.json via file://."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.append('/usr/lib/python3/dist-packages')
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path('/home/hatch/workspace/tools/shot-venv/bin/python')
CHROMIUM = '/home/hatch/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome'
APP = (ROOT / 'app' / 'index.html').as_uri()


def main():
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError(f'Run this script with {PYTHON}; current Python is {sys.executable}')

    shots = json.loads((ROOT / 'shots.json').read_text())
    output_dir = ROOT / 'screenshots'
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROMIUM,
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--allow-file-access-from-files'],
        )
        try:
            for shot in shots:
                page = browser.new_page(viewport={'width': shot['w'], 'height': shot['h']})
                try:
                    page.goto(APP + shot['query'], wait_until='load', timeout=30000)
                    page.wait_for_function('window.__shotReady === true', timeout=30000)
                    target = output_dir / shot['name']
                    page.screenshot(path=str(target), type='jpeg', quality=88)

                    if target.stat().st_size > 250000:
                        quality = 82
                        while target.stat().st_size > 260000 and quality >= 20:
                            with Image.open(target) as image:
                                image.convert('RGB').save(
                                    target, format='JPEG', quality=quality, optimize=True
                                )
                            quality -= 5
                    if target.stat().st_size > 262144:
                        raise RuntimeError(
                            f'{target.name} remains over 262144 bytes after recompression '
                            f'({target.stat().st_size} bytes)'
                        )
                finally:
                    page.close()
        finally:
            browser.close()

    for shot in shots:
        path = output_dir / shot['name']
        print(f'{path.name}: {path.stat().st_size} bytes')


if __name__ == '__main__':
    main()
