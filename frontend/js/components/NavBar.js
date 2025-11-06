import { ARTEFACT_TYPES } from '../config.js';

export class NavBar {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentPath = window.location.pathname;
  }

  render() {
    const navBarHTML = `
      <nav class="p-navigation is-dark">
        <div class="p-navigation__row">
          <div class="p-navigation__banner">
            <div class="p-navigation__tagged-logo">
              <a class="p-navigation__link" href="/">
                <div class="p-navigation__logo-tag">
                  <img class="p-navigation__logo-icon" src="https://assets.ubuntu.com/v1/82818827-CoF_white.svg" alt="Canonical" width="30">
                </div>
                <span class="p-navigation__logo-title">Test Observer</span>
              </a>
            </div>
          </div>
          <nav class="p-navigation__nav" aria-label="Main navigation">
            <ul class="p-navigation__items">
              ${this._renderArtefactTypeLinks()}
              <li class="p-navigation__item--dropdown-toggle" id="help-menu-toggle">
                <a class="p-navigation__link" href="#" aria-controls="help-menu">Help</a>
                <ul class="p-navigation__dropdown" id="help-menu" aria-hidden="true">
                  <li><a href="https://canonical-test-observer.readthedocs-hosted.com/en/latest/" target="_blank">Docs</a></li>
                  <li><a href="https://github.com/canonical/test_observer/issues" target="_blank">Feedback</a></li>
                  <li><a href="https://github.com/canonical/test_observer" target="_blank">Source Code</a></li>
                </ul>
              </li>
              <li class="p-navigation__item">
                <a class="p-navigation__link" href="/test-results">Test Results</a>
              </li>
              <li class="p-navigation__item">
                <a class="p-navigation__link" href="/issues">Issues</a>
              </li>
            </ul>
          </nav>
        </div>
      </nav>
    `;

    this.container.innerHTML = navBarHTML;
    this._highlightActiveLink();
    this._initializeVanillaDropdowns();
  }

  _renderArtefactTypeLinks() {
    return ARTEFACT_TYPES.map(type => {
      const title = `${type.charAt(0).toUpperCase() + type.slice(1)} Testing`;
      const route = `/${type}s`;
      return `<li class="p-navigation__item"><a class="p-navigation__link" href="${route}">${title}</a></li>`;
    }).join('');
  }

  _highlightActiveLink() {
    const links = this.container.querySelectorAll('.p-navigation__link');
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (href && href !== '#' && window.location.pathname.startsWith(href)) {
        link.classList.add('is-selected');
      }
    });
  }

  _initializeVanillaDropdowns() {
    // Use Vanilla Framework's dropdown pattern
    const dropdownToggles = this.container.querySelectorAll('.p-navigation__item--dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
      const link = toggle.querySelector('.p-navigation__link');
      const dropdown = toggle.querySelector('.p-navigation__dropdown');
      
      if (link && dropdown) {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          const isHidden = dropdown.getAttribute('aria-hidden') === 'true';
          
          // Close all other dropdowns first
          this.container.querySelectorAll('.p-navigation__dropdown').forEach(d => {
            if (d !== dropdown) {
              d.setAttribute('aria-hidden', 'true');
            }
          });
          
          // Toggle current dropdown
          dropdown.setAttribute('aria-hidden', !isHidden);
        });
      }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.container.contains(e.target)) {
        this.container.querySelectorAll('.p-navigation__dropdown').forEach(dropdown => {
          dropdown.setAttribute('aria-hidden', 'true');
        });
      }
    });
  }
}
