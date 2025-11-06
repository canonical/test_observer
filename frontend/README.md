# Test Observer Frontend

The frontend of Test Observer is a web application developed with Vanilla JavaScript (ES6+ modules), HTML, and CSS using the [Vanilla Framework](https://vanillaframework.io/).

## Architecture

- **HTML**: Single page application structure in `index.html`
- **CSS**: [Vanilla Framework](https://vanillaframework.io/) compiled from SCSS
- **JavaScript**: ES6+ modules with components in `js/components/`
- **Configuration**: Centralized configuration in `js/config.js`
- **Build Tools**: npm with SASS for CSS compilation

## Setup

Install dependencies:

```bash
cd frontend
npm install
```

Build the CSS:

```bash
npm run build
```

This compiles the SCSS files from `sass/` into optimized CSS in `css/`.

## Development

### Build CSS

```bash
npm run build-css
```

### Watch for Changes

For development, you can watch for SCSS changes and automatically recompile:

```bash
npm run watch-css
```

### Serve Locally

To run the frontend locally, serve the directory with any HTTP server:

```bash
# Using Python's built-in server
python3 -m http.server 8080

# Or using Node's http-server (if installed)
npx http-server -p 8080

# Or using PHP's built-in server
php -S localhost:8080
```

Then open your browser to `http://localhost:8080`

**Note**: The frontend uses ES6 modules, so you need to serve it via HTTP (not file://) for the modules to work.

## Project Structure

```
frontend/
├── index.html              # Main HTML shell
├── package.json            # Dependencies and build scripts
├── sass/
│   └── styles.scss        # Main SCSS file (imports Vanilla Framework)
├── css/                    # Compiled CSS (generated, not in git)
│   └── styles.css         # Compiled from SCSS
├── js/
│   ├── app.js             # Main application entry point
│   ├── config.js          # Configuration (API URL, artefact types, etc.)
│   └── components/
│       └── NavBar.js      # Navigation bar component
├── Dockerfile              # Production Docker image
└── nginx.conf              # Nginx configuration
```

## Vanilla Framework

This project uses [Vanilla Framework](https://vanillaframework.io/) - Ubuntu's CSS framework. The framework is installed via npm and compiled from SCSS, following the recommended setup:

- **Installation**: `npm install vanilla-framework`
- **Compilation**: SCSS files import Vanilla Framework and compile to CSS
- **Build tool**: SASS with load-path to node_modules
- **Customization**: Add custom styles in `sass/styles.scss` after importing Vanilla Framework

This approach provides:
- Full Vanilla Framework features and components
- Ability to customize and extend styles
- Optimized, compressed CSS output
- Source maps for debugging

### Adding Custom Styles

Edit `sass/styles.scss` to add custom styles:

```scss
// Import Vanilla Framework
@import 'vanilla-framework';
@include vanilla;

// Your custom styles here
.my-custom-class {
  // ...
}
```

Then rebuild: `npm run build-css`

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can set `window.testObserverAPIBaseURI` before the app initializes, or modify the `API_BASE_URL` in `js/config.js`.

## Docker

The frontend is served via nginx in production. The Dockerfile includes a build step to compile CSS:

```bash
# Build the Docker image (includes CSS compilation)
docker build -t test-observer-frontend .

# Or using docker-compose
docker compose build test-observer-frontend
```

See the `Dockerfile` in this directory for the containerized setup.
