import { NavBar } from './components/NavBar.js';

class App {
  constructor() {
    this.navBar = new NavBar('navigation-bar');
  }

  init() {
    // Initialize the navigation bar
    this.navBar.render();
    
    // Initialize other components as they are added in future PRs
    this._renderEmptyContent();
  }

  _renderEmptyContent() {
    const appContent = document.getElementById('app-content');
    if (appContent) {
      appContent.innerHTML = `
        <div class="p-strip">
          <div class="row">
            <div class="col-12">
              <h1>Test Observer</h1>
              <p>Content area - to be implemented in future PRs</p>
            </div>
          </div>
        </div>
      `;
    }
  }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
