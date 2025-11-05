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

import { useEffect } from 'preact/hooks';
import { currentArtefacts, isLoading, error, setCurrentFamily } from '../api/store';
import type { FamilyName } from '../models/types';
import ArtefactCard from '../components/ArtefactCard';
import './Dashboard.css';

interface DashboardProps {
  path?: string;
}

const Dashboard = ({ path }: DashboardProps) => {
  useEffect(() => {
    const family = path?.replace('/', '') as FamilyName || 'snap';
    setCurrentFamily(family);
  }, [path]);

  if (isLoading.value) {
    return <div class="dashboard-loading">Loading artefacts...</div>;
  }

  if (error.value) {
    return <div class="dashboard-error">Error: {error.value}</div>;
  }

  return (
    <div class="dashboard">
      <div class="dashboard-header">
        <h2>Artefacts</h2>
      </div>
      <div class="dashboard-content">
        {currentArtefacts.value.length === 0 ? (
          <div class="dashboard-empty">No artefacts found</div>
        ) : (
          <div class="artefacts-grid">
            {currentArtefacts.value.map((artefact) => (
              <ArtefactCard key={artefact.id} artefact={artefact} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
