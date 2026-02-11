# Test Observer - Svelte PoC

This is a Svelte proof-of-concept (PoC) rewrite of the Test Observer frontend, intended for comparison with the Vue.js and React implementations.

## Features

- Dashboard views for different artefact types (snaps, debs, charms, images)
- Artefact detail pages with test execution information
- Test results search functionality
- Issues tracking and management
- User authentication via SAML

## Development

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Project Structure

- `src/` - Source code
  - `components/` - Reusable Svelte components
  - `views/` - Page-level components
  - `services/` - API and utility services
  - `App.svelte` - Root component
  - `main.js` - Application entry point

## Deployment

The application is configured to be served from `/svelte_poc/` path when deployed. The production build output is placed in the `dist/` directory and should be served by nginx alongside the main Flutter UI and other PoC implementations.
