#!/usr/bin/env python3
"""
QA Agent Screenshot Tool
========================
Opens a URL in a headless Chromium browser, waits for the page to fully render,
and saves a screenshot. Intended for use by the QA/Judge agent to capture the
current state of the Flutter UI (port 30001) or the future Vue UI for comparison.

By default, authenticates via SSO (SimpleSAML) before loading the target URL,
so the screenshot is captured in a logged-in state. Pass --no-login to skip SSO
and capture the unauthenticated view instead.

SSO login flow (default):
  1. Hit the backend SAML initiation URL with the target URL as return_to.
  2. Fill credentials on the SimpleSAML HTML form and submit.
  3. The IdP redirects back through the backend to the Flutter UI.
  4. Wait for render, then take the screenshot.

Usage:
    python3 screenshot.py [URL] [OUTPUT_PATH] [--width W] [--height H] [--wait MS]

Examples:
    python3 screenshot.py http://localhost:30001/ /tmp/flutter-home.png
    python3 screenshot.py http://localhost:30001/ /tmp/flutter-home.png --no-login
    python3 screenshot.py http://localhost:5173/ /tmp/vue-home.png --width 1440 --height 900

Arguments:
    URL           Page to capture (default: http://localhost:30001/)
    OUTPUT_PATH   Where to save the PNG (default: /tmp/screenshot.png)
    --no-login    Skip SSO login; screenshot the unauthenticated page
    --api-url     Backend API base URL for SSO initiation (default: http://localhost:30000/)
    --username    SSO username (default: certbot)
    --password    SSO password (default: password)
    --width       Viewport width in pixels (default: 1280)
    --height      Viewport height in pixels (default: 900)
    --wait        Extra ms to wait after render (default: 3000)
    --full-page   Capture the full scrollable page, not just the viewport
"""

import argparse
import os
import sys
from pathlib import Path


def _proxy_config():
    proxy_url = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    return {"server": proxy_url, "bypass": "localhost,127.0.0.1"} if proxy_url else None


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
        default=3000,
        help="Extra ms to wait after render (default: 3000)",
    )
    parser.add_argument(
        "--full-page",
        action="store_true",
        help="Capture the full scrollable page height",
    )
    parser.add_argument(
        "--no-login",
        action="store_true",
        help="Skip SSO login and screenshot the unauthenticated page",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:30000/",
        help="Backend API base URL for SSO (default: http://localhost:30000/)",
    )
    parser.add_argument("--username", default="certbot", help="SSO username (default: certbot)")
    parser.add_argument("--password", default="password", help="SSO password (default: password)")
    return parser.parse_args()


def take_screenshot(
    url: str,
    output: str,
    width: int,
    height: int,
    wait_ms: int,
    full_page: bool,
    login: bool = True,
    api_url: str = "http://localhost:30000/",
    username: str = "certbot",
    password: str = "password",
):
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
    print(f"Viewport: {width}x{height} | Wait: {wait_ms}ms | Full page: {full_page} | Login: {login}")

    proxy_config = _proxy_config()
    launch_kwargs: dict = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            # Ensure localhost is never routed through the corporate proxy,
            # regardless of HTTP_PROXY / HTTPS_PROXY env vars.
            "--proxy-bypass-list=localhost,127.0.0.1,::1",
        ],
    }
    if proxy_config:
        launch_kwargs["proxy"] = proxy_config

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": width, "height": height})

        if login:
            # ── 1. Initiate SAML login, with the target URL as return_to ────
            login_url = f"{api_url.rstrip('/')}/v1/auth/saml/login?return_to={url}"
            print(f"SSO login: {login_url}")
            page.goto(login_url, wait_until="domcontentloaded", timeout=15000)

            # ── 2. Fill credentials and submit ───────────────────────────────
            page.wait_for_selector('input[name="username"]', timeout=10000)
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.keyboard.press("Enter")

            # ── 3. Wait for redirect back to the Flutter UI ──────────────────
            page.wait_for_url(f"**{url.rstrip('/')}**", timeout=15000)
            print(f"  Redirected to: {page.url}")
            # Wait for Flutter/CanvasKit assets to finish loading before the
            # extra wait_ms render delay starts.
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except PlaywrightTimeout:
                pass
        else:
            try:
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
        login=not args.no_login,
        api_url=args.api_url,
        username=args.username,
        password=args.password,
    )


if __name__ == "__main__":
    main()
