# Test Observer - Vanilla JS Frontend

This is the vanilla JavaScript Single Page Application (SPA) version of Test Observer, migrated from Flutter.

## Architecture

The application follows a clean, modular architecture:

```
frontend/
├── index.html              # Main HTML file
├── css/
│   └── style.css          # Custom styles (supplements Vanilla Framework)
├── js/
│   ├── app.js             # Main app entry, routing, state management
│   ├── api.js             # API calls using fetch
│   ├── models.js          # Data model classes
│   ├── components/        # Page components
│   │   ├── DashboardPage.js
│   │   ├── ArtefactPage.js
│   │   └── ...
│   └── utils/
│       └── helpers.js     # Utility functions
```

## Features

- **Hash-based Routing**: Client-side routing using URL hash
- **Family Support**: Separate dashboards for snaps, debs, charms, and images
- **Artefact Details**: View detailed information about specific artefacts
- **Test Execution Tracking**: Display test executions, statuses, and results
- **Vanilla Framework**: Uses Vanilla CSS Framework for styling

## Running Locally

1. Start the backend API (see backend/README.md)

2. Serve the frontend with any HTTP server:
   ```bash
   cd frontend
   python3 -m http.server 8080
   ```

3. Open http://localhost:8080/index.html in your browser

## Configuration

The API base URL can be configured by setting `window.testObserverAPIBaseURI` before loading the app:

```html
<script>
  window.testObserverAPIBaseURI = 'http://your-api-url:port/';
</script>
```

Default: `http://localhost:30000/`

## Routes

- `#/snaps` - Snap artefacts dashboard
- `#/debs` - Deb artefacts dashboard
- `#/charms` - Charm artefacts dashboard
- `#/images` - Image artefacts dashboard
- `#/snaps/:id` - Specific snap artefact details (same pattern for other families)
- `#/test-results` - Test results page (coming soon)
- `#/issues` - Issues page (coming soon)

## Development

### Adding New Pages

1. Create a new component in `js/components/YourPage.js`
2. Export a function that creates and returns the page element
3. Import and add routing logic in `js/app.js`

### Adding New API Methods

1. Add the method to `js/api.js`
2. Use the `apiFetch` helper for consistent error handling
3. Return model instances from `models.js`

### Styling

- Use Vanilla Framework classes wherever possible
- Add custom styles to `css/style.css` only when necessary
- Use semantic HTML elements

## Browser Support

- Modern browsers with ES6+ module support
- Chrome, Firefox, Safari, Edge (latest versions)

## Migration Status

This is a work in progress migration from Flutter to vanilla JavaScript:

- ✅ Foundation (HTML, models, API layer)
- ✅ Routing and state management
- ✅ Dashboard page
- ✅ Artefact detail page
- 🚧 Test Results page
- 🚧 Issues page
- 🚧 Filtering and search
- 🚧 User authentication UI
