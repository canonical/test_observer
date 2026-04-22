#!/usr/bin/env node
/**
 * QA Agent Screenshot Tool
 * ========================
 * Opens a URL in a headless Chromium browser, waits for the page to fully render,
 * and saves a screenshot. Intended for use by the QA/Judge agent to capture the
 * current state of the Flutter UI (port 30001) or the candidate rewrite for comparison.
 *
 * By default, authenticates via SSO (SimpleSAML) before loading the target URL,
 * so the screenshot is captured in a logged-in state. Pass --no-login to skip SSO
 * and capture the unauthenticated view instead.
 *
 * SSO login flow (default):
 *   1. Hit the backend SAML initiation URL with the target URL as return_to.
 *   2. Fill credentials on the SimpleSAML HTML form and submit.
 *   3. The IdP redirects back through the backend to the target UI.
 *   4. If the target URL has a hash fragment (e.g. /#/snaps/1), navigate there
 *      in a second step — hash fragments are stripped during the SAML redirect
 *      because the server never sees them.
 *   5. Wait for render, then take the screenshot.
 *
 * Prerequisites:
 *   sudo apt-get install node-playwright
 *   npx --yes playwright@1.38.0 install chromium   # one-time browser download
 *
 * Usage:
 *   node screenshot.mjs [URL] [OUTPUT_PATH] [OPTIONS]
 *
 * Examples:
 *   node screenshot.mjs http://localhost:30001/ /tmp/flutter-home.png
 *   node screenshot.mjs http://localhost:30001/ /tmp/flutter-home.png --no-login
 *   node screenshot.mjs http://localhost:30001/svelte_poc/snaps /tmp/svelte-home.png --width 1440 --height 900
 *
 * Options:
 *   --no-login    Skip SSO login; screenshot the unauthenticated page
 *   --api-url URL Backend API base URL for SSO initiation (default: http://localhost:30000/)
 *   --username U  SSO username (default: certbot)
 *   --password P  SSO password (default: password)
 *   --width N     Viewport width in pixels (default: 1280)
 *   --height N    Viewport height in pixels (default: 900)
 *   --wait N      Extra ms to wait after render (default: 3000)
 *   --full-page   Capture the full scrollable page, not just the viewport
 */

const { chromium } = require('playwright');
const { mkdirSync } = require('node:fs');
const { dirname, resolve } = require('node:path');
const { parseArgs } = require('node:util');

// ── Argument parsing ────────────────────────────────────────────────────────

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    'no-login':  { type: 'boolean', default: false },
    'api-url':   { type: 'string',  default: 'http://localhost:30000/' },
    'username':  { type: 'string',  default: 'certbot' },
    'password':  { type: 'string',  default: 'password' },
    'width':     { type: 'string',  default: '1280' },
    'height':    { type: 'string',  default: '900' },
    'wait':      { type: 'string',  default: '3000' },
    'full-page': { type: 'boolean', default: false },
  },
});

const url       = positionals[0] || 'http://localhost:30001/';
const output    = resolve(positionals[1] || '/tmp/screenshot.png');
const width     = parseInt(values.width, 10);
const height    = parseInt(values.height, 10);
const waitMs    = parseInt(values.wait, 10);
const fullPage  = values['full-page'];
const login     = !values['no-login'];
const apiUrl    = values['api-url'].replace(/\/+$/, '');
const username  = values.username;
const password  = values.password;

// ── Proxy helpers ───────────────────────────────────────────────────────────

function proxyConfig() {
  const proxyUrl = process.env.HTTPS_PROXY || process.env.https_proxy
                || process.env.HTTP_PROXY  || process.env.http_proxy;
  return proxyUrl || null;
}

// ── Work around rimraf bug in Ubuntu's node-playwright 1.38 package ─────────
// The system package ships a rimraf that requires a callback, but playwright
// calls it without one, causing an uncaught assertion on browser.close().
// We swallow that specific error so the process exits cleanly.
process.on('uncaughtException', (err) => {
  if (err && err.code === 'ERR_ASSERTION' && err.message && err.message.includes('rimraf')) {
    // Harmless cleanup error — ignore it.
    return;
  }
  console.error(err);
  process.exit(1);
});

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  mkdirSync(dirname(output), { recursive: true });

  console.log(`Opening: ${url}`);
  console.log(`Viewport: ${width}x${height} | Wait: ${waitMs}ms | Full page: ${fullPage} | Login: ${login}`);

  // Configure proxy at the Chromium flag level (not Playwright's proxy option,
  // which intercepts localhost traffic). The bypass list ensures localhost
  // targets are fetched directly while external CDNs go through the proxy.
  const proxyUrl = proxyConfig();
  const proxyArgs = proxyUrl
    ? [`--proxy-server=${proxyUrl}`, '--proxy-bypass-list=localhost;127.0.0.1;::1']
    : [];

  const launchOptions = {
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      ...proxyArgs,
    ],
  };

  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width, height } });

  try {
    if (login) {
      // ── Determine login return target ───────────────────────────────────
      // Hash fragments (#/snaps/1) are never sent to the server, so the SAML
      // redirect will lose them. We handle this by:
      //   a) Using the origin (no hash) as the return_to for SSO.
      //   b) After login succeeds, navigating to the full target URL (with hash).
      const parsed = new URL(url);
      const returnTo = parsed.hash
        ? `${parsed.origin}${parsed.pathname}${parsed.search}`  // strip hash
        : url;

      // ── 1. Initiate SAML login ─────────────────────────────────────────
      const loginUrl = `${apiUrl}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      console.log(`SSO login: ${loginUrl}`);
      await page.goto(loginUrl, { waitUntil: 'domcontentloaded', timeout: 15_000 });

      // ── 2. Fill credentials and submit ──────────────────────────────────
      await page.waitForSelector('input[name="username"]', { timeout: 10_000 });
      console.log('  Filling credentials...');
      await page.fill('input[name="username"]', username);
      await page.fill('input[name="password"]', password);
      await page.keyboard.press('Enter');
      console.log('  Submitted, waiting for redirect...');

      // ── 3. Wait for redirect back to the target UI ──────────────────────
      try {
        await page.waitForURL(`**localhost:30001**`, { timeout: 30_000 });
      } catch {
        await page.waitForLoadState('load', { timeout: 15_000 }).catch(() => {});
      }
      console.log(`  Landed at: ${page.url()}`);

      try {
        await page.waitForLoadState('networkidle', { timeout: 30_000 });
      } catch {
        // networkidle may not fire for long-polling apps — continue anyway
      }

      // ── 4. If the target URL had a hash, navigate there now ─────────────
      // The session cookie is set, so this second navigation is authenticated.
      if (parsed.hash) {
        console.log(`  Navigating to hash target: ${url}`);
        await page.goto(url, { waitUntil: 'load', timeout: 15_000 });
        try {
          await page.waitForLoadState('networkidle', { timeout: 15_000 });
        } catch { /* continue */ }
      }
    } else {
      try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30_000 });
      } catch {
        console.warn('WARNING: Network idle timeout — taking screenshot of current state.');
      }
    }

    // Extra wait for JS frameworks (Flutter/Svelte) that animate on load
    if (waitMs > 0) {
      await page.waitForTimeout(waitMs);
    }

    await page.screenshot({ path: output, fullPage: fullPage });
    console.log(`Screenshot saved: ${output}`);

  } finally {
    await browser.close();
  }
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
