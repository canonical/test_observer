#!/usr/bin/env python3
"""
QA Agent Login + Screenshot Tool
===================================
Authenticates into the Test Observer UI via SSO (SimpleSAML) and captures
a screenshot of the logged-in state.

Login flow:
  1. Hit the backend SAML initiation URL directly (no Flutter pre-load needed).
  2. SimpleSAML redirects to the IdP login form — fill credentials and submit.
  3. The IdP redirects back through the backend, which redirects to the Flutter UI.
  4. Wait for Flutter to render, then take the screenshot.

Usage:
    python3 login_screenshot.py [URL] [OUTPUT] [options]

Options:
    URL              Base URL of the Flutter UI (default: http://localhost:30001/)
    OUTPUT           Output PNG path (default: /tmp/flutter-loggedin.png)
    --api-url        Base URL of the backend API (default: http://localhost:30000/)
    --username       SSO username (default: certbot)
    --password       SSO password (default: password)
    --wait           Extra ms to wait after Flutter finishes rendering (default: 3000)

Examples:
    python3 login_screenshot.py
    python3 login_screenshot.py http://localhost:30001/ /tmp/logged-in.png
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


def login_and_screenshot(
    base_url: str,
    api_url: str,
    output: str,
    username: str,
    password: str,
    wait_ms: int,
):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed.", file=sys.stderr)
        sys.exit(1)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proxy_config = _proxy_config()

    with sync_playwright() as p:
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
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # ── 1. Initiate SAML login via the backend ───────────────────────────
        login_url = f"{api_url.rstrip('/')}/v1/auth/saml/login?return_to={base_url}"
        print(f"Navigating to SSO login: {login_url}")
        page.goto(login_url, wait_until="domcontentloaded", timeout=15000)

        # ── 2. Fill in credentials on the standard HTML SSO form ────────────
        print(f"Filling credentials (username={username}) ...")
        page.wait_for_selector('input[name="username"]', timeout=10000)
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # ── 3. Submit the form ───────────────────────────────────────────────
        print("Submitting SSO form ...")
        page.keyboard.press("Enter")

        # ── 4. Wait for redirect back to the Flutter UI ──────────────────────
        print("Waiting for redirect back to Flutter UI ...")
        page.wait_for_url(f"**{base_url.rstrip('/')}**", timeout=15000)
        print(f"  Redirected to: {page.url}")

        # ── 5. Wait for Flutter to fully render ──────────────────────────────
        print(f"Waiting {wait_ms}ms for Flutter to render ...")
        page.wait_for_timeout(wait_ms)

        # ── 6. Take screenshot ──────────────────────────────────────────────
        page.screenshot(path=str(output_path))
        size = output_path.stat().st_size
        print(f"Screenshot saved: {output_path.resolve()} ({size // 1024}KB)")

        browser.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Log into Test Observer via SSO and take a screenshot."
    )
    parser.add_argument("url", nargs="?", default="http://localhost:30001/")
    parser.add_argument("output", nargs="?", default="/tmp/flutter-loggedin.png")
    parser.add_argument("--api-url", default="http://localhost:30000/", help="Backend API base URL")
    parser.add_argument("--username", default="certbot")
    parser.add_argument("--password", default="password")
    parser.add_argument("--wait", type=int, default=3000, help="ms to wait after login render")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    login_and_screenshot(
        base_url=args.url,
        api_url=args.api_url,
        output=args.output,
        username=args.username,
        password=args.password,
        wait_ms=args.wait,
    )
