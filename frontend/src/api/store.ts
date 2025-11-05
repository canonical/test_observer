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

import { signal, computed } from '@preact/signals';
import type { Artefact, FamilyName } from '../models/types';
import { apiClient } from '../api/client';

// Signals for application state
export const currentFamily = signal<FamilyName>('snap');
export const artefacts = signal<Map<number, Artefact>>(new Map());
export const isLoading = signal(false);
export const error = signal<string | null>(null);

// Computed values
export const currentArtefacts = computed(() => {
  const all = artefacts.value;
  return Array.from(all.values());
});

// Actions
export async function fetchArtefacts(family: FamilyName) {
  isLoading.value = true;
  error.value = null;
  
  try {
    const data = await apiClient.get<Record<string, Artefact>>(
      '/v1/artefacts',
      { family }
    );
    
    const artefactMap = new Map<number, Artefact>();
    Object.values(data).forEach(artefact => {
      artefactMap.set(artefact.id, artefact);
    });
    
    artefacts.value = artefactMap;
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch artefacts';
  } finally {
    isLoading.value = false;
  }
}

export function setCurrentFamily(family: FamilyName) {
  currentFamily.value = family;
  fetchArtefacts(family);
}
