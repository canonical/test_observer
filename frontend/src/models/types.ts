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

export type FamilyName = 'snap' | 'deb' | 'charm' | 'image';

export type StageName = 
  | 'stable'
  | 'candidate' 
  | 'beta'
  | 'edge'
  | 'proposed'
  | 'updates'
  | 'security'
  | 'end-of-life';

export type ArtefactStatus = 
  | 'approved'
  | 'undecided'
  | 'marked_as_failed';

export interface User {
  id: number;
  launchpad_email: string;
  launchpad_handle: string;
  name: string;
}

export interface Artefact {
  id: number;
  name: string;
  version: string;
  family: FamilyName;
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  image_url: string;
  status: ArtefactStatus;
  comment: string;
  stage: StageName;
  all_environment_reviews_count: number;
  completed_environment_reviews_count: number;
  assignee: User;
  bug_link: string;
  due_date?: string;
}

export interface ArtefactBuild {
  id: number;
  artefact_id: number;
  architecture: string;
  revision?: number;
}

export interface Environment {
  id: number;
  name: string;
  architecture: string;
}

export interface TestExecution {
  id: number;
  artefact_build_id: number;
  environment_id: number;
  status: string;
}

export interface TestResult {
  id: number;
  test_execution_id: number;
  name: string;
  status: string;
  comment: string;
  io_log: string;
}
