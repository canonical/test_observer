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

import { Router } from 'preact-router';
import Dashboard from './pages/Dashboard';
import ArtefactPage from './pages/ArtefactPage';
import Navbar from './components/Navbar';
import './app.css';

export function App() {
  return (
    <div class="app">
      <Navbar />
      <Router>
        <Dashboard path="/" />
        <Dashboard path="/snaps" />
        <ArtefactPage path="/snaps/:artefactId" />
        <Dashboard path="/debs" />
        <ArtefactPage path="/debs/:artefactId" />
        <Dashboard path="/charms" />
        <ArtefactPage path="/charms/:artefactId" />
        <Dashboard path="/images" />
        <ArtefactPage path="/images/:artefactId" />
      </Router>
    </div>
  );
}
