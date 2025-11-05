// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/**
 * Modal utilities using Vanilla Framework
 * Provides confirm and alert functionality using proper Vanilla Framework modals
 */

import { createElement } from './helpers.js';

/**
 * Show a confirmation modal
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {Object} options - Optional configuration
 * @param {string} options.confirmText - Text for confirm button (default: 'Confirm')
 * @param {string} options.cancelText - Text for cancel button (default: 'Cancel')
 * @param {boolean} options.isDangerous - Use negative/destructive styling (default: false)
 * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
 */
export function showConfirm(title, message, options = {}) {
  return new Promise((resolve) => {
    const {
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      isDangerous = false
    } = options;

    // Create modal container
    const modal = createElement('div', {
      className: 'p-modal',
      id: 'modal-confirm'
    });
    
    // Create modal dialog
    const dialog = createElement('div', {
      className: 'p-modal__dialog',
      role: 'dialog',
      ariaLabelledby: 'modal-title',
      ariaDescribedby: 'modal-description'
    });
    
    // Header
    const header = createElement('header', { className: 'p-modal__header' });
    header.appendChild(createElement('h2', {
      className: 'p-modal__title',
      id: 'modal-title',
      textContent: title
    }));
    
    const closeButton = createElement('button', {
      className: 'p-modal__close',
      ariaLabel: 'Close modal',
      ariaControls: 'modal-confirm',
      textContent: 'Close'
    });
    closeButton.addEventListener('click', () => {
      closeModal(modal);
      resolve(false);
    });
    header.appendChild(closeButton);
    dialog.appendChild(header);
    
    // Content
    const content = createElement('p', {
      id: 'modal-description',
      textContent: message
    });
    dialog.appendChild(content);
    
    // Footer
    const footer = createElement('footer', { className: 'p-modal__footer' });
    
    const cancelButton = createElement('button', {
      className: 'p-button--neutral',
      textContent: cancelText
    });
    cancelButton.addEventListener('click', () => {
      closeModal(modal);
      resolve(false);
    });
    footer.appendChild(cancelButton);
    
    const confirmButton = createElement('button', {
      className: isDangerous ? 'p-button--negative' : 'p-button--positive',
      textContent: confirmText
    });
    confirmButton.addEventListener('click', () => {
      closeModal(modal);
      resolve(true);
    });
    footer.appendChild(confirmButton);
    
    dialog.appendChild(footer);
    modal.appendChild(dialog);
    
    // Add to body and show
    document.body.appendChild(modal);
    
    // Handle escape key
    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeModal(modal);
        resolve(false);
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);
    
    // Focus first button after short delay
    setTimeout(() => {
      cancelButton.focus();
    }, 100);
  });
}

/**
 * Show an alert modal
 * @param {string} title - Modal title
 * @param {string} message - Modal message  
 * @param {Object} options - Optional configuration
 * @param {string} options.okText - Text for OK button (default: 'OK')
 * @param {boolean} options.isError - Use error styling (default: false)
 * @returns {Promise<void>}
 */
export function showAlert(title, message, options = {}) {
  return new Promise((resolve) => {
    const {
      okText = 'OK',
      isError = false
    } = options;

    // Create modal container
    const modal = createElement('div', {
      className: 'p-modal',
      id: 'modal-alert'
    });
    
    // Create modal dialog
    const dialog = createElement('div', {
      className: 'p-modal__dialog',
      role: 'dialog',
      ariaLabelledby: 'modal-title',
      ariaDescribedby: 'modal-description'
    });
    
    // Header
    const header = createElement('header', { className: 'p-modal__header' });
    header.appendChild(createElement('h2', {
      className: 'p-modal__title',
      id: 'modal-title',
      textContent: title
    }));
    
    const closeButton = createElement('button', {
      className: 'p-modal__close',
      ariaLabel: 'Close modal',
      ariaControls: 'modal-alert',
      textContent: 'Close'
    });
    closeButton.addEventListener('click', () => {
      closeModal(modal);
      resolve();
    });
    header.appendChild(closeButton);
    dialog.appendChild(header);
    
    // Content
    const content = createElement('p', {
      id: 'modal-description',
      textContent: message,
      style: isError ? 'color: var(--color-failed, #c7162b);' : ''
    });
    dialog.appendChild(content);
    
    // Footer
    const footer = createElement('footer', { className: 'p-modal__footer' });
    
    const okButton = createElement('button', {
      className: isError ? 'p-button--negative' : 'p-button--positive',
      textContent: okText
    });
    okButton.addEventListener('click', () => {
      closeModal(modal);
      resolve();
    });
    footer.appendChild(okButton);
    
    dialog.appendChild(footer);
    modal.appendChild(dialog);
    
    // Add to body and show
    document.body.appendChild(modal);
    
    // Handle escape key
    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeModal(modal);
        resolve();
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);
    
    // Focus OK button after short delay
    setTimeout(() => {
      okButton.focus();
    }, 100);
  });
}

/**
 * Close and remove a modal
 * @param {HTMLElement} modal - The modal element to close
 */
function closeModal(modal) {
  if (modal && modal.parentNode) {
    modal.parentNode.removeChild(modal);
  }
}
