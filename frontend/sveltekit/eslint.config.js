// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import js from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import prettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  globalIgnores([
    ".svelte-kit/",
    "build/",
    "node_modules/",
    "static/",
    "package-lock.json",
  ]),
  js.configs.recommended,
  tseslint.configs.strictTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  ...svelte.configs["flat/recommended"],
  prettier,
  ...svelte.configs["flat/prettier"],
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
        extraFileExtensions: [".svelte"],
      },
    },
    linterOptions: {
      reportUnusedDisableDirectives: "error",
    },
    rules: {
      "no-console": ["error", { allow: ["warn", "error"] }],
      eqeqeq: ["error", "always"],
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/restrict-template-expressions": [
        "error",
        { allowNumber: true },
      ],
      "@typescript-eslint/switch-exhaustiveness-check": [
        "error",
        { considerDefaultExhaustiveForUnions: true },
      ],
    },
  },
  {
    files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        // No svelte.config.js exists; Svelte options live in vite.config.ts.
        svelteConfig: { compilerOptions: { runes: true } },
      },
    },
  },
  {
    // TypeScript cannot resolve SvelteKit's generated `./$types` inside .svelte
    // components, so type-aware rules report false positives there. Type safety
    // for components is covered by `svelte-check` instead.
    files: ["**/*.svelte"],
    extends: [tseslint.configs.disableTypeChecked],
  },
  {
    files: ["*.config.{js,ts}"],
    languageOptions: {
      globals: globals.node,
    },
  },
  {
    // Not covered by tsconfig.json, so type-aware rules have no program to use.
    files: ["eslint.config.js"],
    extends: [tseslint.configs.disableTypeChecked],
  },
);
