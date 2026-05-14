// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

let sidebarOpen: boolean = $state(true);
let density: "compact" | "comfortable" = $state("comfortable");

export function getSidebarOpen(): boolean {
  return sidebarOpen;
}

export function setSidebarOpen(open: boolean): void {
  sidebarOpen = open;
}

export function toggleSidebar(): void {
  sidebarOpen = !sidebarOpen;
}

export function getDensity(): "compact" | "comfortable" {
  return density;
}

export function setDensity(d: "compact" | "comfortable"): void {
  density = d;
}
