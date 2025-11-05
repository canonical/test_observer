// Copyright (C) 2024 Canonical Ltd.
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

import { route } from 'preact-router';
import { currentFamily } from '../api/store';
import './Navbar.css';

const Navbar = () => {
  const families = [
    { name: 'snaps', label: 'Snaps', path: '/snaps' },
    { name: 'debs', label: 'Debs', path: '/debs' },
    { name: 'charms', label: 'Charms', path: '/charms' },
    { name: 'images', label: 'Images', path: '/images' },
  ];

  const handleNavigation = (path: string) => {
    route(path);
  };

  return (
    <nav class="navbar">
      <div class="navbar-brand">
        <img 
          src="/icons/canonical-logo-32x32.png" 
          alt="Canonical" 
          class="navbar-logo"
        />
        <h1 class="navbar-title">Test Observer</h1>
      </div>
      <div class="navbar-links">
        {families.map((family) => (
          <button
            key={family.name}
            class={`navbar-link ${currentFamily.value === family.name ? 'active' : ''}`}
            onClick={() => handleNavigation(family.path)}
          >
            {family.label}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default Navbar;
