#!/home/hatch/workspace/tools/shot-venv/bin/python
"""Capture the local app scenes declared in shots.json."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
sys.path.append('/usr/lib/python3/dist-packages')
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path('/home/hatch/workspace/tools/shot-venv/bin/python')
CHROMIUM = '/home/hatch/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome'
BASE = 'http://127.0.0.1:8080/'


def wait_for_server(process):
    deadline = time.monotonic() + 20
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'node serve.ts exited with status {process.returncode}')
        try:
            with urlopen(BASE, timeout=1):
                return
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(0.2)
    raise RuntimeError(f'Server did not become ready at {BASE}: {last_error}')


def main():
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError(f'Run this script with {PYTHON}; current Python is {sys.executable}')
    shots = json.loads((ROOT / 'shots.json').read_text())
    server = subprocess.Popen(
        ['node', 'serve.ts'], cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True,
    )
    try:
        wait_for_server(server)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=CHROMIUM, headless=True,
                args=['--no-sandbox'],
            )
            try:
                page = browser.new_page()
                for shot in shots:
                    url = BASE + shot['query'].lstrip('?')
                    page.goto(url, wait_until='load', timeout=30000)
                    page.wait_for_function('window.__shotReady === true', timeout=30000)
                    target = ROOT / 'screenshots' / shot['name']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(target), type='jpeg', quality=95, full_page=True)
                    if target.stat().st_size > 250000:
                        quality = 90
                        while target.stat().st_size > 260000 and quality >= 20:
                            with Image.open(target) as image:
                                image.convert('RGB').save(target, format='JPEG', quality=quality, optimize=True)
                            quality -= 5
                        if target.stat().st_size > 260000:
                            raise RuntimeError(f'{target.name} remains over 260000 bytes after recompression')
            finally:
                browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        if server.stdout:
            output = server.stdout.read()
            if output:
                print(output, end='', file=sys.stderr)

    for shot in shots:
        path = ROOT / 'screenshots' / shot['name']
        print(f'{path.name}: {path.stat().st_size} bytes')


if __name__ == '__main__':
    main()
