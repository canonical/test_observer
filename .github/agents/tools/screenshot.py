#!/usr/bin/env python3
"""
QA Agent Screenshot Tool
========================
Opens a URL in a headless Chromium browser, waits for the page to fully render,
and saves a screenshot. Intended for use by the QA/Judge agent to capture the
current state of the Flutter UI (port 30001) or the future Vue UI for comparison.

Usage:
    python3 screenshot.py [URL] [OUTPUT_PATH] [--width W] [--height H] [--wait MS]

Examples:
    python3 screenshot.py http://localhost:30001/ /tmp/flutter-home.png
    python3 screenshot.py http://localhost:30001/snaps /tmp/flutter-snaps.png --wait 3000
    python3 screenshot.py http://localhost:5173/ /tmp/vue-home.png --width 1440 --height 900

Arguments:
    URL           Page to capture (default: http://localhost:30001/)
    OUTPUT_PATH   Where to save the PNG (default: /tmp/screenshot.png)
    --width       Viewport width in pixels (default: 1280)
    --height      Viewport height in pixels (default: 900)
    --wait        Extra ms to wait after network idle, for JS-heavy renders (default: 1000)
    --full-page   Capture the full scrollable page, not just the viewport
"""

import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of a web page using headless Chromium."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="http://localhost:30001/",
        help="URL to screenshot (default: http://localhost:30001/)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="/tmp/screenshot.png",
        help="Output PNG file path (default: /tmp/screenshot.png)",
    )
    parser.add_argument(
        "--width", type=int, default=1280, help="Viewport width (default: 1280)"
    )
    parser.add_argument(
        "--height", type=int, default=900, help="Viewport height (default: 900)"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=1000,
        help="Extra ms to wait after network idle (default: 1000)",
    )
    parser.add_argument(
        "--full-page",
        action="store_true",
        help="Capture the full scrollable page height",
    )
    return parser.parse_args()


def take_screenshot(url: str, output: str, width: int, height: int, wait_ms: int, full_page: bool):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        print("ERROR: Playwright not installed. Run:", file=sys.stderr)
        print("  ~/.agent-tools-venv/bin/pip install playwright", file=sys.stderr)
        print("  ~/.agent-tools-venv/bin/python -m playwright install chromium", file=sys.stderr)
        sys.exit(1)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Opening: {url}")
    print(f"Viewport: {width}x{height} | Wait: {wait_ms}ms | Full page: {full_page}")

    with sync_playwright() as p:
        import os
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
                    or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        # Route external traffic through the system proxy but keep localhost direct.
        proxy_config = {"server": proxy_url, "bypass": "localhost,127.0.0.1"} if proxy_url else None
        page = browser.new_page(
            viewport={"width": width, "height": height},
            proxy=proxy_config,
        )

        try:
            # Wait until network is idle (no requests for 500ms) or 30s timeout
            page.goto(url, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            print("WARNING: Network idle timeout reached — taking screenshot of current state.")

        # Extra wait for JS frameworks (Flutter/Vue) that animate on load
        if wait_ms > 0:
            page.wait_for_timeout(wait_ms)

        page.screenshot(path=str(output_path), full_page=full_page)
        browser.close()

    print(f"Screenshot saved: {output_path.resolve()}")


def main():
    args = parse_args()
    take_screenshot(
        url=args.url,
        output=args.output,
        width=args.width,
        height=args.height,
        wait_ms=args.wait,
        full_page=args.full_page,
    )


if __name__ == "__main__":
    main()
