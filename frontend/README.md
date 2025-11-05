# Test Observer Frontend

A modern web frontend for Test Observer built with [Preact](https://preactjs.com/) and [Preact Signals](https://preactjs.com/guide/v10/signals/).

## Development

```bash
# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Tech Stack

- **Preact**: Fast 3kB alternative to React with the same modern API
- **Preact Signals**: Fine-grained reactivity for state management
- **Preact Router**: Declarative routing for single-page applications
- **TypeScript**: Type-safe development
- **Vite**: Lightning fast build tool and dev server

## Architecture

### State Management

The application uses Preact Signals for state management, providing a simple and performant reactive state system. Global state is managed in `src/api/store.ts`.

Key signals:
- `currentFamily` - Currently selected artefact family (snap/deb/charm/image)
- `artefacts` - Map of all loaded artefacts
- `isLoading` - Loading state indicator
- `error` - Error message if any

### API Client

API communication is handled through `src/api/client.ts`, which provides a typed wrapper around the fetch API with automatic JSON handling and error management.

### Project Structure

```
src/
├── api/           # API client and global state management
├── components/    # Reusable UI components
├── models/        # TypeScript type definitions
├── pages/         # Page components (routed views)
├── hooks/         # Custom Preact hooks
├── utils/         # Utility functions
└── constants/     # Application constants
```

## Building for Production

The production build is optimized and served through nginx:

```bash
docker build -t test-observer-frontend .
docker run -p 80:80 test-observer-frontend
```

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE) file for details.
