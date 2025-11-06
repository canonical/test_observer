# Test Observer Frontend

The frontend of Test Observer is a web application developed with Vanilla JavaScript (ES6+ modules), HTML, and CSS using the Vanilla Framework.

## Architecture

- **HTML**: Single page application structure in `index.html`
- **CSS**: Vanilla Framework with custom styles in `css/style.css`
- **JavaScript**: ES6+ modules with components in `js/components/`
- **Configuration**: Centralized configuration in `js/config.js`

## Setup

No build tools or dependencies are required! The frontend uses native ES6 modules and runs directly in modern browsers.

## Run

To run the frontend locally, simply serve the directory with any HTTP server:

```bash
# Using Python's built-in server
python3 -m http.server 8080

# Or using Node's http-server (if installed)
npx http-server -p 8080

# Or using PHP's built-in server
php -S localhost:8080
```

Then open your browser to `http://localhost:8080`

## Development

The frontend uses ES6 modules, so you need to serve it via HTTP (not file://) for the modules to work.

### Project Structure

```
frontend/
├── index.html              # Main HTML shell
├── css/
│   └── style.css          # Custom styles and Vanilla Framework fallback
├── js/
│   ├── app.js             # Main application entry point
│   ├── config.js          # Configuration (API URL, artefact types, etc.)
│   └── components/
│       └── NavBar.js      # Navigation bar component
```

### Adding New Components

1. Create a new file in `js/components/`
2. Export your component class
3. Import and use it in `js/app.js`

Example:
```javascript
// js/components/MyComponent.js
export class MyComponent {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
  }
  
  render() {
    this.container.innerHTML = '<div>My Component</div>';
  }
}
```

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can set `window.testObserverAPIBaseURI` before the app initializes, or modify the `API_BASE_URL` in `js/config.js`.

## Docker

The frontend is served via nginx in production. See the `Dockerfile` in this directory for the containerized setup.
