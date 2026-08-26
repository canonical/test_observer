// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import adapter from "@sveltejs/adapter-static";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

function isRootPath(path: unknown): asserts path is "/${string}" {
  if (typeof path === "string" && path.startsWith("/")) {
    return;
  }
  throw new Error("Specified path is not a string or does not start with /");
}

const BASE_PATH = process.env.BASE_PATH ?? "/wip";
isRootPath(BASE_PATH);

export default defineConfig({
  plugins: [
    sveltekit({
      compilerOptions: {
        // Force runes mode for the project, except for libraries. Can be removed in svelte 6.
        runes: ({ filename }) =>
          filename.split(/[/\\]/).includes("node_modules") ? undefined : true,
      },
      adapter: adapter({
        pages: "build",
        assets: "build",
        precompress: false,
        strict: true,
        fallback: "200.html",
      }),
      paths: {
        base: BASE_PATH,
      },
    }),
  ],
});
