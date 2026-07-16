// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// BASE_PATH is set at build time via environment variable (e.g. BASE_PATH=/wip).
// To change the web root, update the Dockerfile ENV BASE_PATH=... line.
const BASE_PATH = process.env.BASE_PATH ?? '/wip';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html'
    }),
    paths: {
      base: BASE_PATH
    }
  }
};

export default config;
