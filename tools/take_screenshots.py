#!/home/hatch/workspace/tools/shot-venv/bin/python
"""Capture current app screenshots declared in shots.json."""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

sys.path.append('/usr/lib/python3/dist-packages')
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path('/home/hatch/workspace/tools/shot-venv/bin/python')
CHROMIUM = '/home/hatch/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome'
BASE_URL = 'http://127.0.0.1:8080/'


def server_responds():
    try:
        with urlopen(BASE_URL, timeout=1) as response:
            return response.status < 500
    except (URLError, OSError):
        return False


def main():
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError(f'Run this script with {PYTHON}; current Python is {sys.executable}')

    shots = json.loads((ROOT / 'shots.json').read_text())
    output_dir = ROOT / 'screenshots'
    output_dir.mkdir(parents=True, exist_ok=True)
    server = None

    if not server_responds():
        server = subprocess.Popen(
            ['node', 'serve.ts'], cwd=ROOT, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not server_responds():
            if server.poll() is not None:
                raise RuntimeError(f'node serve.ts exited with status {server.returncode}')
            time.sleep(0.2)
        if not server_responds():
            raise RuntimeError('node serve.ts did not respond on port 8080 within 30 seconds')

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=CHROMIUM,
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-crashpad', '--no-crashpad'],
            )
            try:
                for shot in shots:
                    page = browser.new_page(viewport={'width': shot['w'], 'height': shot['h']})
                    try:
                        page.goto(BASE_URL + shot['query'].lstrip('/'), wait_until='load', timeout=30000)
                        page.wait_for_function('window.__shotReady === true', timeout=30000)
                        target = output_dir / shot['name']
                        page.screenshot(path=str(target), type='jpeg', quality=82)
                        with Image.open(target) as image:
                            if max(image.size) > 1280:
                                scale = 1280 / max(image.size)
                                image.resize(
                                    (round(image.width * scale), round(image.height * scale)),
                                    Image.Resampling.LANCZOS,
                                ).save(target, format='JPEG', quality=78, optimize=True)
                        if target.stat().st_size > 240000:
                            quality = 74
                            while target.stat().st_size > 262144 and quality >= 20:
                                with Image.open(target) as image:
                                    image.convert('RGB').save(
                                        target, format='JPEG', quality=quality, optimize=True
                                    )
                                quality -= 6
                        if target.stat().st_size > 262144:
                            raise RuntimeError(
                                f'{target.name} exceeds 262144 bytes after recompression '
                                f'({target.stat().st_size} bytes)'
                            )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()

    for shot in shots:
        path = output_dir / shot['name']
        with Image.open(path) as image:
            print(f'{path.name}: {image.width}x{image.height}, {path.stat().st_size} bytes')


if __name__ == '__main__':
    main()
