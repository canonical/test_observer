# Test Observer - React PoC

This is a React proof-of-concept version of the Test Observer frontend, demonstrating how the UI could be implemented using React instead of Flutter or Vue.js.

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Architecture

This React PoC uses:
- **React 18** with functional components and hooks
- **React Router 6** for client-side routing
- **Vite** for fast development and optimized builds
- **Vanilla CSS** for styling (matching the Vue PoC approach)

## Deployment

The application is configured to be served from `/react_poc/` base path when deployed in the Docker container alongside the Flutter UI and Vue PoC.
