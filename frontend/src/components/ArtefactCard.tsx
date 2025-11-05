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
import type { Artefact } from '../models/types';
import './ArtefactCard.css';

interface ArtefactCardProps {
  artefact: Artefact;
}

const ArtefactCard = ({ artefact }: ArtefactCardProps) => {
  const handleClick = () => {
    route(`/${artefact.family}s/${artefact.id}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return '#0e8420';
      case 'marked_as_failed':
        return '#c7162b';
      default:
        return '#666';
    }
  };

  return (
    <div class="artefact-card" onClick={handleClick}>
      <div class="artefact-card-header">
        <h3 class="artefact-card-title">{artefact.name}</h3>
        <span 
          class="artefact-card-status"
          style={{ backgroundColor: getStatusColor(artefact.status) }}
        >
          {artefact.status.replace('_', ' ')}
        </span>
      </div>
      <div class="artefact-card-body">
        <div class="artefact-card-info">
          <span class="artefact-card-label">Version:</span>
          <span class="artefact-card-value">{artefact.version}</span>
        </div>
        <div class="artefact-card-info">
          <span class="artefact-card-label">Stage:</span>
          <span class="artefact-card-value">{artefact.stage}</span>
        </div>
        {artefact.track && (
          <div class="artefact-card-info">
            <span class="artefact-card-label">Track:</span>
            <span class="artefact-card-value">{artefact.track}</span>
          </div>
        )}
        <div class="artefact-card-info">
          <span class="artefact-card-label">Reviews:</span>
          <span class="artefact-card-value">
            {artefact.completed_environment_reviews_count} / {artefact.all_environment_reviews_count}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ArtefactCard;
