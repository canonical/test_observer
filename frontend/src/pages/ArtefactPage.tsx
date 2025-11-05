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

import { useEffect, useState } from 'preact/hooks';
import type { Artefact } from '../models/types';
import { artefacts } from '../api/store';
import './ArtefactPage.css';

interface ArtefactPageProps {
  path?: string;
  artefactId?: string;
}

const ArtefactPage = ({ artefactId }: ArtefactPageProps) => {
  const [artefact, setArtefact] = useState<Artefact | null>(null);

  useEffect(() => {
    if (artefactId) {
      const id = parseInt(artefactId);
      const foundArtefact = artefacts.value.get(id);
      if (foundArtefact) {
        setArtefact(foundArtefact);
      }
    }
  }, [artefactId]);

  if (!artefact) {
    return <div class="artefact-page-loading">Loading artefact...</div>;
  }

  return (
    <div class="artefact-page">
      <div class="artefact-page-header">
        <h2>{artefact.name}</h2>
        <span class="artefact-version">v{artefact.version}</span>
      </div>
      <div class="artefact-page-content">
        <div class="artefact-detail-section">
          <h3>Details</h3>
          <div class="artefact-detail-grid">
            <div class="artefact-detail-item">
              <span class="label">Family:</span>
              <span class="value">{artefact.family}</span>
            </div>
            <div class="artefact-detail-item">
              <span class="label">Stage:</span>
              <span class="value">{artefact.stage}</span>
            </div>
            <div class="artefact-detail-item">
              <span class="label">Status:</span>
              <span class="value">{artefact.status}</span>
            </div>
            {artefact.track && (
              <div class="artefact-detail-item">
                <span class="label">Track:</span>
                <span class="value">{artefact.track}</span>
              </div>
            )}
            {artefact.assignee && (
              <div class="artefact-detail-item">
                <span class="label">Assignee:</span>
                <span class="value">{artefact.assignee.name}</span>
              </div>
            )}
          </div>
        </div>
        <div class="artefact-detail-section">
          <h3>Test Progress</h3>
          <p>
            Completed {artefact.completed_environment_reviews_count} of{' '}
            {artefact.all_environment_reviews_count} environment reviews
          </p>
        </div>
      </div>
    </div>
  );
};

export default ArtefactPage;
