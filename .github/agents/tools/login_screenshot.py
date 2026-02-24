#!/usr/bin/env python3
"""
QA Agent Login + Screenshot Tool
===================================
Authenticates into the Test Observer UI via SSO (SimpleSAML) and captures
a screenshot of the logged-in state. Since the frontend is Flutter Web
(CanvasKit renderer), interaction uses a combination of:
  - Keyboard events (Escape to dismiss dialogs)
  - Flutter's accessibility semantics tree (flt-semantics elements) for
    button discovery via aria-label
  - Coordinate-based mouse clicks derived from bounding rects

Usage:
    python3 login_screenshot.py [URL] [OUTPUT] [options]

Options:
    URL              Base URL of the Flutter UI (default: http://localhost:30001/)
    OUTPUT           Output PNG path (default: /tmp/flutter-loggedin.png)
    --username       SSO username (default: certbot)
    --password       SSO password (default: password)
    --route          Hash route to navigate to after login (default: none, stays on redirect)
    --wait           Extra ms to wait after Flutter finishes rendering (default: 3000)

Examples:
    python3 login_screenshot.py
    python3 login_screenshot.py http://localhost:30001/ /tmp/logged-in.png
    python3 login_screenshot.py http://localhost:30001/ /tmp/snaps.png --route "#/snaps"
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


def _activate_flutter_semantics(page) -> bool:
    """
    Flutter Web (CanvasKit) hides its accessibility/semantics tree until the
    user explicitly enables it. We trigger this by firing a click MouseEvent
    directly on the flt-semantics-placeholder (bypassing Playwright's
    viewport check, since the element is intentionally 1x1 at -1,-1).
    Returns True if semantics were successfully activated.
    """
    activated = page.evaluate("""() => {
        const el = document.querySelector('flt-semantics-placeholder');
        if (!el) return false;
        el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        return true;
    }""")
    if activated:
        page.wait_for_timeout(1500)
    return activated


def _find_flutter_button(page, label_substring: str) -> dict | None:
    """
    Search Flutter's semantics tree (flt-semantics elements) for a node whose
    aria-label contains label_substring (case-insensitive).
    Returns {x, y, w, h, label} of the first visible match, or None.
    """
    result = page.evaluate(f"""() => {{
        const needle = {repr(label_substring.lower())};
        const candidates = Array.from(
            document.querySelectorAll('flt-semantics[aria-label], flt-semantics[role="button"]')
        );
        for (const el of candidates) {{
            const lbl = (el.getAttribute('aria-label') || '').toLowerCase();
            if (lbl.includes(needle)) {{
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {{
                    return {{x: r.x, y: r.y, w: r.width, h: r.height, label: el.getAttribute('aria-label')}};
                }}
            }}
        }}
        return null;
    }}""")
    return result


def _click_flutter_button(page, label_substring: str, timeout_ms: int = 10000) -> bool:
    """
    Wait for a Flutter semantics button matching label_substring to appear,
    then click its centre via page.mouse. Returns True on success.
    """
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    while True:
        btn = _find_flutter_button(page, label_substring)
        if btn:
            cx = btn["x"] + btn["w"] / 2
            cy = btn["y"] + btn["h"] / 2
            print(f"  Found '{btn['label']}' at ({cx:.0f}, {cy:.0f}) — clicking")
            page.mouse.click(cx, cy)
            return True
        remaining = deadline - page.evaluate("() => Date.now()")
        if remaining <= 0:
            print(f"  WARNING: Button matching '{label_substring}' not found in semantics tree.")
            return False
        page.wait_for_timeout(300)


def login_and_screenshot(
    base_url: str,
    output: str,
    username: str,
    password: str,
    route: str,
    wait_ms: int,
):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
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

        # ── 1. Load the Flutter UI ──────────────────────────────────────────
        print(f"Loading {base_url} ...")
        try:
            page.goto(base_url, wait_until="networkidle", timeout=30000)
        except PWTimeout:
            print("  (networkidle timeout — continuing)")
        page.wait_for_timeout(5000)
        print(f"  Landed on: {page.url}")

        # ── 2. Dismiss the 'Insufficient permissions' error dialog ──────────
        print("Pressing Escape to dismiss any error dialog ...")
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)

        # ── 3. Navigate directly to the SSO login URL ────────────────────────
        # The Flutter 'Log in' button simply navigates to:
        #   {apiUrl}/v1/auth/saml/login?return_to={currentUrl}
        # Driving it directly is more reliable than hunting for it via the
        # Flutter semantics tree (it's a custom widget with no aria-label).
        api_base = page.evaluate("() => window.testObserverAPIBaseURI || 'http://localhost:30000/'")
        return_to = page.url or base_url
        login_url = f"{api_base.rstrip('/')}/v1/auth/saml/login?return_to={return_to}"
        print(f"Navigating to SSO login: {login_url}")
        page.goto(login_url, wait_until="domcontentloaded", timeout=15000)

        # ── 4. Fill in credentials on the standard HTML SSO form ────────────
        print(f"Filling credentials (username={username}) ...")
        page.wait_for_selector('input[name="username"]', timeout=10000)
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # ── 5. Submit the form ───────────────────────────────────────────────
        print("Submitting SSO form ...")
        page.keyboard.press("Enter")

        # ── 6. Wait for redirect back to the Flutter UI ──────────────────────
        print("Waiting for redirect back to Flutter UI ...")
        try:
            page.wait_for_url(f"**{base_url.rstrip('/')}**", timeout=15000)
        except PWTimeout:
            pass
        print(f"  Redirected to: {page.url}")

        # Verify we are back on the right host
        if base_url.split("//")[1].split("/")[0] not in page.url:
            print(f"  WARNING: Unexpected URL after SSO: {page.url}")

        # ── 7. Optionally navigate to a specific route ───────────────────────
        if route:
            target = base_url.rstrip("/") + "/" + route.lstrip("/")
            print(f"Navigating to route: {target}")
            page.goto(target, wait_until="networkidle", timeout=20000)

        # ── 8. Wait for Flutter to fully render ─────────────────────────────
        print(f"Waiting {wait_ms}ms for Flutter to render ...")
        page.wait_for_timeout(wait_ms)

        # ── 9. Take screenshot ──────────────────────────────────────────────
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
    parser.add_argument("--username", default="certbot")
    parser.add_argument("--password", default="password")
    parser.add_argument("--route", default="", help="Hash route after login, e.g. '#/snaps'")
    parser.add_argument("--wait", type=int, default=3000, help="ms to wait after login render")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    login_and_screenshot(
        base_url=args.url,
        output=args.output,
        username=args.username,
        password=args.password,
        route=args.route,
        wait_ms=args.wait,
    )
