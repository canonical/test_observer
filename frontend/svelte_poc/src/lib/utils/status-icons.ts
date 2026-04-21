import type { TestExecutionStatus, TestResultStatus } from '$lib/types/artefact-page';

export interface StatusIconInfo {
  icon: string;
  color: string;
  label: string;
}

export const EXECUTION_STATUS_ICONS: Record<TestExecutionStatus, StatusIconInfo> = {
  NOT_STARTED: { icon: 'play_arrow', color: '#757575', label: 'Not Started' },
  IN_PROGRESS: { icon: 'refresh', color: '#757575', label: 'In Progress' },
  PASSED: { icon: 'check_circle', color: '#0E8420', label: 'Passed' },
  FAILED: { icon: 'cancel', color: '#C7162B', label: 'Failed' },
  NOT_TESTED: { icon: 'info', color: '#757575', label: 'Not Tested' },
  ENDED_PREMATURELY: { icon: 'block', color: '#757575', label: 'Ended Prematurely' },
};

export const RESULT_STATUS_ICONS: Record<TestResultStatus, StatusIconInfo> = {
  PASSED: { icon: 'check_circle', color: '#0E8420', label: 'Passed' },
  FAILED: { icon: 'cancel', color: '#C7162B', label: 'Failed' },
  SKIPPED: { icon: 'block', color: '#757575', label: 'Skipped' },
};
