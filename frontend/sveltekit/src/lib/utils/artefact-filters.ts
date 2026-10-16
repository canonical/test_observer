// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { TestExecution } from "$lib/types/artefact-page";

type Run = Pick<TestExecution, "status" | "test_plan">;

type PlanRun = Pick<
  TestExecution,
  "id" | "status" | "test_plan" | "artefact_build_id" | "environment"
>;

export function parseArtefactId(value: string): number | null {
  return parsePositiveSafeInteger(value);
}

export function parsePositiveSafeInteger(value: string): number | null {
  if (!/^\d+$/.test(value)) return null;
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export function decodeFilterValues(value: string | null): string[] {
  if (!value) return [];
  return value.split(",").flatMap((part) => {
    try {
      return [decodeURIComponent(part)];
    } catch {
      // Ignore malformed values in a URL instead of breaking page rendering.
      return [];
    }
  });
}

export function shouldFetchExpandedData(
  parentExpanded: boolean,
  expanded: boolean,
  dataUnloaded: boolean,
): boolean {
  return parentExpanded && expanded && dataUnloaded;
}

export function latestPlanStatuses(runsDescending: Run[]): string[] {
  const latestByPlan = new Map<string, string>();
  for (const run of runsDescending) {
    const plan = run.test_plan || "(unnamed)";
    if (!latestByPlan.has(plan)) latestByPlan.set(plan, run.status);
  }
  return [...latestByPlan.values()];
}

export function latestPlanRuns<T extends PlanRun>(runsDescending: T[]): T[] {
  const latestByBuildPlan = new Map<string, T>();
  for (const run of runsDescending) {
    const plan = run.test_plan || "(unnamed)";
    const key = `${run.artefact_build_id}|${run.environment.id}|${plan}`;
    if (!latestByBuildPlan.has(key)) latestByBuildPlan.set(key, run);
  }
  return [...latestByBuildPlan.values()];
}

export function matchingLatestPlanRuns<T extends PlanRun>(
  runsDescending: T[],
  selectedStatuses: string[],
): T[] {
  if (selectedStatuses.length === 0) return latestPlanRuns(runsDescending);

  const latestStatusByPlan = new Map<string, string>();
  for (const run of runsDescending) {
    const plan = run.test_plan || "(unnamed)";
    if (!latestStatusByPlan.has(plan)) latestStatusByPlan.set(plan, run.status);
  }
  const matchingPlans = new Set(
    [...latestStatusByPlan]
      .filter(([, status]) => selectedStatuses.includes(status))
      .map(([plan]) => plan),
  );
  return latestPlanRuns(runsDescending).filter((run) =>
    matchingPlans.has(run.test_plan || "(unnamed)"),
  );
}

export function matchesExecutionStatuses(
  runs: Run[],
  selectedStatuses: string[],
): boolean {
  return (
    selectedStatuses.length === 0 ||
    runs.some((run) => selectedStatuses.includes(run.status))
  );
}

export function matchesPlanLastRunStatuses(
  runsDescending: Run[],
  selectedStatuses: string[],
): boolean {
  return (
    selectedStatuses.length === 0 ||
    latestPlanStatuses(runsDescending).some((status) =>
      selectedStatuses.includes(status),
    )
  );
}
